
import discord
from discord.ext import commands
import mysql.connector

class DatabaseConnector:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def connect(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

class DiscordConnector(commands.Bot):
    def __init__(self, token, prefix, intents):
        super().__init__(command_prefix=prefix, intents=intents)
        self.token = token

    def run_bot(self):
        self.run(self.token)
