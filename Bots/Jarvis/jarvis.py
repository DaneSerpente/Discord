# Home media management bot
import os
import paramiko

from discord.ext import commands
from dotenv import load_dotenv

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
NAS01_IP = os.getenv('NAS01_IP')
NAS01_UN = os.getenv('NAS01_UN')
NAS01_PW = os.getenv('NAS01_PW')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.command(name='diskspace', help='Show diskspace for the specified device')
async def df(ctx, device_name):
    if device_name.lower() == "nas01":
        ssh.connect(hostname=NAS01_IP, username=NAS01_UN, password=NAS01_PW)
        stdin, stdout, stderr = ssh.exec_command('df -h | grep vg1000')
        result = stdout.read().decode('utf-8').split()
        await ctx.send(f'Free space: {result[3]}')
        ssh.close()
    

bot.run(TOKEN)
