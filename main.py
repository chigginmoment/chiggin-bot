import asyncio
import os
import discord
import random
import re
import constants
import psycopg2
from datetime import datetime
from bot import Bot
from storage import *
import reel_helper
import shutil

from discord.ext import commands
from dotenv import load_dotenv
from discord.utils import get
from concurrent.futures import ThreadPoolExecutor

bot = Bot()
channel = None

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_SERVER')

awaiting_response = []
pref_array = []
spam_protection = []
pref_map = {}

@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f'Connected to: {guild}')
        if guild.name == GUILD:  # figures out what the current guild is
            break

    activity = discord.Activity(type=discord.ActivityType.watching, name="Instagram suspend me")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # global pref_array
    global pref_map
    # pref_array = db_update(bot.connection)
    pref_map = db_update_map(bot.connection)
    print("Ready on ", datetime.now())


@bot.event
async def on_guild_join(guild):
    global pref_map
    print("Joined new server.")
    db_add_server(bot.connection, str(guild.id), guild.name)
    pref_map = db_update_map(bot.connection)


@bot.event
async def on_guild_remove(guild):
    global pref_map
    db_remove_server(bot.connection, str(guild.id))
    print("Left server.")
    pref_map = db_update_map(bot.connection)


"""
@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hello {member.name}.'
    )
"""


