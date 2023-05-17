import discord
from discord.ext import commands
import sys
sys.path.append("/home/lars/discord-kpi")
from config import discord_bot_token as token

bot = commands.Bot(command_prefix='!', )

@bot.command()
async def usercount(ctx):
    guild = ctx.guild
    no_of_members = guild.member_count
    await ctx.send(f'Number of members: {no_of_members}')

bot.run(token)

