import discord
import os
import json
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import itertools
import sys
import traceback
from async_timeout import timeout
from functools import partial
import youtube_dl
from yt_dlp import YoutubeDL

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

class Song():
    """Song object containing all music data and its relevant info."""
    def __init__(self, title, web_url, requester, file_path, uploader, song_duration):
        self.title = title
        self.web_url = web_url
        self.requester = requester
        self.file_path = file_path
        self.uploader = uploader
        self.song_duration = song_duration

    def get_duration(self):
        seconds = self.song_duration
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)
        
        return duration


class SongSource(discord.FFmpegPCMAudio):
    """Source object that allows for reading current amount of reads to calculate duration"""
    def __init__(self, source, metadata = None):
        self.source = source
        self.read_count = 0
        self.metadata = metadata # The Song object that contains all the info
    
    def read(self):
        data = self.source.read()
        if data:
            self.read_count += 1
        return data

    def curr_dur(self):
        return self.read_count


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        embed = discord.Embed(title="", description=f"Queued [{data['title']}]({data['webpage_url']}) [{ctx.author.mention}]", color=discord.Color.red())
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume', 'loopqueue')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue(maxsize=10)
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None
        self.loopqueue = False

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    song_data = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            print(f"Now playing {song_data.title} requested by {song_data.requester}")
            

            ffmpeg_options = {
                'options': '-vn',
            }
            
            audio = discord.FFmpegPCMAudio(song_data.file_path, **ffmpeg_options)

            song_source = SongSource(audio, song_data)

            self.current = song_source
            print(song_source)

            self._guild.voice_client.play(song_source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            embed = discord.Embed(title="Now playing", description=f"[{song_data.title} by {song_data.uploader}]({song_data.web_url}) [requested by {song_data.requester}]", color=discord.Color.red())
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()
            print("Song finished playing.")

            if self.loopqueue:
                await self.queue.put(self.current.metadata)
                await self._channel.send(f"Loop On: Placed {song_data.title} back in the queue.")

            self.current = None

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))
        

