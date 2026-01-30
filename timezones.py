# This file will handle the timezone system. (lies)

import discord
from discord import app_commands
from discord.ext import commands
from storage import *
from datetime import datetime, timezone, timedelta

class TimezoneSelect(discord.ui.Select):
    def __init__(self, bot):
        options=[
            discord.SelectOption(label=-12),
            discord.SelectOption(label=-11),
            discord.SelectOption(label=-10),
            discord.SelectOption(label=-9),
            discord.SelectOption(label=-8),
            discord.SelectOption(label=-7),
            discord.SelectOption(label=-6),
            discord.SelectOption(label=-5),
            discord.SelectOption(label=-4),
            discord.SelectOption(label=-3),
            discord.SelectOption(label=-2),
            discord.SelectOption(label=-1),
            discord.SelectOption(label=0, description="Choose this if your timezone matches UTC time."),
            discord.SelectOption(label=1),
            discord.SelectOption(label=2),
            discord.SelectOption(label=3),
            discord.SelectOption(label=4),
            discord.SelectOption(label=5),
            discord.SelectOption(label=6),
            discord.SelectOption(label=7),
            discord.SelectOption(label=8),
            discord.SelectOption(label=9),
            discord.SelectOption(label=10),
            discord.SelectOption(label=11),
            discord.SelectOption(label=12)
            ]
        self.bot = bot
        super().__init__(placeholder="Choose an offset",max_values=1,min_values=1,options=options)

    async def callback(self, interaction):
        await interaction.response.send_message(f"Set your timezone to UTC: {self.values[0]}.", ephemeral=True)
        mutuals = interaction.user.mutual_guilds

        # Check if this user is stored. If so, let them know their choice is being overridden. If not,
        # let them know their choice is being saved. Call database method here.
        db_insert_update_user(self.bot.connection, interaction.user.id, interaction.user.name, self.values[0], mutuals)


class TimezoneSelectView(discord.ui.View):
    def __init__(self, bot, timeout = 30,):
        super().__init__(timeout=timeout)
        self.add_item(TimezoneSelect(bot=bot))


class TimezoneHelper(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def construct_embed(self, times, server):
        # I cannot be arsed.
        embed = discord.Embed(title=f"Local User Timezones in {server.name}", description="This is everybody's current time.")
        values = ""
        current_time = datetime.now(timezone.utc)
        # Here, convert the user id to a nickname and convert the time delta to a timezone.
        for entry in times:
            user = await server.fetch_member(int(entry[0]))
            nickname = user.display_name
            user_time = (current_time + timedelta(hours= int(entry[2]))).strftime("%H:%M:%S")

            values += f"{nickname} {user_time}\n"

        embed.add_field(name="Users", value=values)
        embed.set_footer(text="To register, type /settime.")
        return embed
        
    @app_commands.command(name="settime", description="Tell me what timezone you live in!")
    async def set_time(self, interaction: discord.Interaction):
        current_time = datetime.now(timezone.utc)
        message = current_time.strftime("The current time is %H:%M:%S in UTC (24 hour time). Please use this reference to select your timezone as its offset from UTC.")
        await interaction.response.send_message(message, view=TimezoneSelectView(bot=self.bot), ephemeral=True)

    @app_commands.command(name="timezones", description="I'll tell you what timezones everyone else is in!")
    async def get_times(self, interaction: discord.Interaction):
        await interaction.response.defer()
        times = db_get_server_timezones(self.bot.connection, interaction.guild.id)
        embed = await self.construct_embed(times, interaction.guild)
        await interaction.followup.send("Here you go!", embed=embed)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload):
        user_id = payload.user.id
        server_id = payload.guild_id
        db_delete_user_server(self.bot.connection, server_id, user_id)


    # TODO: That thing Mo suggested

    # TODO: /setevent. Using a dropdown, the user can set the time they want 
        

