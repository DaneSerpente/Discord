# cogs/sonarr.py

import discord
from discord.ext import commands
from clients.sonarr_client import SonarrClient
from utils.media_tools import youtube_trailer
import os

class SonarrCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sonarr = SonarrClient(
            base_url=os.getenv("SONARR_URL"),
            api_key=os.getenv("SONARR_API_KEY")
        )
        self.search_cache = {}  # Store search results per user

    @commands.group()
    async def sonarr(self, ctx):
        """Sonarr command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Available subcommands: `search`, `info`, `download`")

    @sonarr.command(name='search')
    async def search_series(self, ctx, *, query: str):
        """Search for a TV series in Sonarr."""
        try:
            results = self.sonarr.search_series(query)
            if not results:
                await ctx.send(f"No results found for '{query}'.")
                return

            results = results[:20]
            self.search_cache[ctx.author.id] = results

            embed = discord.Embed(title=f"Search results for '{query}'", color=discord.Color.blue())
            for idx, series in enumerate(results, start=1):
                title = series.get("title", "Unknown Title")
                year = series.get("year", "N/A")
                embed.add_field(name=f"{idx}. {title} ({year})", value=series.get("overview", "No description available.")[:200] + "...", inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error searching for series: {e}")

    @sonarr.command(name='info')
    async def series_info(self, ctx, index: int):
        """Get detailed info about a previously searched series."""
        results = self.search_cache.get(ctx.author.id)
        if not results or index < 1 or index > len(results):
            await ctx.send("Invalid selection. Please run `!sonarr search` first and choose a valid number.")
            return

        series = results[index - 1]

        trailer_url = youtube_trailer(series['title'], series['year'])
        tvdb_url = f"https://thetvdb.com/series/{series.get('tvdbId', 'N/A')}"
        tvdb_url = f"https://thetvdb.com/?tab=series&id={series.get('tvdbId', 'N/A')}"


        fanart_image = next(
            (img for img in series.get('images', []) if img.get('coverType') == 'fanart'),
            None
        )

        embed = discord.Embed(title=f"{series['title']} ({series['year']})", url=tvdb_url, color=discord.Color.blue())
        embed.set_thumbnail(url=series['remotePoster'])
        
        embed.add_field(name='**Overview**', value=series['overview'], inline=False)
        embed.add_field(name='**Rating**', value=series['ratings']['value'], inline=True)
        embed.add_field(name='**Seasons**', value=series['statistics']['seasonCount'], inline=True)
        embed.add_field(name='**Status**', value=series['status'].capitalize(), inline=True)
        if series['seasonFolder'] == True:
            embed.add_field(name='**In Library**', value='Yes', inline=False)
        else:
            embed.add_field(name='**In Library**', value='No', inline=False)
        embed.add_field(name='**Genres**', value=', '.join(series['genres']), inline=False)
        embed.add_field(name='**Links**', value=f"[Trailer]({trailer_url}) / [TVDb]({tvdb_url})", inline=False)
        if fanart_image:
            embed.set_image(url=fanart_image['remoteUrl'])

        await ctx.send(embed=embed)

    @sonarr.command(name='download')
    async def download_series(self, ctx, index: int, *, profile_name: str = "HD WebDL"):
        """Download a series from the cached search results using a quality profile."""
        results = self.search_cache.get(ctx.author.id)
        if not results or index < 1 or index > len(results):
            await ctx.send("Invalid selection. Please run `!sonarr search` first and choose a valid number.")
            return

        series = results[index - 1]

        try:
            profiles = self.sonarr.get_profiles()
            profile = next((p for p in profiles if p["name"].lower() == profile_name.lower()), None)
            if not profile:
                await ctx.send(f"Profile '{profile_name}' not found. Available profiles: {', '.join(p['name'] for p in profiles)}")
                return

            if profile_name.lower() == "kids":
                folder_path = "/media/Kids/Shows/"
            elif profile_name.lower() == "anime":
                folder_path = "/media/Anime/Shows/"
            else:
                folder_path = "/media/Shows/"

            series_payload = {
                "title": series["title"],
                "qualityProfileId": profile["id"],
                "tvdbId": series["tvdbId"],
                "year": series["year"],
                "rootFolderPath": folder_path,
                "monitored": True,
                "seasonFolder": True,
                "addOptions": {
                    "searchForMissingEpisodes": True
                }
            }

            added = self.sonarr.add_series(series_payload)
            await ctx.send(f"✅ Series '{series['title']}' added to Sonarr with profile '{profile_name}'.")

        except Exception as e:
            await ctx.send(f"Error adding series: {e}")

async def setup(bot):
    await bot.add_cog(SonarrCog(bot))
