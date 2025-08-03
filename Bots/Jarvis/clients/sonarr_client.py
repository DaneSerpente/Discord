# clients/sonarr_client.py

import requests

class SonarrClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {'X-Api-Key': api_key}

    def search_series(self, query):
        """Search for a TV series by title."""
        endpoint = f"{self.base_url}/api/v3/series/lookup"
        params = {'term': query}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def add_series(self, series_data):
        """Add a TV series to Sonarr."""
        endpoint = f"{self.base_url}/api/v3/series"
        response = requests.post(endpoint, headers=self.headers, json=series_data)
        response.raise_for_status()
        return response.json()

    def get_profiles(self):
        """Fetch available quality profiles."""
        endpoint = f"{self.base_url}/api/v3/qualityProfile"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
