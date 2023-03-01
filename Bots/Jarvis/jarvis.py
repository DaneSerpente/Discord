# Home media management bot
import os
import paramiko
import requests
import discord
import urllib.request
import re

from discord.ext import commands
from dotenv import load_dotenv
from urllib.parse import quote
from datetime import datetime
#from requests import get, post

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
RAPIKEY = os.getenv('RADARR_TOKEN')
RURL = 'http://' + str(os.getenv('RADARR_URL'))
SAPIKEY = os.getenv('SONARR_TOKEN')
SURL = 'http://' + str(os.getenv('SONARR_URL'))
NAS01 = [os.getenv('NAS01_IP'), os.getenv('NAS01_UN'), os.getenv('NAS01_PW')]
NAS02 = [os.getenv('NAS02_IP'), os.getenv('NAS02_UN'), os.getenv('NAS02_PW')]
SNAS01 = [os.getenv('SNAS01_IP'), os.getenv('SNAS01_UN'), os.getenv('SNAS01_PW')]
Odroid = [os.getenv('Odroid_IP'), os.getenv('Odroid_UN'), os.getenv('Odroid_PW')]

bot = commands.Bot(command_prefix='!')

def radarr(cmd, opt, prof):
    global data

    if cmd.lower() == 'search':
        term = quote(opt)
        r = requests.get(RURL + '/api/v3/movie/lookup?term=' + term, headers={'X-Api-Key':RAPIKEY})
        data = r.json()
        menu = ''
        for idx, item in enumerate(data):
            title = item['title']
            year = item['year']
            menu += (str(idx + 1) + f' - {title} ({year})\n')
        return(menu)

    if cmd.lower() == 'download':
        movie = data[int(opt) - 1] 
        profile = prof.lower()
        if profile == 'yts':
            profile = 9
        elif profile == 'remux':
            profile = 7
        elif profile == '4k-rip':
            profile = 8
        elif profile == 'hd-rip':
            profile = 10
        headers = {'X-Api-Key': RAPIKEY}
        json_data = {
            'title': movie['title'],
            'qualityProfileId': profile,
            'tmdbid': movie['tmdbId'],
            'rootFolderPath': '/media/nas/media/Movies/',
            'addOptions': {'searchForMovie': True}
        }
        add_move = requests.post(RURL + "/api/v3/movie", headers=headers, json=json_data) 
        if movie['status'] == 'released':
            return(f'Downloading {movie["title"]}')
        else:
            return(f' {movie["title"]} is not yet available for download. Added to library and monitored')

def sonarr(cmd, opt, prof):
    global data

    if cmd.lower() == 'search':
        term = quote(opt)
        r = requests.get(SURL + '/api/v3/series/lookup?term=' + term, headers={'X-Api-Key':SAPIKEY})
        data = r.json()[0:20]
        menu = ''
        for idx, item in enumerate(data):
            title = item['title']
            year = item['year']
            menu += (str(idx + 1) + f' - {title} ({year})\n')
        return(menu)

    if cmd.lower() == 'download':
        show = data[int(opt) - 1] 
        profile = prof.lower()
        if profile == '4k-webrip':
            profile = 9
        elif profile == 'remux':
            profile = 7
        elif profile == '4k-rip':
            profile = 8
        elif profile == 'hd-webrip':
            profile = 10
        headers = {'X-Api-Key': SAPIKEY}
        json_data = {
            'title': show['title'],
            'qualityProfileId': profile,
            'tvdbid': show['tvdbId'],
            'rootFolderPath': '/media/nas/media/Shows/',
            'addOptions': {'monitor': 'all', 'searchForMissingEpisodes': True, 'searchForCutoffUnmetEpisodes': True},
            'monitored': True,
            'languageProfileId': 1
        }
        add_show= requests.post(SURL + "/api/v3/series", headers=headers, json=json_data) 
        return(f'{show["title"]} added to library')


def disk_space(device):
    if device.lower() == 'nas01':
        ssh.connect(hostname=NAS01[0], username=NAS01[1], password=NAS01[2])
        stdin, stdout, stderr = ssh.exec_command('df -h | grep volume1$')
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

