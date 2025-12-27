import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from guild_player import GuildPlayer
from typing import Any

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
prefix = "#"

env = os.getenv("PY_ENV", "development")

if env == "production":
    print("=== Loading opus in prod ===")
    prefix = "!"
    discord.opus.load_opus("libopus.so")

    if not discord.opus.is_loaded():
        raise Exception("Opus is not loaded")

bot = commands.AutoShardedBot(command_prefix=prefix, intents=intents)

players = {}

def get_player(ctx):
    """Gets the player for the current guild."""
    guild = ctx.guild
    if guild.id not in players:
        players[guild.id] = GuildPlayer(guild, bot)
    return players[guild.id]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and before.channel is not None and after.channel is None:
        if member.guild.id in players:
            del players[member.guild.id]

@bot.command()
async def join(ctx):
    """Make Clara joining channel. Usage: `!join`"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        player = get_player(ctx)
        await player.join(channel)
        await ctx.send(f"Joined {channel.name}")
    else:
        await ctx.send("You are not in a voice channel.")

@bot.command()
async def leave(ctx):
    """Make Clara leaving channel. Usage: `!leave`"""
    player = get_player(ctx)
    await player.leave()
    await ctx.send("Left the voice channel.")

@bot.command()
async def play(ctx, *, query=None):
    """Clara will playing song. 
    Syntax: `!play <query:optional> <separator \";;\":optional> <...query:optional>` 
    Usage: `!play yoasobi tabun ;; yoasobi blessing`"""
    player = get_player(ctx)
    if not ctx.author.voice:
        return await ctx.send("You are not in a voice channel.")

    if not query:
        if ctx.author.voice:
            await player.join(ctx.author.voice.channel)

        return await player.play_next(ctx)
    
    if not player.voice_client:
        if ctx.author.voice:
            await player.join(ctx.author.voice.channel)
        
    queries = list(map(lambda x: x.strip(), query.split(";;")))

    if len(queries) < 2 and query:
        await ctx.send(f"Searching for `{query}`...")
        await player.play(query, ctx)
    elif len(queries) >= 2:
        await ctx.send(f"Multiple query found for `{", ".join(queries)}...`")

        for query in queries:
            await player.play(query, ctx)
    else:
        await ctx.send(f"Invalid command.")
   

@bot.command()
async def skip(ctx):
    """Clara will skip currently playing song. Usage: `!skip`"""
    player = get_player(ctx)
    await player.skip()
    await ctx.send("Skipped the current song.")

def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    return f"{int(minutes):02}:{int(seconds):02}"

def parse_queue(song_queue: list[Any]):
    message = "**Song Queue:**\n"

    for i, song_data in enumerate(song_queue):
        title = song_data.get('title', 'Unknown Title')
        duration = song_data.get('duration', 0)
        formatted_duration = format_duration(duration)
        line = f"{i+1}. {title} ({formatted_duration})\n"

        if len(message) + len(line) > 1990: 
            message = "...\n" + line
        else:
            message += line

    return message    
    
@bot.command()
async def queue(ctx):
    """List of currently queued song, song will be saved unless cleared. Usage: `!queue`"""
    player = get_player(ctx)
    song_queue = player.get_queue()
    if song_queue:
        message = parse_queue(song_queue)
        await ctx.send(message)
    else:
        await ctx.send("The song queue is empty.")

@bot.command()
async def current_song(ctx):
    """Clara will show currently playing song. Usage: `!current_song`"""
    player = get_player(ctx)
    now_playing = player.current_song
    is_playing = player.is_playing

    if now_playing and is_playing:
        await ctx.send(f"Currently playing {now_playing.get("title")}.")
    elif now_playing and not is_playing:
        await ctx.send(f"First song in the playlist is {now_playing.get("title")}.")
    else:
        await ctx.send(f"Clara has no song in the list.")

@bot.command()
async def stop(ctx):
    """Clara will stop currently playing song and will clear all queues. Usage: `!stop`"""
    player = get_player(ctx)
    await player.stop()
    await ctx.send("Stopped the music and cleared the queue.")

@bot.command()
async def pause(ctx):
    """Clara will pause currently playing song. Usage: `!pause`"""
    player = get_player(ctx)
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.pause()
        await ctx.send("Paused the song.")
    else:
        await ctx.send("I'm not playing anything.")

@bot.command()
async def resume(ctx):
    """Clara will resume currently paused song. Usage: `!resume`"""
    player = get_player(ctx)
    if player.voice_client and player.voice_client.is_paused():
        player.voice_client.resume()
        await ctx.send("Resumed the song.")
    else:
        await ctx.send("The song is not paused.")

@bot.command()
async def remove(ctx, index: int):
    """Clara will remove song from queue based on index of song in queue. 
    Syntax: `!remove <index>`
    Usage: `!remove 1`"""
    player = get_player(ctx)
    player.remove_from_queue(index - 1)
    await ctx.send(f"Removed song at position {index}.")

@bot.command()
async def repeat(ctx):
    """Clara will toggle repeat mode. Configuration will be saved. Usage: `!repeat`"""
    player = get_player(ctx)
    is_repeating = player.toggle_repeat()
    if is_repeating:
        await ctx.send("Repeat mode is now ON.")
    else:
        await ctx.send("Repeat mode is now OFF.")


TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    print("DISCORD_TOKEN not found in .env file. Please create a .env file and add your bot token.")
else:
    bot.run(TOKEN)