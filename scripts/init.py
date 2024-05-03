import sys
sys.path.append("/home/lars/discord-kpi")
from config import discord_bot_token as token, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from connectors import DatabaseConnector, DiscordConnector
import discord

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.emojis_and_stickers = True

database_connector = DatabaseConnector(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
discord_connector = DiscordConnector(token, "!", intents)