def recycle(cmd):
    ssh.connect(hostname=NAS01[0], username=NAS01[1], password=NAS01[2])
    if cmd.lower() == 'check':
        stdin, stdout, stderr = ssh.exec_command('du -hs /volume1/Media/#recycle')
        result = stdout.read().decode('utf-8').split()
        return result[0] 

    elif cmd.lower() == 'empty':
        stdin, stdout, stderr = ssh.exec_command('rm -r /volume1/Media/#recycle/*')
    ssh.close()

def raid(option='status'):
    req_info = ('state:', 'raidz1', 'caef', 'b56c', 'b5c2', '7fc6', 'errors:') 
    stat = []
    ssh.connect(hostname=SNAS01[0], username=SNAS01[1], password=SNAS01[2])
    for i in req_info:
        stdin, stdout, stderr = ssh.exec_command(f'zpool status | grep {i} | head -1')
        if i == 'errors:':
            result = stdout.read().decode('utf-8')
            stat.append(result)
        else:
            result = stdout.read().decode('utf-8').split()
            stat.append(result[1])
    return stat 
    ssh.close()

def vpn(dev, cmd):
    if dev == 'SNAS01':
        host = SNAS01
    elif dev == 'Odroid':
        host = Odroid

    ssh.connect(hostname=host[0], username=host[1], password=host[2])

    if cmd.lower() == 'status':
        if dev == 'SNAS01':
            stdin, stdout, stderr = ssh.exec_command('iocage exec transmission service openvpn status')
            if 'running' in stdout.read().decode('utf-8'):
                return "VPN is running"
            else:
                return "VPN is not running"  
        else:
            stdin, stdout, stderr = ssh.exec_command('systemctl status openvpn | grep Active')
            if 'active' in stdout.read().decode('utf-8'):
                return "VPN is running"
            else:
                return "VPN is not running"
    elif cmd.lower() == 'check':
        if dev == 'SNAS01':            
            stdin, stdout, stderr = ssh.exec_command('iocage exec transmission ping -c 1 -t 2 8.8.8.8 | grep ttl')
            if 'ttl' in stdout.read().decode('utf-8'):
                return "VPN is operating properly"
            else:
                return "There is a problem with the VPN"
        else:
            stdin, stdout, stderr = ssh.exec_command('ping -c 1 -t 2 8.8.8.8 | grep ttl')
            if 'ttl' in stdout.read().decode('utf-8'):
                return "VPN is operating properly"
            else:
                return "There is a problem with the VPN"
    elif cmd.lower() == 'restart':
        if dev == 'SNAS01':            
            ssh.exec_command('iocage exec transmission service openvpn restart')
            return "VPN service has been restarted"
        else:
            ssh.exec_command('systemctl restart openvpn')
            return "VPN service has been restarted"
    ssh.close()
        
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.command(name='radarr')
async def radar_cmds(ctx, cmd, opt, prof='yts'):
    options = ('search', 'download', 'help', 'info')
    profiles = ('4k-rip', 'hd-rip', 'remux', 'yts')

    if cmd not in options:
        response = 'Available options:\nsearch\ninfo\ndownload\nhelp'
        await ctx.send(response)
    if prof not in profiles:
        response = 'Available quality profiles:\nremux\n4k-rip\nhd-rip\nyts'
        await ctx.send(response)

    elif cmd == 'info':
        query = data[int(opt) - 1]
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + quote(query['title'] + ' ' + str(query['year']) + ' ' + 'official trailer'))
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        youtube_url = 'https://www.youtube.com/watch?v=' + video_ids[0]
        imdb_url = 'https://www.imdb.com/title/' + str(query['imdbId'])
        tmdb_url = 'https://www.themoviedb.org/movie/' + str(query['tmdbId'])
        embed=discord.Embed(
        title=query['title'] + ' (' + str(query['year']) + ')',
            url=tmdb_url,
            color=discord.Color.blue())
        embed.set_thumbnail(url=query['remotePoster'])
        embed.add_field(name='**Overview**', value=query['overview'], inline=False)
        if 'imdb' in query['ratings']:
            embed.add_field(name='**IMDB Rating**', value=query['ratings']['imdb']['value'], inline=True)
        if 'rottenTomatoes' in query['ratings']:
            embed.add_field(name='**Rotten Rating**', value=str(query['ratings']['rottenTomatoes']['value']) + '%', inline=True)
        embed.add_field(name='**Status**', value=query['status'].capitalize(), inline=True)
        if query['hasFile'] == True:
            embed.add_field(name='**In Library**', value=query['movieFile']['relativePath'], inline=False)
        elif query['hasFile'] == False and query['monitored'] == True:
            embed.add_field(name='**In Library**', value='Monitored', inline=False)
        embed.add_field(name='**Genres**', value=', '.join(query['genres']), inline=False)
        embed.add_field(name='**Links**', value=f'[Trailer]({youtube_url}) / [IMBd]({imdb_url}) / [TMDb]({tmdb_url})', inline=False)
        if len(query['images']) != 1:
            embed.set_image(url=query['images'][1]['remoteUrl'])
        await ctx.send(embed=embed)
    else:
        response = radarr(cmd, opt, prof)
        await ctx.send(response)

