import asyncio
import os
import discord

from discord.ext import commands
from dotenv import load_dotenv
from storage import *


class Bot(commands.Bot):
    """Override initialization to include database."""

    def __init__(self, command_prefix, help_command="help", description=None):
        super().__init__(command_prefix, help_command, description)
        self.connection = db_connect()

    def start(self, *args, **kwargs):
        super().start(self, *args, **kwargs)

    def close(self):
        db_disconnect(self.connection)
        super().close()