@bot.event
async def on_message(message):
    # print("On message?")
    global pref_map

    nuisance = pref_map[str(message.guild.id)][4]

    if message.author == bot.user:
        return

    if message.channel.id == constants.CHANNEL:  # This is where the bot copies everything I say
        await message.channel.send("Heard.")

        print("Echoing message.")
        for pref in pref_map:
            if pref_map[pref][0] is not None:
                channel_name = pref_map[pref][3]
                server_name = pref_map[pref][2]
                print(f"Echoing message in server {server_name} in channel {channel_name}")
                echo_channel = bot.get_channel(int(pref_map[pref][0]))
                if message.content:
                    await echo_channel.send(message.content)
                if message.attachments:
                    await echo_channel.send("\n".join(x.url for x in message.attachments))

        print("Done echoing.")

    if message.content == 'raise exception':
        raise discord.DiscordException

    if re.match(r"(?i)(^sus )|(.* sus$)|(.* sus .*)|(^sus$)", message.content) and message.channel.id not in spam_protection:
        roll = random.randint(1, 5)
        if roll == 1 or nuisance:
            await message.channel.send("<a:RockEyebrow:970449809121112096>")
            if not nuisance:
                spam_protection.append(message.channel.id)
                await asyncio.sleep(800)
                spam_protection.remove(message.channel.id)

    if re.match(r'(?i).*amog.*', message.content) and message.channel.id not in spam_protection:
        roll = random.randint(1, 5)
        if roll == 1 or nuisance:
            await message.channel.send(random.choice(constants.AMOGUS_GIFS))
            if not nuisance:
                spam_protection.append(message.channel.id)
                await asyncio.sleep(800)
                spam_protection.remove(message.channel.id)

    if re.match(r'(?i).*ragnar.*', message.content) and message.channel.id not in spam_protection:
        await message.channel.send(constants.RAGNAR)
        if not nuisance:
            spam_protection.append(message.channel.id)
            await asyncio.sleep(800)
            spam_protection.remove(message.channel.id)

    if re.match(r'(?i).*tromp.*', message.content) and message.channel.id not in spam_protection:
        await message.channel.send(constants.TROMP)
        if not nuisance:
            spam_protection.append(message.channel.id)
            await asyncio.sleep(800)
            spam_protection.remove(message.channel.id)

    if re.match(r'.*<:dj:896639618601074689>.*', message.content):
        await message.channel.send("🐖💨<:gupy:978882222054592553>")

    if re.match(r".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", message.content):  
        await message.add_reaction(constants.LOADING_EMOTE)  
        post_short = re.search(".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", message.content).group(1).strip()
        big = False
        loop = asyncio.get_event_loop()
        filename, file = await loop.run_in_executor(ThreadPoolExecutor(), reel_helper.download, message.content)

        try:
            reel_size = os.path.getsize(filename)
            print("Reel size:", reel_size)
            if  reel_size > 8388608:
                big = True
                new = await message.reply(f"This reel is: {reel_size} bytes. Give me a minute to compress it.", mention_author=False)
                filename = await loop.run_in_executor(ThreadPoolExecutor(), reel_helper.compress, post_short, file)
        except Exception as e:
            print("There do be an issue:", e)


        try:
            if big:
                await new.delete()
                
            await message.reply(file=discord.File(filename), mention_author=False)
            print("Uploaded reel")
        except Exception as e:
            print("Failed to upload reel")

        await message.remove_reaction(constants.LOADING_EMOTE, bot.user)

        try:
            shutil.rmtree(post_short)
            print("Successfully removed Instagram post")
        except OSError as e:
            print("Error: ", e)

    if re.match(r".*(https://)(twitter\.com/[^\n ]*).*", message.content):
        url = re.search(".*(https://)(twitter\.com/[^\n ]*).*", message.content).group(2)
        if message.embeds and message.embeds[0].video:
            await message.add_reaction(constants.TWITTER_EMOTE)
            
    if bot.user.mentioned_in(message):  # action on being mentioned
        #    await message.channel.send("<@" + str(constants.CHIGGIN) + ">")]
        if "mention" in spam_protection:
            await message.channel.send("My prefix is //")
        else:
            spam_protection.append("mention")
            await message.channel.send("<@" + str(constants.CHIGGIN) + ">")
            await asyncio.sleep(14400)
            spam_protection.remove("mention")

    if not message.guild:
        try:
            
            if message.author.id in awaiting_response:
                return
            else:
                awaiting_response.append(message.author.id)

            await message.channel.send("DM received. Is this feedback to make an improvement? Please reply with `yes` "
                                       "or `no`.")

            def check(m):
                return ("yes" in m.content.lower() or "no" in m.content.lower()) and m.author == message.author
            msg = await bot.wait_for('message', timeout=20.0, check=check)
  
            if "yes" in msg.content.lower():
                await message.channel.send("Thanks, I'll consider your feedback.")
                with open("feedback.txt", "a") as f:
                    f.write(f"{message.author} said {message.content} on {message.created_at}\n")
                print(f'{message.author} said {message.content} on {message.created_at}')
            else:
                await message.channel.send("...")
            awaiting_response.remove(message.author.id)
        except discord.errors.Forbidden:
            pass
        except asyncio.TimeoutError:
            await message.channel.send("Timeout. No response recorded.")
            awaiting_response.remove(message.author.id)

    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if re.match(r".*(https://)(twitter\.com/[^\n ]*).*", after.content):
        url = re.search(".*(https://)(twitter\.com/[^\n ]*).*", after.content).group(2)
        if after.embeds and after.embeds[0].video:
            await after.add_reaction(constants.TWITTER_EMOTE)
    if re.match(r'.*<:dj:896639618601074689>.*', after.content):
        await after.channel.send("🐖💨<:gupy:978882222054592553>")


