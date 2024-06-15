
import discord
from discord.ext import commands
from sshtunnel import SSHTunnelForwarder
import mysql.connector
import sys
sys.path.append("/home/lars/discord-kpi")


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

class BastionDatabaseConnector:
    def __init__(self, ssh_host, ssh_port, ssh_username, ssh_key_path, db_host, db_port, db_user, db_password, db_name):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_key_path = ssh_key_path
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.server = None

    def connect(self):
        self.server = SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_username,
            ssh_pkey=self.ssh_key_path,
            remote_bind_address=(self.db_host, self.db_port)
        )
        self.server.start()

        connection = mysql.connector.connect(
            host=self.server.local_bind_host,
            port=self.server.local_bind_port,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name
        )
        return connection

    def close_tunnel(self):
        if self.server:
            self.server.stop()

class DiscordConnector(commands.Bot):
    def __init__(self, token, prefix, intents):
        super().__init__(command_prefix=prefix, intents=intents)
        self.token = token

    def run_bot(self):
        self.run(self.token)
