import os
import discord

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('ODkxNTI3Nzk2OTQ4NjI3NTE2.YU_p9g.kJHsvqqlj07UzPve7iVXMBKULwQ')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(TOKEN)
