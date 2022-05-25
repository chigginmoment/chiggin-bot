import os
import discord
import random

from discord.ext import commands
from dotenv import load_dotenv
bot = commands.Bot(command_prefix="//", description="I'm retaredd")



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_SERVER')

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


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


@bot.command(name='Speak', help='it doesnt work')
@commands.has_role("Torpedo")
async def speak(ctx):
    await ctx.send("I have no idea what I'm doing.")


@bot.command(name='pick', help="Picks a number between 2 numbers specified.")
async def pick_random(ctx, start: int, end: int):
    num = random.randint(start, end)
    if start < 2 < end:
        num = 2

    await ctx.send(num)


bot.run(TOKEN)
