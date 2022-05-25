import os
import discord
import random
import emojis

from discord.ext import commands
from dotenv import load_dotenv
bot = commands.Bot(command_prefix="//", description="I'm retaredd")
channel = None


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_SERVER')

@bot.event
async def on_ready():

    for guild in bot.guilds:
        print(f'Connected to: {guild}')
        if guild.name == GUILD: # figures out what the current guild is
            break

    with open('server_prefs.txt', 'r+') as prefs: # read all server preferences here
        pref = prefs.readline()
        global channel
        while pref:
            if pref.split()[0] == guild.name:
                channel = pref.split()[1]

@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hello {member.name}.'
    )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == 'Speak.':
        response2 = "I've created another Discord bot."
        await message.channel.send(response2)

    if message.content == 'raise exception':
        raise discord.DiscordException

#    if message.content.match(r'🐖.*💨.*<:dj:896639618601074689>'):
#        await message.channel.send("🐖💨<:gupy:978882222054592553>")

    if bot.user.mentioned_in(message):  # action on being mentioned
        await message.channel.send("please don't nothing works yet (but my prefix is // and //pick does work)")

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


@bot.command(name='speak', help='it doesnt work')
@commands.has_role("Torpedo")
async def speak(ctx):
    await ctx.send("I have no idea what I'm doing.")


@bot.command(name='pick', help="Picks a number between 2 numbers specified.")
async def pick_random(ctx, start: int, end: int):
    num = random.randint(start, end)
    if start <= 2 <= end:
        num = 2

    await ctx.send(num)


@bot.command(name="emoji")
async def emoji(ctx):
    await ctx.send("🐖💨<:gupy:978882222054592553>")


@bot.command(name='here', help='Send in target channel for reposting.')
async def here(ctx):
    #server_name = ctx.message.guild.name
    #print(server_name)
    pass

bot.run(TOKEN)
