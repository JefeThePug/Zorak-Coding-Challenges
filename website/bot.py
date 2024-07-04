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

@bot.command()
async def get_roles(ctx):
    guild = ctx.guild
    roles = guild.roles
    role_details = [f'{role.name}: {role.id}' for role in roles]
    await ctx.send('\n'.join(role_details))

@bot.command()
async def list_members(ctx):
    members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
    member_list = '\n'.join(f'{member.name} joined at {member.joined_at}' for member in members)
    await ctx.send(member_list)

@bot.command()
async def get_channels(ctx):
    guild = ctx.guild
    channels = guild.channels
    channel_details = [f'{channel.name}: {channel.id}' for channel in channels]
    await ctx.send('\n'.join(channel_details))

bot.run(os.environ.get("BOT_TOKEN"))
