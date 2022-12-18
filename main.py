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

bot = Bot()
channel = None

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_SERVER')

awaiting_response = []
pref_array = []
spam_protection = []

@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f'Connected to: {guild}')
        if guild.name == GUILD:  # figures out what the current guild is
            break

    game = discord.Game("with myself")
    await bot.change_presence(status=discord.Status.online, activity=game)

    global pref_array
    pref_array = db_update(bot.connection)
    print("Ready on ", datetime.now())


@bot.event
async def on_guild_join(guild):
    print("Joined new server.")
    db_add_server(bot.connection, str(guild.id), guild.name)


@bot.event
async def on_guild_remove(guild):
    # TODO: Remove guild from database
    db_remove_server(bot.connection, str(guild.id))
    print("Left server.")


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

    if message.author == bot.user:
        return

    if message.channel.id == constants.CHANNEL:  # This is where the bot copies everything I say
        await message.channel.send("Heard.")

        print("Echoing message.")
        for pref in pref_array:
            if pref[1] is not None:
                channel_name = pref[4]
                print(f"Echoing message in server {pref[3]} in channel {channel_name}")
                echo_channel = bot.get_channel(int(pref[1]))
                if message.content:
                    await echo_channel.send(message.content)
                if message.attachments:
                    await echo_channel.send("\n".join(x.url for x in message.attachments))

        print("Done echoing.")

    if message.content == 'raise exception':
        raise discord.DiscordException

    # print(re.match(r"(?i)(^sus )|(.* sus$)|(.* sus .*)|(^sus$)", message.content), message.content)

    if re.match(r"(?i)(^sus )|(.* sus$)|(.* sus .*)|(^sus$)", message.content) and message.channel.id not in spam_protection:
        roll = random.randint(1, 5)
        if roll == 1:
            spam_protection.append(message.channel.id)
            await message.channel.send("<a:RockEyebrow:970449809121112096>")
            await asyncio.sleep(800)
            spam_protection.remove(message.channel.id)

    if re.match(r'(?i).*amog.*', message.content) and message.channel.id not in spam_protection:
        roll = random.randint(1, 5)
        if roll == 1:
            spam_protection.append(message.channel.id)
            await message.channel.send(random.choice(constants.AMOGUS_GIFS))
            await asyncio.sleep(800)
            spam_protection.remove(message.channel.id)

    if re.match(r'(?i).*ragnar.*', message.content) and message.channel.id not in spam_protection:
        spam_protection.append(message.channel.id)
        await message.channel.send(constants.RAGNAR)
        await asyncio.sleep(84600)
        spam_protection.remove(message.channel.id)

    if re.match(r'.*<:dj:896639618601074689>.*', message.content):
        await message.channel.send("🐖💨<:gupy:978882222054592553>")

    if re.match(r".*https:\/\/www\.instagram\.com\/reel\/(.*)\/.*", message.content):

        # print("amogus")

        # reply = await asyncio.to_thread(reel_helper.post_reel, message=message)

        # if reply == -1:
        #     await message.reply("Reel embed failed", mention_author=False)
        # else:
        #     await message.reply(file=discord.File(reply), mention_author=False)

        
        print("detected post")
        post_id = reel_helper.download(message.content).strip()
        print("Downloaded Instagram post: ", post_id)
        for file in os.listdir(f"{post_id}"):
            if file.endswith(".mp4"):
                print(f"{post_id}/{file}")
                try:
                    if os.path.getsize(f"{post_id}/{file}") > 8388608:
                        await message.reply("Reel embed failed: file too large. Compression coming soontm.")
                        print("Uploading reel failed: Reel too large.")
                    else:
                        await message.reply(file=discord.File(f"{post_id}/{file}"), mention_author=False)
                        print("Uploaded reel")
                except Exception as e:
                    await message.reply("Reel embed failed: "+ e)
                    print("Uploading reel failed: "+ e)
                break
        
        try:
            shutil.rmtree(post_id)
            print("Successfully removed Instagram post")
        except OSError as e:
            print("Error: ", e)
            
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
async def on_raw_reaction_add(payload):
    """Checks posts for 3 ♻ reaction in order to manage reposts."""
    react_chan = bot.get_channel(payload.channel_id)
    message = await react_chan.fetch_message(payload.message_id)
    reaction = get(message.reactions, emoji=payload.emoji.name)

    flag = False
    for pref in pref_array:
        if str(message.channel.id) == pref[1]:
            flag = True

    if message.author == bot.user and payload.emoji.name == constants.REPOST_EMOTE and flag:
        if reaction and reaction.count >= 1:
            await message.delete()
            print("User voted repost deleted.")

    elif payload.emoji.name == constants.ARCHIVE_EMOTE and reaction.count < 2:
        # This will become able to set on a per-server basis
        # print("embedding")
        archive_channel = bot.get_channel(int(db_fetch_archive(bot.connection, str(payload.guild_id))))

        if not archive_channel:
            return

        embed = discord.Embed(color=0xA9B0FF, title="Message link", url=message.jump_url)
        # embed is spaghetti so FIXME but later
        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)

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
            f.write(f'Unhandled message content {args[0]} at time {datetime.now()}\n')
        else:
            raise

 
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


"""
@bot.command(name='speak', help='it doesnt work')
@commands.has_role("Torpedo")
async def speak(ctx):
    await ctx.send("This function tests role permissions.")
"""


@bot.command(name='pick', help="Picks a number between 2 numbers specified.")
async def pick_random(ctx, start: int, end: int):
    num = random.randint(start, end)
    if start <= 2 <= end:
        num = 2

    await ctx.send(num)


@bot.command(name='here', help='Send in target channel for reposting.')
async def here(ctx):
    await ctx.send("Setting this channel as this server's default repost channel...")
    server_id = ctx.message.guild.id  # Used to ident server from which this was sent
    server_name = ctx.message.guild.name

    channel_id = ctx.message.channel.id
    channel_name = ctx.message.channel

    db_insert_channel(bot.connection, str(server_id), str(channel_id), channel_name)

    global pref_array
    pref_array = db_update(bot.connection)

    await ctx.send("Done.")


@bot.command(name='nothere', help="Unsets this channel as your repost channel.")
async def nothere(ctx):
    await ctx.send("Unsetting this channel...")
    server_id = ctx.message.guild.id

    db_delete_channel(bot.connection, str(server_id))

    global pref_array
    pref_array = db_update(bot.connection)

    await ctx.send("Done.")


@bot.command(name='archive', help='sets this channel as archive channel')
async def archive(ctx):
    await ctx.send("Setting this channel as archive...")
    server_id = ctx.message.guild.id
    channel_id = ctx.message.channel.id

    db_archive(bot.connection, str(server_id), str(channel_id))

    global pref_array
    pref_array = db_update(bot.connection)

    await ctx.send("Done.")


@bot.command(name='notarchive', help='unsets this channel as archive channel')
async def notarchive(ctx):
    await ctx.send("Unsetting this channel...")
    server_id = ctx.message.guild.id

    db_not_archive(bot.connection, str(server_id))

    global pref_array
    pref_array = db_update(bot.connection)

    await ctx.send("Done.")


@bot.command(name='test', help="testing this command")
async def test(ctx):

    # print(pref_array)
    print(spam_protection)
    await ctx.send("Test program run.")


bot.run(TOKEN)
