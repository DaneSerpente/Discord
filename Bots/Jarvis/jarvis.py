# Home media management bot
import os
import paramiko

from discord.ext import commands
from dotenv import load_dotenv

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
NAS01 = [os.getenv('NAS01_IP'), os.getenv('NAS01_UN'), os.getenv('NAS01_PW')]
NAS02 = [os.getenv('NAS02_IP'), os.getenv('NAS02_UN'), os.getenv('NAS02_PW')]
SNAS01 = [os.getenv('SNAS01_IP'), os.getenv('SNAS01_UN'), os.getenv('SNAS01_PW')]
Odroid = [os.getenv('Odroid_IP'), os.getenv('Odroid_UN'), os.getenv('Odroid_PW')]

bot = commands.Bot(command_prefix='!')

def disk_space(device):
    if device.lower() == 'nas01':
        ssh.connect(hostname=NAS01[0], username=NAS01[1], password=NAS01[2])
        stdin, stdout, stderr = ssh.exec_command('df -h | grep vg1000')
        result = stdout.read().decode('utf-8').split()
        df = [result[1], result[2], result[3], result[4]]
        return df
        ssh.close()

    if device.lower() == 'nas02':
        ssh.connect(hostname=NAS02[0], username=NAS02[1], password=NAS02[2])
        stdin, stdout, stderr = ssh.exec_command('df -h | grep md0')
        result = stdout.read().decode('utf-8').split()
        df = [result[1], result[2], result[3], result[4]]
        return df
        ssh.close()

    if device.lower() == 'snas01':
        ssh.connect(hostname=SNAS01[0], username=SNAS01[1], password=SNAS01[2])
        stdin, stdout, stderr = ssh.exec_command('df -h | grep "^datastore/media"')
        result = stdout.read().decode('utf-8').split()
        df = [result[1], result[2], result[3], result[4]]
        return df
        ssh.close()

def raid(option='status'):
        req_info = ('raidz1', 'caef', 'b56c', 'b5c2', '7fc6') 
        stat = []
        ssh.connect(hostname=SNAS01[0], username=SNAS01[1], password=SNAS01[2])
        for i in req_info:
            stdin, stdout, stderr = ssh.exec_command(f'zpool status | grep {i}')
            result = stdout.read().decode('utf-8').split()
            stat.append(result[1])
        return stat 
        ssh.close()
        
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.command(name='NAS01', help='Show details for NAS01')
async def df(ctx, cmd):
    if cmd.lower() == 'diskspace':
        df = disk_space('nas01')
        response = (f"Total space: {df[0]}\n"
                    f"Used space: {df[1]}\n"
                    f"Free space: {df[2]}\n"
                    f"Capacity: {df[3]}\n")
        await ctx.send(response)
    
@bot.command(name='NAS02', help='Show details for NAS02')
async def df(ctx, cmd):
    if cmd.lower() == 'diskspace':
        df = disk_space('nas02')
        response = (f"Total space: {df[0]}\n"
                    f"Used space: {df[1]}\n"
                    f"Free space: {df[2]}\n"
                    f"Capacity: {df[3]}\n")
        await ctx.send(response)

@bot.command(name='SNAS01', help='Show details for SNAS01')
async def df(ctx, cmd, subcmd=''):
    if cmd.lower() == 'diskspace':
        df = disk_space('snas01')
        response = (f"Total space: {df[0]}\n"
                    f"Used space: {df[1]}\n"
                    f"Free space: {df[2]}\n"
                    f"Capacity: {df[3]}\n")
        await ctx.send(response)

    if cmd.lower() == 'raid':
        r_stat = raid('subcmd')
        response = f"RAID: {r_stat[0]}"
        await ctx.send(response)

bot.run(TOKEN)