class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='join', description="connects to voice")
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        """Connect to voice.
        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        """
        print("Join command")

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title="", description="No channel to join. Please call `,join` from a voice channel.", color=discord.Color.red())
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client
        print(vc, channel, ctx.author, ctx.author.voice.channel)

        # TODO: Delete an existing Player
        if ctx.guild.id in self.players:
            del self.players[ctx.guild.id]

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👍')
        await ctx.send(f'**Joined `{channel}`**')

    @commands.command(name='play', description="streams music")
    async def play_(self, ctx, *, search: str):
        """Request a song and add it to the queue.
        This command attempts to join a valid voice channel if the bot is not already in one.
        """
        save_path = "music"
        # print(search)

        await ctx.typing()

        vc = ctx.voice_client

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Error: unable to join requested voice channel")
            return

        if vc and ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send("Bot is already playing in a different voice channel.")
            return

        if not vc:
            await ctx.invoke(self.connect_)
            vc = ctx.voice_client
        player = self.get_player(ctx)

        search_query = f"ytsearch1:{search}"

        ydl_opts = {
            'outtmpl': save_path + '/%(title)s_%(uploader)s.%(ext)s', 
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            # 'verbose': True,
            'limit-rate': 100 * 1024,
            'restrictfilenames': True,
            'max_filesize': 30 * 1024 * 1024,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if not ('entries' in info and len(info['entries']) > 0):
                print(info)
                await ctx.send("No search results!")
                return
            else:
                video = info['entries'][0]
                url = video['url']
                title = video.get('title')
                uploader = video.get('uploader')
                filepath = ydl.prepare_filename(video)
                song_duration = video.get('duration')

        if song_duration > 900:
            await ctx.send(f"Song {title} duration is {song_duration} seconds long, longer than 15 minutes. Can't add this.")
            return

        await ctx.send(f"Added to Queue: {title}, uploaded by {uploader}")
        # print(url)

        requester = ctx.author
        song_data = Song(title, url, requester, filepath, uploader, song_duration)

        print(f"Passed song {song_data.title} to the queue")
        await player.queue.put(song_data)

    @commands.command(name='playurl', description="plays music from url")
    async def playurl_(self, ctx, url):
        """Same as play, except instead of a search it uses a url
        """
        save_path = "music"
        print("Playurl called")

        await ctx.typing()

        vc = ctx.voice_client

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Error: unable to join requested voice channel")
            return

        if vc and ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send("Bot is already playing in a different voice channel.")
            return

        if not vc:
            await ctx.invoke(self.connect_)
            vc = ctx.voice_client
        player = self.get_player(ctx)

        ydl_opts = {
            'outtmpl': save_path + '/%(title)s_%(uploader)s.%(ext)s', # '%(title)s_%(uploader)s.%(ext)s'
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            # 'verbose': True,
            'limit-rate': 100 * 1024,
            'restrictfilenames': True,
            'max_filesize': 30 * 1024 * 1024,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title')
            uploader = info.get('uploader')
            new_filepath = ydl.prepare_filename(info)
            song_duration = info.get('duration')

        print(new_filepath)

        await ctx.send(f"Added to Queue: {title}, uploaded by {uploader}")


        requester = ctx.author
        song_data = Song(title, url, requester, new_filepath, uploader, song_duration)

        print(f"Passed song {song_data.title} to the queue")
        await player.queue.put(song_data)

    @commands.command(name='pause', description="pauses music")
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title="", description="I am currently not playing anything", color=discord.Color.red())
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send("Paused ⏸️")

    @commands.command(name='resume', description="resumes music")
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send("Resuming ⏯️")

    @commands.command(name='skip', description="skips to next song in queue")
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
    
    @commands.command(name='remove', description="removes specified song from queue")
    async def remove_(self, ctx, pos : int=None):
        """Removes specified song from queue"""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if pos == None:
            player.queue._queue.pop()
        else:
            try:
                s = player.queue._queue[pos-1]
                del player.queue._queue[pos-1]
                embed = discord.Embed(title="", description=f"Removed [{s.title}]({s.web_url}) [{s.requester}]", color=discord.Color.red())
                await ctx.send(embed=embed)
            except Exception as e:
                print(e)
                embed = discord.Embed(title="", description=f'Could not find a track for "{pos}"', color=discord.Color.red())
                await ctx.send(embed=embed)
    
    @commands.command(name='clear', description="clears entire queue")
    async def clear_(self, ctx):
        """Deletes entire queue of upcoming songs."""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('**Cleared**')

    @commands.command(name='loop', description="loops entire queue")
    async def loopqueue_(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.loopqueue = not player.loopqueue

        if player.loopqueue:
            await ctx.send("Looping queue (there is no loop song functionality)")
        else:
            await ctx.send("Loop off")


    @commands.command(name='queue', description="shows the queue")
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(title="", description="queue is empty", color=discord.Color.red())
            return await ctx.send(embed=embed)

        # print(vc.source)

        # print(vc.source.curr_dur())
        read_count = vc.source.curr_dur() # each read is 20 ms

        seconds = read_count / 50
        print(seconds)

        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        # print(duration)
        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
        # print("Upcoming:", upcoming)
        # fmt = '\n'.join(f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | ` {duration} Requested by: {_['requester']}`\n" for _ in upcoming)
        fmt = '\n'.join(f"`{i + 1}.` [{source.title}]({source.web_url}) uploaded by {source.uploader}| Duration: {source.get_duration()} ` Requested by: {source.requester}`\n" 
                for i, source in enumerate(upcoming))
        fmt = f"\n__Now Playing__:\n[{vc.source.metadata.title}]({vc.source.metadata.web_url}) uploaded by {vc.source.metadata.uploader} | Playing for: {duration} ` Requested by: {vc.source.metadata.requester}`\n\n__Up Next:__\n" + fmt + f"\n**{len(upcoming)} songs in queue**"
        # print(fmt)

        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=discord.Color.red())
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar)

        await ctx.send(embed=embed)

    @commands.command(name='np', description="shows the current playing song")
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title="", description="I am currently not playing anything", color=discord.Color.red())
            return await ctx.send(embed=embed)
        

        read_count = vc.source.curr_dur() # each read is 20 ms

        seconds = read_count / 50
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        embed = discord.Embed(title="", description=f"[{vc.source.metadata.title}]({vc.source.metadata.web_url}) [{vc.source.metadata.requester}] uploaded by {vc.source.metadata.uploader} | `{duration} / {vc.source.metadata.get_duration()}`", color=discord.Color.red())
        embed.set_author(icon_url=self.bot.user.avatar, name=f"Now Playing 🎶")
        await ctx.send(embed=embed)

    @commands.command(name='volume', description="changes volume")
    async def change_volume(self, ctx, *, vol: float=None):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I am not currently connected to voice", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        if not vol:
            embed = discord.Embed(title="", description=f"🔊 **{(vc.source.volume)*100}%**", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if not 0 < vol < 101:
            embed = discord.Embed(title="", description="Please enter a value between 1 and 100", color=discord.Color.red())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title="", description=f'**`{ctx.author}`** set the volume to **{vol}%**', color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(name='leave', description="stops music and disconnects from voice")
    async def leave_(self, ctx):
        """Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        player = self.get_player(ctx)

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👋')
        await ctx.send('**Successfully disconnected**')

        await self.cleanup(ctx.guild)

def setup(bot):
    bot.add_cog(Music(bot))