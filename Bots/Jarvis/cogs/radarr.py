
# cogs/radarr.py

import discord
from discord.ext import commands
from clients.radarr_client import RadarrClient
from utils.media_tools import youtube_trailer
import os

class RadarrCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.radarr = RadarrClient(
            base_url=os.getenv("RADARR_URL"),
            api_key=os.getenv("RADARR_API_KEY")
        )
        self.search_cache = {}  # Store search results per user

    @commands.group()
    async def radarr(self, ctx):
        """Radarr command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Available subcommands: `search`, `info`, `download`")

    @radarr.command(name='search')
    async def search_movie(self, ctx, *, query: str):
        """Search for a movie in Radarr."""
        try:
            results = self.radarr.search_movie(query)
            if not results:
                await ctx.send(f"No results found for '{query}'.")
                return

            self.search_cache[ctx.author.id] = results  # Cache results per user

            embed = discord.Embed(title=f"Search results for '{query}'", color=discord.Color.yellow())
            for idx, movie in enumerate(results, start=1):
                title = movie.get("title", "Unknown Title")
                year = movie.get("year", "N/A")
                embed.add_field(name=f"{idx}. {title} ({year})", value=movie.get("overview", "No description available.")[:200] + "...", inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error searching for movie: {e}")
 
    @radarr.command(name='info')
    async def movie_info(self, ctx, index: int):
        """Get detailed info about a previously searched movie."""
        results = self.search_cache.get(ctx.author.id)
        if not results or index < 1 or index > len(results):
            await ctx.send("Invalid selection. Please run `!radarr search` first and choose a valid number.")
            return

        movie = results[index - 1]

        # Get the YouTube trailer URL
        trailer_url = youtube_trailer(movie['title'], movie['year'])
        imdb_url = f"https://www.imdb.com/title/{movie.get('imdbId', 'N/A')}/"
        tmdb_url = f"https://www.themoviedb.org/movie/{movie.get('tmdbId', 'N/A')}"

        embed = discord.Embed(title=f"{movie['title']} ({movie['year']})", url=tmdb_url, color=discord.Color.yellow()) # Title and year
        embed.set_thumbnail(url=movie['remotePoster']) # Movie tumbnail poster
        embed.add_field(name='**Overview**', value=movie['overview'], inline=False) # Moview description

        # Add ratings if available
        if 'imdb' in movie['ratings']:
            embed.add_field(name='**IMDB Rating**', value=movie['ratings']['imdb']['value'], inline=True)
        if 'rottenTomatoes' in movie['ratings']:
            embed.add_field(name='**Rotten Rating**', value=str(movie['ratings']['rottenTomatoes']['value']) + '%', inline=True)
        
        # Add additional movie details
        embed.add_field(name='**Status**', value=movie['status'].capitalize(), inline=True)
        if movie.get('movieFile') and movie['movieFile'].get('relativePath'):
            embed.add_field(name='**In Library**', value=movie['movieFile']['relativePath'], inline=False)
        elif movie['monitored'] == True:
            embed.add_field(name='**In Library**', value='Monitored', inline=False)
        embed.add_field(name='**Genres**', value=', '.join(movie['genres']), inline=False)
        embed.add_field(name='**Links**', value=f"[Trailer]({trailer_url}) / [IMBd]({imdb_url}) / [TMDb]({tmdb_url})", inline=False)
        if len(movie['images']) != 1:
            embed.set_image(url=movie['images'][1]['remoteUrl'])

        await ctx.send(embed=embed)

    @radarr.command(name='download')
    async def download_movie(self, ctx, index: int, *, profile_name: str = "HD"):
        """Download a movie from the cached search results using a quality profile."""
        results = self.search_cache.get(ctx.author.id)
        if not results or index < 1 or index > len(results):
         await ctx.send("Invalid selection. Please run `!radarr search` first and choose a valid number.")
         return

        movie = results[index - 1]

        try:
            # Get all profiles from Radarr
            profiles = self.radarr.get_profiles()
            profile = next((p for p in profiles if p["name"].lower() == profile_name.lower()), None)
            if not profile:
                await ctx.send(f"Profile '{profile_name}' not found. Available profiles: {', '.join(p['name'] for p in profiles)}")
                return
            
            # Determine the folder path based on the profile name
            if profile_name.lower() == "kids":
                folder_path = "/media/Kids/Movies/"
            elif profile_name.lower() == "anime":
                folder_path = "/media/Anime/Movies/"
            else:
                folder_path = "/media/Movies/"

            # Prepare the movie payload for Radarr
            movie_payload = {
                "title": movie["title"],
                "qualityProfileId": profile["id"],
                "tmdbId": movie["tmdbId"],
                "year": movie["year"],
                "rootFolderPath": folder_path,
                "monitored": True,
                "addOptions": {
                    "searchForMovie": True
                }
            }

            # Add the movie to Radarr
            added = self.radarr.add_movie(movie_payload)
            await ctx.send(f"✅ Movie '{movie['title']}' added to Radarr with profile '{profile_name}'.")

        except Exception as e:
            await ctx.send(f"Error adding movie: {e}")

async def setup(bot):
    await bot.add_cog(RadarrCog(bot))

