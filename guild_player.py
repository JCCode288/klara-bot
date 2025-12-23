import asyncio
import discord
import yt_dlp
from redis_queue import add_to_queue, get_from_queue, get_queue, clear_queue, remove_from_queue, set_repeat, get_repeat

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
        self.current_song_url = None
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

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            url = info['url']
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0) # duration in seconds

        song_data = {"url": url, "title": title, "duration": duration}
        add_to_queue(self.guild.id, song_data)

        if not self.is_playing:
            await self.play_next(ctx)
        else:
            await ctx.send(f"{song_data['title']} is added to queue.")


    async def play_next(self, ctx):
        """Plays the next song in the queue."""

        song_data = get_from_queue(self.guild.id)
        self.current_song_url = song_data

        if not self.current_song_url:
            self.is_playing = False
            return ctx.send("No more song to play.")

        if song_data and self.voice_client:
            msg = f"Playing {song_data['title']}"
            print(msg)
            await ctx.send(msg)

            self.is_playing = True
            self.voice_client.play(
                discord.FFmpegPCMAudio(song_data['url'], **FFMPEG_OPTIONS),
                after=lambda e: self.bot.loop.create_task(self.play_next(ctx)),
            )

            if self.repeat:
                add_to_queue(self.guild.id, self.current_song_url)
        else:
            ctx.send("Something happened. Please try again.")
            print("Failed to play song.")
            self.is_playing = False
            self.current_song_url = None

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
        self.current_song_url = None

    async def skip(self):
        """Skips the current song."""
        if self.voice_client and self.is_playing:
            self.voice_client.stop()
            # play_next will be called by the 'after' callback in play
