import asyncio
import os
import discord

from discord.ext import commands
from dotenv import load_dotenv
from storage import *


class Bot(commands.Bot):
    """Override initialization to include database."""

    def __init__(self):
        super().__init__(command_prefix="//", description="am chiggin")
        self.connection = db_connect()

    async def close(self):
        db_disconnect(self.connection)
        await super().close()
