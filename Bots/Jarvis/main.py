import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")



async def main():
    async with bot:
        await bot.load_extension('cogs.radarr')
        await bot.load_extension('cogs.sonarr')
        await bot.start(TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())