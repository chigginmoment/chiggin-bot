import asyncio
import os
import discord
import random
import re
import constants
import psycopg2
from datetime import datetime
from bot import Bot

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

    game = discord.Game("implementing database methods")
    await bot.change_presence(status=discord.Status.online, activity=game)

    with open("server_prefs.txt", "r") as prefs:
        global pref_array
        pref_array = prefs.readlines()


@bot.event
async def on_guild_join():
    print("Joined new server.")


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

        for pref in pref_array:
            parsed = pref.split("|")
            channel_name = parsed[3].strip("\n")
            print(f"Echoing message in server {parsed[2]} in channel {channel_name}")
            echo_channel = bot.get_channel(int(parsed[1]))
            if message.content:
                await echo_channel.send(message.content)
            if message.attachments:
                await echo_channel.send("\n".join(x.url for x in message.attachments))

    if message.content == 'raise exception':
        raise discord.DiscordException

    if re.match(r'(?i).*amog.*', message.content) and message.channel.id not in spam_protection:
        roll = random.randint(1, 3)
        if roll == 1:
            spam_protection.append(message.channel.id)
            await message.channel.send("sus")
            await asyncio.sleep(20)
            spam_protection.remove(message.channel.id)

    if re.match(r'(?i).*ragnar.*', message.content) and message.channel.id not in spam_protection:
        spam_protection.append(message.channel.id)
        await message.channel.send(constants.RAGNAR)
        await asyncio.sleep(180)
        spam_protection.remove(message.channel.id)

    if re.match(r'.*<:dj:896639618601074689>.*', message.content):
        await message.channel.send("🐖💨<:gupy:978882222054592553>")

    if bot.user.mentioned_in(message):  # action on being mentioned
        await message.channel.send("<@" + str(constants.CHIGGIN) + ">")

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
            # print(f'{message.author} said {message.content} on {message.created_at}')
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

    # print(payload.emoji.name == "😭")

    flag = False
    for pref in pref_array:
        if message.channel.id == int(pref.split("|")[1]):
            flag = True

    if message.author == bot.user and payload.emoji.name == "♻️" and flag:
        if reaction and reaction.count >= 3:
            await message.delete()

    elif payload.emoji.name == "😭" and reaction.count < 2 and payload.guild_id == 722841977129009296:
        # This will become able to set on a per-server basis
        # print("embedding")
        archive_channel = bot.get_channel(constants.ARCHIVE)
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
            f.write(f'Unhandled message: {args[0]}\n')
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

    with open("server_prefs.txt", 'w') as prefs:
        for pref in pref_array:
            if pref != "\n" and int(pref.split("|")[0]) == server_id:  # if reached an existing entry
                pref_array[pref_array.index(pref)] = f'{server_id}|{channel_id}|{server_name}|{channel_name}\n'
                prefs.writelines(pref_array)
                await ctx.send("Done.")
                return

        # if made it here then there is no empty newline, only write at end of file
        new_pref = f'{server_id}|{channel_id}|{server_name}|{channel_name}\n'
        pref_array.append(new_pref)
        prefs.writelines(pref_array)
        await ctx.send("Done.")
        return


@bot.command(name='nothere', help="Unsets this channel as your repost channel.")
async def nothere(ctx):
    await ctx.send("Unsetting this channel...")
    channel_id = ctx.message.channel.id

    with open("server_prefs.txt", "w") as prefs:
        for pref in pref_array:
            if pref != "\n" and int(pref.split("|")[1]) == channel_id:
                pref_array.remove(pref)
                prefs.writelines(pref_array)

    await ctx.send("Done.")


bot.run(TOKEN)
