import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()          
    print(f'{bot.user} has connected to Discord!')

        

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

bot.run(os.environ.get("BOT_TOKEN"))
