import asyncio
import discord
from discord.ext.commands import AutoShardedBot
import yt_dlp
from urllib.parse import parse_qs, urlparse
from redis_queue import add_to_queue, get_from_queue, get_queue, clear_queue, remove_from_queue, set_repeat, get_repeat, remove_first_queue, publish_song_added, publish_song_listened, set_song_url, get_song_url

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class GuildPlayer:
    def __init__(self, guild: discord.Guild, bot: AutoShardedBot):
        self.guild = guild
        self.bot = bot
        self.voice_client = None
        self.joined = False
        self.is_playing = False
        self.repeat = False
        self.current_song = None
        self.repeat = get_repeat(guild.id) or False
        self.max_retries = 2

        if guild.voice_client:
            self.voice_client = guild.voice_client
            self.joined = guild.voice_client.is_connected()
            self.is_playing = guild.voice_client.is_playing()

    async def join(self, channel: discord.VoiceChannel):
        """Joins a voice channel."""
        if self.voice_client:
            await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()
        
        self.joined = True

    async def leave(self):
        """Leaves the voice channel."""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            self.joined = False
    
    def get_song_info(self, song_query: str):
        if song_query.startswith('http'):
            query_parsed = urlparse(song_query)
            if "si=" in query_parsed.query:
                song_query = song_query.strip("?" + query_parsed.query)

        url = f"ytsearch:{song_query}"

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(
                url, 
                download=False
            )
            entries = info.get("entries")
            if not entries or not len(entries):
                return None
            
            return info["entries"][0]

    async def play(self, query: str, ctx):
        """Plays a song from a query."""
        if not self.voice_client:
            return

        loop = asyncio.get_event_loop()
        song_query = query.strip()

        try:
            info = await loop.run_in_executor(None, self.get_song_info, song_query)

            if not info:
                raise RuntimeError("Failed to get song info")

            tags = [tag.strip() for tag in info.get("tags", [])]
            webpage_url = info["webpage_url"] # expecting error when this undefined
            url = info['url'] # expecting error when this undefined
            title = info.get('title', 'Unknown Title').strip()
            duration = info.get('duration', 0)  # duration in seconds
        except Exception as e:
            await ctx.send("There was an error searching for the song.")
            print(f"Error fetching song info: {e}")
            return

        if not webpage_url:
            return ctx.send("Cannot found youtube for current song. Can you be more specific or change the word order?")

        song_data = {"title": title, "duration": duration, "webpage_url": webpage_url}
        expired_at = self._get_song_expiration(url)
        add_to_queue(self.guild.id, song_data)
        set_song_url(webpage_url, url, expired_at)
        
        event_data = {
            "guild_id": self.guild.id,
            "guild_name": self.guild.name,
            "user_id": ctx.author.id,
            "user_name":ctx.author.name,
            "song_url": webpage_url,
            "song_title": title,
            "song_duration": duration,
            "song_tags": tags,
        }
        publish_song_added(event_data)

        if not self.is_playing:
            await self.play_next(ctx)
        else:
            await ctx.send(f"{song_data['title']} is added to queue.")


    async def play_next(self, ctx, retries = 0):
        """Plays the next song in the queue."""
        song_data = get_from_queue(self.guild.id)

        if not song_data:
            return await ctx.send("No song in queue.")

        song_title = song_data.get("title")
        webpage_url = song_data.get("webpage_url")
        song_url = get_song_url(webpage_url)

        if not song_url:
            song_data = self.get_song_info(webpage_url)
            webpage_url = song_data["webpage_url"]
            song_url = song_data['url']
            song_title = song_data.get('title')
            expired_at = self._get_song_expiration(song_url)

            if not song_url or not webpage_url or not expired_at:
                return await ctx.send("Failed to retrieve song url.")

            set_song_url(webpage_url, song_url, expired_at)

        if not song_url:
            return await ctx.send("Failed to retrieve song url.")

        self.current_song = song_data

        def after_play(e):
            listened_members = [
                {"id": member.id, "name": member.name}
                for member in ctx.voice_client.channel.members if not member.bot
            ]
            
            event_data = {
                "guild_id": self.guild.id,
                "guild_name": self.guild.name,
                "song_url": webpage_url,
                "song_url": webpage_url,
                "song_title": song_title,
                "listened_members": listened_members,
            }
            publish_song_listened(event_data)
            remove_first_queue(self.guild.id)

            if self.repeat:
                add_to_queue(self.guild.id, self.current_song)
            
            return self.bot.loop.create_task(self.play_next(ctx))

        if not self.current_song:
            self.is_playing = False
            return ctx.send("No more song to play.")

        if self.voice_client:
            msg = f"Playing {song_title or "unnamed song"}."
            await ctx.send(msg)
    
            try:
                self.is_playing = True
                self.voice_client.play(
                    discord.FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS),
                    after=after_play,
                )
            except Exception as err:
                print(err)
                self.is_playing = False
                if retries < self.max_retries:
                    return await self.play_next(ctx, retries + 1)
                else:
                    return await ctx.send("Failed to play song")
        else:
            ctx.send("Something happened. Please try again.")
            print("Failed to play song.")
            self.is_playing = False
            self.current_song = None

    def toggle_repeat(self):
        """Toggles the repeat mode."""
        self.repeat = not self.repeat
        set_repeat(self.guild.id, self.repeat)

        return self.repeat

    def get_queue(self):
        """Gets the current song queue."""
        return get_queue(self.guild.id)

    def remove_from_queue(self, index: int):
        """Removes a song from the queue by its index."""
        remove_from_queue(self.guild.id, index)

    async def stop(self):   
        """Stops playing and clears the queue."""
        if self.voice_client:
            self.voice_client.stop()
        clear_queue(self.guild.id)
        self.is_playing = False
        self.current_song = None
        self.joined = False

    async def skip(self):
        """Skips the current song."""
        if self.voice_client and self.is_playing:
            self.voice_client.stop()
            # play_next will be called by the 'after' callback in play

    def _get_song_expiration(self, url_str: str):
        parsed_url = urlparse(url_str)
        parsed_query = parse_qs(parsed_url.query)

        expirations = parsed_query.get("expire", [])
        if not len(expirations):
            return None
        
        return int(expirations[0])