import asyncio
import discord
import yt_dlp
from redis_queue import add_to_queue, get_from_queue, get_queue, clear_queue, remove_from_queue, set_repeat, get_repeat, remove_first_queue, publish_song_added, publish_song_listened

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class GuildPlayer:
    def __init__(self, guild: discord.Guild, bot):
        self.guild = guild
        self.bot = bot
        self.voice_client = None
        self.is_playing = False
        self.repeat = False
        self.current_song = None
        self.repeat = get_repeat(guild.id) or False

    async def join(self, channel: discord.VoiceChannel):
        """Joins a voice channel."""
        if self.voice_client:
            await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()

    async def leave(self):
        """Leaves the voice channel."""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
        clear_queue(self.guild.id)

    async def play(self, query: str, ctx):
        """Plays a song from a query."""
        if not self.voice_client:
            return

        loop = asyncio.get_event_loop()
        
        query_parts = query.split('#')
        song_query = query_parts[0].strip()
        tags = [tag.strip() for tag in query_parts[1:]]

        def get_song_info():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                return ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]

        try:
            info = await loop.run_in_executor(None, get_song_info)
            url = info['url']
            webpage_url = info.get("webpage_url")
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)  # duration in seconds
        except Exception as e:
            await ctx.send("There was an error searching for the song.")
            print(f"Error fetching song info: {e}")
            return

        song_data = {"url": url, "title": title, "duration": duration, "webpage_url": webpage_url}
        add_to_queue(self.guild.id, song_data)
        
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


    async def play_next(self, ctx):
        """Plays the next song in the queue."""

        song_data = get_from_queue(self.guild.id)

        if not song_data:
            return await ctx.send("No song in queue.")

        song_url = song_data.get("url")
        song_title = song_data.get("title")

        if not song_url:
            return await ctx.send("Failed to retrieve song url.")

        self.current_song = song_data

        def after_play(e):
            listened_members = [
                {"id": member.id, "name": member.name}
                for member in ctx.voice_client.channel.members
            ]
            
            event_data = {
                "guild_id": self.guild.id,
                "guild_name": self.guild.name,
                "song_url": song_url,
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

        if song_data and self.voice_client:
            msg = f"Playing {song_title or "unnamed song"}."
            await ctx.send(msg)
    
            self.is_playing = True
            self.voice_client.play(
                discord.FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS),
                after=after_play,
            )
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

    async def skip(self):
        """Skips the current song."""
        if self.voice_client and self.is_playing:
            self.voice_client.stop()
            # play_next will be called by the 'after' callback in play