@bot.event
async def on_raw_reaction_add(payload):
    """Checks posts for 1 ♻ reaction in order to manage reposts."""
    react_chan = bot.get_channel(payload.channel_id)
    message = await react_chan.fetch_message(payload.message_id)
    reaction = get(message.reactions, emoji=payload.emoji.name)
    user = payload.user_id

    if user == bot.user.id:
        return

    if message.author == bot.user and payload.emoji.name == constants.REPOST_EMOTE:
        if reaction and reaction.count >= 1:
            await message.delete()
            print("User voted repost deleted.")

    elif payload.emoji.name == constants.TWITTER_EMOTE and payload.message_id not in spam_protection and reaction.count <=2:
        if re.match(r".*(https://)(twitter\.com/[^\n ]*).*", message.content):
            if message.embeds and message.embeds[0].video:
                url = re.search(".*(https://)(twitter\.com/[^\n ]*).*", message.content).group(2)
                await message.reply("https://vx" + url, mention_author=False)
            else:
                await message.channel.send("I found a Twitter link but not a video embed.\
                If you want to include this functionality, let me know.")
            spam_protection.append(payload.message_id)
            await asyncio.sleep(600)
            spam_protection.remove(payload.message_id)


    elif payload.emoji.name == constants.ARCHIVE_EMOTE and reaction.count < 2:
        # This will become able to set on a per-server basis
        # print("embedding")
        archive_channel = bot.get_channel(int(db_fetch_archive(bot.connection, str(payload.guild_id))))

        if not archive_channel:
            return

        embed = discord.Embed(color=0xA9B0FF, title="Message link", url=message.jump_url)
        # embed is spaghetti so FIXME but later
        embed.set_author(name=message.author.name, icon_url=message.author.avatar)

        content = "Image only"
        if message.content:
            content = message.content
        embed.add_field(name="Message", value=content, inline=False)

        if message.embeds:
            main_embed = message.embeds[0]
            main_picture = main_embed.image.url
            embed.set_image(url=main_picture)

            if main_embed.type == "image":
                embed.set_image(url=main_embed.url)
            elif main_embed.type == "rich":
                embed.add_field(name=main_embed.author.name, value=main_embed.description, inline=False)
                for field in main_embed.fields:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)  # No idea how to put multiple images in an embed

        embed.set_footer(text=f"Message sent at {message.created_at} and pinned at {datetime.now()}.")

        await archive_channel.send(content=f" In {message.channel.mention} pinned by {payload.member.name}",
                                   embed=embed)


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message error: {args[0]} at time {datetime.now()}\n')
        else:
            raise

 
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


@bot.command(name='pick', help="Picks a number between 2 numbers specified.")
async def pick_random(ctx, start: int, end: int):
    num = random.randint(start, end)
    if start <= 2 <= end:
        num = 2

    await ctx.send(num)


@bot.command(name='here', help='Send in target channel for reposting.')
async def here(ctx):
    if ctx.message.author.id == constants.CHIGGIN:
        await ctx.send("No, you can't do that.")
        return

    global pref_map
    await ctx.send("Setting this channel as this server's default repost channel...")
    server_id = ctx.message.guild.id  # Used to ident server from which this was sent

    channel_id = ctx.message.channel.id
    channel_name = ctx.message.channel

    db_insert_channel(bot.connection, str(server_id), str(channel_id), channel_name)

    pref_map = db_update_map(bot.connection)

    await ctx.send("Done.")


@bot.command(name='nothere', help="Unsets this channel as your repost channel.")
async def nothere(ctx):
    if ctx.message.author.id == constants.CHIGGIN:
        await ctx.send("No, you can't do that.")
        return

    global pref_map
    await ctx.send("Unsetting this channel...")
    server_id = ctx.message.guild.id

    db_delete_channel(bot.connection, str(server_id))

    pref_map = db_update_map(bot.connection)

    await ctx.send("Done.")


@bot.command(name='archive', help='sets this channel as archive channel')
async def archive(ctx):
    global pref_map
    await ctx.send("Setting this channel as archive...")
    server_id = ctx.message.guild.id
    channel_id = ctx.message.channel.id

    db_archive(bot.connection, str(server_id), str(channel_id))

    pref_map = db_update_map(bot.connection)

    await ctx.send("Done.")


@bot.command(name='notarchive', help='unsets this channel as archive channel')
async def notarchive(ctx):
    global pref_map
    await ctx.send("Unsetting this channel...")
    server_id = ctx.message.guild.id

    db_not_archive(bot.connection, str(server_id))

    pref_map = db_update_map(bot.connection)

    await ctx.send("Done.")


@bot.command(name='nuisance', help='How annoying do you want me to be?')
@commands.has_permissions(administrator=True)
async def nuisance(ctx):
    global pref_map
    server_id = ctx.message.guild.id

    nuisance = pref_map[str(server_id)][4]

    db_nuisance(bot.connection, str(server_id))
    if nuisance:
        await ctx.send("Quieting down.")
    else:
        await ctx.send("If you say so.")

    pref_map = db_update_map(bot.connection)


@bot.command(name='test', help="testing this command")
async def test(ctx):
    global pref_map
    pref_map = db_update_map(bot.connection)
    if ctx.message.author.id == constants.CHIGGIN:
        print(pref_map)
        await ctx.send("Test run.")
    else:
        await ctx.send("No, you can't do that.")


bot.run(TOKEN)
