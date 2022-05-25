import os
import discord
import random
import re

from discord.ext import commands
from dotenv import load_dotenv

bot = commands.Bot(command_prefix="//", description="am chiggin")
channel = None

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_SERVER')


@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f'Connected to: {guild}')
        if guild.name == GUILD:  # figures out what the current guild is
            break

    game = discord.Game("with cloning")
    await bot.change_presence(status=discord.Status.online, activity=game)


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

    if message.channel.id == 979094074084692028:  # This is where the bot copies everything I say
        await message.channel.send("Heard.")

        with open("server_prefs.txt", "r") as prefs:
            pref_array = prefs.readlines()

        for pref in pref_array:
            parsed = pref.split("|")
            print(f'Echoing message in server {parsed[2]} in channel {parsed[3]}')
            echo_channel = bot.get_channel(int(parsed[1]))
            if message.content:
                await echo_channel.send(message.content)
            if message.attachments:
                await echo_channel.send("\n".join(x.url for x in message.attachments))

    if message.content == 'Speak.':
        response2 = "I've created another Discord bot."
        await message.channel.send(response2)

    if message.content == 'raise exception':
        raise discord.DiscordException

    if re.match(r'🐖.*💨.*<:dj:896639618601074689>', message.content):
        await message.channel.send("🐖💨<:gupy:978882222054592553>")

    if re.match(r'(?i).*amog.*', message.content):
        await message.channel.send("sus")
    """
    if bot.user.mentioned_in(message):  # action on being mentioned
        await message.channel.send("Ping the other one. My prefix is //.")
    """

    await bot.process_commands(message)


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
    # print(server_id, channel_id)

    with open('server_prefs.txt', 'r') as prefs:  # read all server preferences here
        pref_array = prefs.readlines()

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

    with open("server_prefs.txt", "r") as prefs:
        pref_array = prefs.readlines()

    with open("server_prefs.txt", "w") as prefs:
        for pref in pref_array:
            if pref != "\n" and int(pref.split("|")[1]) == channel_id:
                pref_array.remove(pref)
                prefs.writelines(pref_array)

    await ctx.send("Done.")


bot.run(TOKEN)
