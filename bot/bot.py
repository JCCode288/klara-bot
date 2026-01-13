import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from players import Players
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

players = Players(bot)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# @bot.event
# async def on_voice_state_update(member, before, after):
#     try:
#         ctx = before.channel or after.channel
#         player = players.get_player(ctx)
#         if after.channel is None or not getattr(after.channel, "members"):
#             await player.leave()
#             players.remove_player(ctx)
#     except Exception as err:
#         print("=== Something happened ===")
#         print(err)

@bot.command()
async def join(ctx):
    """Make Clara joining channel. Usage: `!join`"""
    try:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            player = players.get_player(ctx)
            if not player.voice_client:
                await player.join(channel)
                await ctx.send(f"Joined {channel.name}")
            else:
                await player.leave()
                await player.join(channel)
                await ctx.send(f"Rejoining {channel.name}")
        else:
            await ctx.send("You are not in a voice channel.")
    except Exception as err:
        print("Something happened")
        print(err)
        return

@bot.command()
async def leave(ctx):
    """Make Clara leaving channel. Usage: `!leave`"""
    try:
        player = players.get_player(ctx)
        await player.leave()
        await ctx.send("Left the voice channel.")
    except Exception as err:
        print("Something happened")
        print(err)

@bot.command()
async def play(ctx, *, query=None):
    """Clara will playing song. 
    Syntax: `!play <query:optional> <separator \";;\":optional> <...query:optional>` 
    Usage: `!play yoasobi tabun ;; yoasobi blessing`"""
    try:
        player = players.get_player(ctx)

        if not ctx.author.voice:
            return await ctx.send("You are not in a voice channel.")
        
        if not player.voice_client:
            await player.join(ctx.author.voice.channel)

        if not query:
            return await player.play_next(ctx)
            
        queries = list(map(lambda x: x.strip(), query.split(";;")))

        if len(queries) < 2 and query:
            await ctx.send(f"Searching for `{query}`...")
            await player.play(query, ctx)
        elif len(queries) >= 2:
            await ctx.send(f"Multiple query found for `{"\n".join(queries)}`")

            for query in queries:
                await player.play(query, ctx)
        else:
            await ctx.send(f"Invalid command.")
    except Exception as err:
        print("Somethign happened")
        print(err)
   

@bot.command()
async def skip(ctx):
    """Clara will skip currently playing song. Usage: `!skip`"""
    try:
        player = players.get_player(ctx)
        await player.skip()
        await ctx.send("Skipped the current song.")
    except Exception as err:
        print("Something happened")
        print(err)

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
    try:
        player = players.get_player(ctx)
        song_queue = player.get_queue()
        if song_queue:
            message = parse_queue(song_queue)
            await ctx.send(message)
        else:
            await ctx.send("The song queue is empty.")
    except Exception as err:
        print("Something error")
        print(err)

@bot.command()
async def current_song(ctx):
    """Clara will show currently playing song. Usage: `!current_song`"""
    try:
        player = players.get_player(ctx)
        now_playing = player.current_song
        is_playing = player.is_playing

        if now_playing and is_playing:
            await ctx.send(f"Currently playing {now_playing.get("title")}.")
        elif now_playing and not is_playing:
            await ctx.send(f"First song in the playlist is {now_playing.get("title")}.")
        else:
            await ctx.send(f"Clara has no song in the list.")
    except Exception as err:
        print("Something happened")
        print(err)

@bot.command()
async def stop(ctx):
    """Clara will stop currently playing song and will clear all queues. Usage: `!stop`"""
    try:
        player = players.get_player(ctx)
        await player.stop()
        await ctx.send("Stopped the music and cleared the queue.")
    except Exception as err:
        print("Something happened")
        print(err)

@bot.command()
async def pause(ctx):
    """Clara will pause currently playing song. Usage: `!pause`"""
    try:
        player = players.get_player(ctx)
        if player.voice_client and player.voice_client.is_playing():
            player.voice_client.pause()
            await ctx.send("Paused the song.")
        else:
            await ctx.send("I'm not playing anything.")
    except Exception as err:
        print("Something happeend")
        print(err)

@bot.command()
async def resume(ctx):
    """Clara will resume currently paused song. Usage: `!resume`"""
    try:
        player = players.get_player(ctx)
        if player.voice_client and player.voice_client.is_paused():
            player.voice_client.resume()
            await ctx.send("Resumed the song.")
        else:
            await ctx.send("The song is not paused.")
    except Exception as err:
        print("Something happened")
        print(err)

@bot.command()
async def remove(ctx, index: int):
    """Clara will remove song from queue based on index of song in queue. 
    Syntax: `!remove <index>`
    Usage: `!remove 1`"""
    try:
        player = players.get_player(ctx)
        player.remove_from_queue(index - 1)
        await ctx.send(f"Removed song at position {index}.")
    except Exception as err:
        print("Something happened")
        print(err)

@bot.command()
async def repeat(ctx):
    """Clara will toggle repeat mode. Configuration will be saved. Usage: `!repeat`"""
    try:
        player = players.get_player(ctx)
        is_repeating = player.toggle_repeat()
        if is_repeating:
            await ctx.send("Repeat mode is now ON.")
        else:
            await ctx.send("Repeat mode is now OFF.")
    except Exception as err:
        print("Something happened")
        print(err)

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    print("DISCORD_TOKEN not found in .env file. Please create a .env file and add your bot token.")
else:
    bot.run(TOKEN)