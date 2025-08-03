# clients/radarr_client.py

import requests

class RadarrClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {'X-Api-Key': api_key}

    def search_movie(self, query):
        """Search for a movie by title."""
        endpoint = f"{self.base_url}/api/v3/movie/lookup"
        params = {'term': query}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def add_movie(self, movie_data):
        """Add a movie to Radarr."""
        endpoint = f"{self.base_url}/api/v3/movie"
        response = requests.post(endpoint, headers=self.headers, json=movie_data)
        response.raise_for_status()
        return response.json()

    def get_profiles(self):
        """Fetch available quality profiles."""
        endpoint = f"{self.base_url}/api/v3/qualityProfile"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
