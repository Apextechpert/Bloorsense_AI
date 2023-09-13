import discord
from discord.ext import commands
import yt_dlp as youtube_dl
from youtube_search import YoutubeSearch
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Necessary API

Token = ""

SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''

client = discord.Client(intents=discord.Intents.all())
bot = commands.Bot(command_prefix='/',intents=discord.Intents.all())

# youtubedl
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

ffmpeg_options = {'options': '-vn'}


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Successful connected to the server")

# Chatting function
@bot.tree.command(name="ping", description="Get ping from bot")
async def ping(interaction: discord.Interaction):
    botlantency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong: {botlantency} ms.")

@bot.hybrid_command(name="noob", description="Checking who is noob")
async def noob(ctx):
    embed = discord.Embed(color=discord.Color.green())
    embed.set_author(name=f"{ctx.author.display_name} is noob")
    await ctx.send(embed = embed)

@bot.tree.command(name="help", description="List of all command of Bloorsense")
async def help(interaction: discord.Interaction):
    message = """
```
Chat Commands:
/ping - Return the latency of Bloorsense
/noob - Checking the person who is noob

Music Commands:
/join - Let Bloorsense join the voice channel
/leave - Let Bloorsense leave the voice channel
/play - play certain music with url
/searchyt - search certain music by given words from Youtube and play
/searchspotify - Search and play music from Spotify
/playspotify - Play the music with previous given tracknumber
/stop - stopping the current music playing

Future Function:
/MineHyp - Checking current Minecraft Hypixel data

```
"""
    
    await interaction.response.send_message(message)

@bot.tree.command(name="info", description="Given update info of Bloorsense")
async def info(interaction: discord.Interaction):
    message = """
```
Your update and version message here

```
"""
    
    await interaction.response.send_message(message)

# Music Function

@bot.hybrid_command(name='join', description='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.author.name))
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send("Connect Successful!")

@bot.hybrid_command(name='leave', description='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Successfully leave")
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.hybrid_command(name='play', description='To play song')
async def play(ctx, url):
    voice_channel = ctx.author.voice.channel

    if not ctx.voice_client:
        voice_client = await voice_channel.connect()
    else:
        voice_client = ctx.voice_client

    try:
        with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')

        voice_client.stop()
        voice_client.play(discord.FFmpegPCMAudio(source=url, **ffmpeg_options))
        await ctx.send(f'**Now playing**: {title}')
    except Exception as err:
        await ctx.send(f'An error occurred: {str(err)}')


@bot.hybrid_command(name='searchyt', description='Search and play a song from YouTube by name')
async def searchyt(ctx, *, query: str):
    voice_channel = ctx.author.voice.channel

    if not ctx.voice_client:
        voice_client = await voice_channel.connect()
    else:
        voice_client = ctx.voice_client

    try:
        # Use the YoutubeSearch library to search for videos by name
        results = YoutubeSearch(query, max_results=1).to_dict()
        
        if results:
            # Get the URL of the first search result
            video = results[0]
            url = 'https://www.youtube.com/watch?v=' + video['id']

            print("URL:", url)
            # Use youtube_dl to get the title
            with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')

            # Stop any currently playing audio and play the new audio
            voice_client.stop()
            voice_client.play(discord.FFmpegPCMAudio(source=url, **ffmpeg_options))
            
            await ctx.send(f'**Now playing**: {title}')
        else:
            await ctx.send('No results found for the given query.')
    except Exception as err:
        await ctx.send(f'An error occurred: {str(err)}')

# Initialize the Spotify client
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id= SPOTIPY_CLIENT_ID,
                                                                       client_secret=SPOTIPY_CLIENT_SECRET))

# Store search results in a dictionary
search_results = {}


@bot.hybrid_command(name='searchspotify', description='Search for a song on Spotify and play it')
async def search_spotify(ctx, query: str):
    try:
        # Search for tracks on Spotify
        results = sp.search(q=query, type='track', limit=10)

        if 'tracks' in results:
            tracks = results['tracks']['items']

            # Check if there are matching tracks
            if len(tracks) > 0:
                search_results[ctx.author.id] = tracks  # Store search results for the user

                # Create a list of track descriptions
                track_descriptions = [f"{i+1}. {track['name']} by {', '.join([artist['name'] for artist in track['artists']])}" for i, track in enumerate(tracks)]

                # Combine track descriptions into a single message
                message = "**Search results**:\n" + "\n".join(track_descriptions)

                await ctx.send(message)
                await ctx.send("**Select a track to play using /playspotify <track_number>**")
            else:
                await ctx.send("No matching tracks found on Spotify.")
        else:
            await ctx.send("No matching tracks found on Spotify.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        await ctx.send(f"An error occurred: {str(e)}")

@bot.hybrid_command(name='playspotify', description='Play a selected track from Spotify')
async def play_spotify(ctx, track_number: int):
    try:
        # Check if the user provided a valid track number
        if track_number <= 0:
            await ctx.send("Please select a valid track number.")
            return

        # Retrieve the selected track from the search results for the user
        if ctx.author.id in search_results:
            tracks = search_results[ctx.author.id]

            if 1 <= track_number <= len(tracks):
                selected_track = tracks[track_number - 1]
                track_name = selected_track['name']
                track_uri = selected_track['uri']

                # Check if the bot is in a voice channel and connect if not
                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    channel = ctx.author.voice.channel
                    await channel.connect()

                # Play the selected track using its Spotify URI

                voice_client = ctx.voice_client
                voice_client.stop()
                voice_client.play(discord.FFmpegPCMAudio(track_uri, **ffmpeg_options))
                await ctx.send(f"**Now Playing**: {track_name}")
            else:
                await ctx.send("Invalid track number. Please select a valid track number using /searchspotify.")
        else:
            await ctx.send("No search results found. Please use /searchspotify to search for tracks first.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        await ctx.send(f"An error occurred: {str(e)}")



@bot.hybrid_command(name='stop', description='Stops the song')
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await ctx.send("Stopped!")
        voice_client.stop()
        
    else:
        await ctx.send("The bot is not playing anything at the moment.")


bot.run(Token)