@bot.command(name='sonarr')
async def sonarr_cmds(ctx, cmd, opt, prof='hd-webrip'):
    options = ('search', 'download', 'help', 'info')
    profiles = ('4k-rip', 'hd-webrip', 'remux', '4k-webrip')

    if cmd not in options:
        response = 'Available options:\nsearch\ninfo\ndownload\nhelp'
        await ctx.send(response)
    if prof not in profiles:
        response = 'Available quality profiles:\nremux\n4k-rip\n4k-webrip\nhd-webrip'
        await ctx.send(response)

    elif cmd == 'info':
        query = data[int(opt) - 1]
        imdb_url = 'https://www.imdb.com/title/' + str(query['imdbId'])
        tvdb_url = 'https://thetvdb.com/?tab=series&id=' + str(query['tvdbId'])
        for i in query['images']:
            if i['coverType'] == 'poster':
                poster_url = i['remoteUrl']
            elif i['coverType'] == 'fanart':
                fanart_url = i['remoteUrl']
        embed=discord.Embed(
        title=query['title'] + ' (' + str(query['year']) + ')',
            url=tvdb_url,
            color=discord.Color.blue())
        embed.set_thumbnail(url=poster_url)
        embed.add_field(name='**Overview**', value=query['overview'], inline=False)
        embed.add_field(name='**Rating**', value=query['ratings']['value'], inline=True)
        embed.add_field(name='**Seasons**', value=query['statistics']['seasonCount'], inline=True)
        embed.add_field(name='**Status**', value=query['status'].capitalize(), inline=True)
        if query['seasonFolder'] == True:
            embed.add_field(name='**In Library**', value='Yes', inline=False)
        else:
            embed.add_field(name='**In Library**', value='No', inline=False)
        embed.add_field(name='**Genres**', value=', '.join(query['genres']), inline=False)
        embed.add_field(name='**Links**', value=f'[IMBd]({imdb_url}) / [TVDb]({tvdb_url})', inline=False)
        if len(query['images']) != 1:
            embed.set_image(url=fanart_url)
        await ctx.send(embed=embed)
    else:
        response = sonarr(cmd, opt, prof)
        await ctx.send(response)
        

@bot.command(name='NAS01', help='Show details for NAS01')
async def df(ctx, cmd, subcmd=''):
    if cmd.lower() == 'diskspace':
        df = disk_space('nas01')
        response = (f"Total space: {df[0]}\n"
                    f"Used space: {df[1]}\n"
                    f"Free space: {df[2]}\n"
                    f"Capacity: {df[3]}\n")
        await ctx.send(response)

    elif cmd.lower() == 'recycle':
        if subcmd.lower() == 'check':
            size = recycle('check')
            response = f"{size} in the recycling bin"
            await ctx.send(response)
        elif subcmd.lower() == 'empty':
            recycle('empty')
            response = "Recycling bin has been emptied"
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

    elif cmd.lower() == 'raid':
        r_stat = raid('subcmd')
        response = (f"Datastore: {r_stat[0]}\n"
                    f"RAID: {r_stat[1]}\n"
                    f"HDD01: {r_stat[2]}\n"
                    f"HDD02: {r_stat[3]}\n"
                    f"HDD03: {r_stat[4]}\n"
                    f"HDD04: {r_stat[5]}\n\n"
                    f"{r_stat[6]}")
        await ctx.send(response)

    elif cmd.lower() == 'vpn':
        if subcmd == 'status':
            await ctx.send(vpn('SNAS01', 'status'))
        elif subcmd == 'check':
            await ctx.send(vpn('SNAS01', 'check'))
        elif subcmd == 'restart':
            await ctx.send(vpn('SNAS01', 'restart')) 

bot.run(TOKEN)
