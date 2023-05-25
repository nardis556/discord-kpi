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

class CustomCache:
    def __init__(self, size=10000):
        self.size = size
        self.cache = []

    def add(self, item):
        if len(self.cache) >= self.size:
            self.cache.pop(0)
        self.cache.append(item)

    def get(self, id):
        for item in self.cache:
            if item.message_id == id:
                return item
        return None

    def load_from_db(self):
        db = database_connector.connect()
        cursor = db.cursor()
        cursor.execute(f"SELECT message_id FROM discord ORDER BY timestamp DESC LIMIT {self.size}")
        for message_id in cursor.fetchall():
            self.cache.append(message_id[0])
        cursor.close()
        print("caching initialized")

message_cache = CustomCache()
message_cache.load_from_db()
