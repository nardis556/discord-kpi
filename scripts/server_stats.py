from init import discord_connector, database_connector
from datetime import datetime
from utils import database_query
import discord
import asyncio

async def gather_server_metrics():
    for guild in discord_connector.guilds:
        guild_details = await discord_connector.fetch_guild(guild.id)

        total_members = guild_details.approximate_member_count
        online_members = guild_details.approximate_presence_count
        offline_members = total_members - online_members
        num_roles = len(guild.roles)
        num_text_channels = len(guild.text_channels)
        num_voice_channels = len(guild.voice_channels)
        num_categories = len(guild.categories)

        await database_query(
            "INSERT INTO server_metrics (timestamp, guild_id, total_members, online_members, offline_members, num_roles, num_text_channels, num_voice_channels, num_categories) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (datetime.now(), guild.id, total_members, online_members, offline_members, num_roles, num_text_channels, num_voice_channels, num_categories)
        )

@discord_connector.event
async def on_ready():
    print(f'{discord_connector.user.name} connected')
    await gather_server_metrics()
    for task in asyncio.all_tasks():
        task.cancel()

if __name__ == "__main__":
    try:
        discord_connector.run_bot()
    except discord.ConnectionClosed:
        print("connection closed")
    except asyncio.CancelledError:
        print("cancelled error")
