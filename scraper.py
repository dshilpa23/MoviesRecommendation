"""
Movie Ingestion Pipeline with TMDB Discovery API
Discovers and fetches movies from TMDB, enforces scrape-once policy with deduplication

Data Source: The Movie Database (TMDB) API
- Discovery API: https://api.themoviedb.org/3/discover/movie
- Details API: https://api.themoviedb.org/3/movie/{id}
- Credits API: https://api.themoviedb.org/3/movie/{id}/credits
- Watch Providers API: https://api.themoviedb.org/3/movie/{id}/watch/providers
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import requests
import time
import json
from collections import deque

from config import (
    MASTER_SHEET_PATH, 
    STATUS_REVIEW,
    TMDB_API_KEY,
    TMDB_BASE_URL,
    TMDB_IMAGE_BASE_URL,
    TMDB_RATE_LIMIT
)
from utils import generate_movie_key, generate_movie_id, normalize_language, extract_year_from_date


class TMDBClient:
    """
    TMDB API client with rate limiting and error handling
    """
    
    def __init__(self, api_key: str = TMDB_API_KEY):
        if not api_key or api_key == "YOUR_TMDB_API_KEY_HERE":
            raise ValueError(
                "TMDB API key not configured. "
                "Get your API key from https://www.themoviedb.org/settings/api "
                "and set it in config.py"
            )
        
        self.api_key = api_key
        self.base_url = TMDB_BASE_URL
        self.image_base_url = TMDB_IMAGE_BASE_URL
        self.session = requests.Session()
        
        # Rate limiting: Track request timestamps
        self.request_times = deque(maxlen=TMDB_RATE_LIMIT)
    
    def _rate_limit(self):
        """Enforce rate limit: max 40 requests per 10 seconds"""
        now = time.time()
        
        # Remove requests older than 10 seconds
        while self.request_times and now - self.request_times[0] > 10:
            self.request_times.popleft()
        
        # If at limit, wait
        if len(self.request_times) >= TMDB_RATE_LIMIT:
            sleep_time = 10 - (now - self.request_times[0])
            if sleep_time > 0:
                print(f"  ⏳ Rate limit reached, waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"  ❌ API request failed: {e}")
            raise
    
    def get_movie_details(self, tmdb_id: str) -> Dict:
        """
        Fetch movie details from TMDB
        
        Args:
            tmdb_id: TMDB movie ID
        
        Returns:
            Movie data dictionary
        """
        endpoint = f"movie/{tmdb_id}"
        params = {
            'append_to_response': 'credits,external_ids,release_dates'
        }
        
        return self._make_request(endpoint, params)
    
    def search_movies(self, query: str, year: Optional[int] = None, language: str = 'en') -> List[Dict]:
        """
        Search for movies by title
        
        Args:
            query: Movie title to search
            year: Optional release year filter
            language: Search language (default: en)
        
        Returns:
            List of movie results
        """
        endpoint = "search/movie"
        params = {
            'query': query,
            'language': language,
            'include_adult': False
        }
        
        if year:
            params['year'] = year
        
        data = self._make_request(endpoint, params)
        return data.get('results', [])
    
    def discover_movies(self, 
                       region: str = 'IN',
                       language: str = 'hi',
                       release_date_gte: str = None,
                       release_date_lte: str = None,
                       page: int = 1) -> Dict:
        """
        Discover movies using TMDB discovery API
        
        Args:
            region: ISO 3166-1 code (e.g., 'IN' for India)
            language: ISO 639-1 code (e.g., 'hi' for Hindi, 'te' for Telugu)
            release_date_gte: Release date from (YYYY-MM-DD)
            release_date_lte: Release date to (YYYY-MM-DD)
            page: Page number (1-based)
        
        Returns:
            Discovery results with movies list
        """
        endpoint = "discover/movie"
        params = {
            'region': region,
            'with_original_language': language,
            'sort_by': 'popularity.desc',
            'page': page,
            'include_adult': False
        }
        
        if release_date_gte:
            params['primary_release_date.gte'] = release_date_gte
        if release_date_lte:
            params['primary_release_date.lte'] = release_date_lte
        
        return self._make_request(endpoint, params)
    
    def get_movie_credits(self, tmdb_id: str) -> Dict:
        """Fetch movie credits (cast and crew)"""
        endpoint = f"movie/{tmdb_id}/credits"
        return self._make_request(endpoint)
    
    def get_watch_providers(self, tmdb_id: str) -> Dict:
        """Fetch OTT watch providers"""
        endpoint = f"movie/{tmdb_id}/watch/providers"
        return self._make_request(endpoint)
    
    def get_poster_url(self, poster_path: Optional[str]) -> str:
        """Get full poster URL from poster path"""
        if not poster_path:
            return ''
        return f"{self.image_base_url}{poster_path}"


# TMDB language code to canonical language name mapping
TMDB_LANGUAGE_MAP = {
    'hi': 'Hindi',
    'te': 'Telugu',
    'ta': 'Tamil',
    'ml': 'Malayalam',
    'en': 'English',
    'kn': 'Kannada',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'pa': 'Punjabi',
    'gu': 'Gujarati',
}


class MovieIngester:
    """
    Movie ingestion pipeline that enforces scrape-once policy
    Fetches movies from TMDB API and manages Excel sheet
    """
    
    def __init__(self, sheet_path=MASTER_SHEET_PATH, api_key: str = TMDB_API_KEY):
        self.sheet_path = sheet_path
        self.df = None
        self.existing_keys = set()
        self.existing_movies = {}
        self.tmdb_client = TMDBClient(api_key)
        self.load_existing()
    
    def load_existing(self):
        """Load existing movies from sheet"""
        try:
            self.df = pd.read_excel(self.sheet_path, engine='openpyxl')
            print(f"📂 Loaded {len(self.df)} existing movies from sheet")
            
            # Build lookup
            for _, row in self.df.iterrows():
                movie_key = row.get('movieKey')
                if pd.notna(movie_key):
                    self.existing_keys.add(movie_key)
                    self.existing_movies[movie_key] = row.to_dict()
            
            print(f"   {len(self.existing_keys)} unique movie keys indexed")
            
        except FileNotFoundError:
            print(f"⚠️  Sheet not found: {self.sheet_path}")
            print(f"   Run init_sheet.py first to create master spreadsheet")
            self.df = None
    
    def should_fetch(self, tmdb_id: str, preview_data: Optional[Dict] = None) -> Tuple[bool, str, str]:
        """
        Check if movie should be fetched from TMDB
        
        Args:
            tmdb_id: TMDB movie ID
            preview_data: Optional preview data (title, year, language) to generate key
        
        Returns:
            (should_fetch, movie_key, reason)
        """
        if not preview_data:
            return (True, '', 'No preview data, must fetch to check')
        
        # Generate key from preview
        title = preview_data.get('title', '')
        release_date = preview_data.get('releaseDate', '')
        language = preview_data.get('language', '')
        region = preview_data.get('region', '')
        
        movie_key = generate_movie_key(title, release_date, language, region)
        
        # Check if exists
        if movie_key not in self.existing_keys:
            return (True, movie_key, 'New movie, not in catalog')
        
        # Exists - check forceRefresh flag
        existing = self.existing_movies.get(movie_key)
        if existing and existing.get('forceRefresh') == True:
            return (True, movie_key, 'Force refresh enabled')
        
        return (False, movie_key, 'Already exists, forceRefresh not set')
    
    def _map_language_from_iso(self, iso_code: str) -> str:
        """Map TMDB ISO language code to our canonical language names"""
        language_map = {
            'hi': 'Hindi',
            'te': 'Telugu',
            'ta': 'Tamil',
            'ml': 'Malayalam',
            'en': 'English',
            'kn': 'Kannada',
            'bn': 'Bengali',
            'mr': 'Marathi',
            'pa': 'Punjabi',
            'gu': 'Gujarati',
        }
        return language_map.get(iso_code.lower(), 'Hindi')  # Default to Hindi
    
    def fetch_movie_from_tmdb(self, tmdb_id: str, language_override: Optional[str] = None) -> Dict:
        """
        Fetch complete movie data from TMDB
        
        Args:
            tmdb_id: TMDB movie ID
            language_override: Override the detected language (e.g., 'Hindi')
        
        Returns:
            Movie data dictionary with required fields only
        """
        print(f"🎬 Fetching TMDB ID: {tmdb_id}")
        
        try:
            # Fetch details
            details = self.tmdb_client.get_movie_details(tmdb_id)
            
            # Fetch credits for actors
            credits = self.tmdb_client.get_movie_credits(tmdb_id)
            cast = credits.get('cast', [])
            top_actors = [actor['name'] for actor in cast[:3]]
            
            # Fetch watch providers
            providers_data = self.tmdb_client.get_watch_providers(tmdb_id)
            india_providers = providers_data.get('results', {}).get('IN', {})
            
            # Extract OTT platforms
            ott_list = []
            for provider_type in ['flatrate', 'rent', 'buy']:
                providers = india_providers.get(provider_type, [])
                for p in providers:
                    provider_name = p.get('provider_name', '')
                    if provider_name and provider_name not in ott_list:
                        ott_list.append(provider_name)
            
            # Extract fields
            title = details.get('title', '')
            original_language = details.get('original_language', '')
            language = language_override or TMDB_LANGUAGE_MAP.get(original_language, 'Unknown')
            release_date = details.get('release_date', '')
            rating = details.get('vote_average')
            poster_path = details.get('poster_path', '')
            
            # Format rating
            if rating is not None:
                rating = round(rating, 1)
            else:
                rating = "NA"
            
            # Format OTT list
            if not ott_list:
                ott_list = "NA"
            
            movie_data = {
                'title': title,
                'tmdbId': str(tmdb_id),
                'language': language,
                'actors': top_actors,
                'rating': rating,
                'releaseDate': release_date,
                'ottList': ott_list,
                'posterPath': self.tmdb_client.get_poster_url(poster_path) if poster_path else ''
            }
            
            print(f"  ✅ {title} ({language}) - Rating: {rating}")
            return movie_data
            
        except Exception as e:
            print(f"  ❌ Error fetching TMDB ID {tmdb_id}: {e}")
            raise
    
    def merge_with_existing(self, existing: Dict, fetched: Dict) -> Dict:
        """
        Merge fetched data with existing, respecting locks
        
        Rules:
        - Editorial fields: NEVER overwrite (rating, ottList, watchUrl, etc.)
        - Locked fields: Check lock flags
        - Empty fields: Update from fetch
        """
        merged = existing.copy()
        
        # Editorial fields - NEVER overwrite these
        editorial_fields = [
            'rating', 'ottList', 'primaryOtt', 'watchUrl', 
            'youtubeId', 'audience', 'editorNotes', 'confidence', 'bucket'
        ]
        
        # Only update non-editorial fields if not locked
        if existing.get('posterLock') != True and not existing.get('posterUrl'):
            merged['posterUrl'] = fetched.get('posterPath', '')
        
        # Update actors if empty
        if not existing.get('actors'):
            actors_list = fetched.get('actors', [])
            merged['actors'] = json.dumps(actors_list) if actors_list else ''
        
        # Update other fields if empty
        if not existing.get('tmdbId'):
            merged['tmdbId'] = fetched.get('tmdbId', '')
        
        if not existing.get('releaseDate'):
            merged['releaseDate'] = fetched.get('releaseDate', '')
            merged['releaseYear'] = extract_year_from_date(fetched.get('releaseDate', '')) or 0
        
        # Update metadata
        merged['lastUpdatedAt'] = datetime.now().isoformat()
        if existing.get('forceRefresh'):
            merged['forceRefresh'] = False  # Reset flag
        
        return merged
    
    def add_new_movie(self, fetched: Dict) -> Dict:
        """
        Convert fetched data to sheet row format
        Only populates specified output columns
        """
        title = fetched.get('title', '')
        release_date = fetched.get('releaseDate', '')
        language = fetched.get('language', '')
        region = ''
        
        # Generate IDs
        movie_key = generate_movie_key(title, release_date, language, region)
        movie_id = generate_movie_id(
            tmdb_id=fetched.get('tmdbId'),
            movie_key=movie_key
        )
        
        # Extract actors
        actors_list = fetched.get('actors', [])
        actors_json = json.dumps(actors_list) if actors_list else ''
        
        # Extract OTT list
        ott_list = fetched.get('ottList', 'NA')
        if isinstance(ott_list, list):
            ott_list_json = json.dumps(ott_list)
        else:
            ott_list_json = ott_list
        
        # Extract rating
        rating_value = fetched.get('rating')
        if rating_value == "NA":
            rating_value = None
        
        # Build row - ONLY specified output columns
        row = {
            'movieId': movie_id,
            'movieKey': movie_key,
            'normalizedTitle': movie_key.split('_')[0] if '_' in movie_key else title.lower(),
            'title': title,
            'sourceUrl': f"https://www.themoviedb.org/movie/{fetched.get('tmdbId', '')}",
            'posterUrl': fetched.get('posterPath', ''),
            'releaseDate': release_date,
            'releaseYear': extract_year_from_date(release_date) or 0,
            'language': language,
            'region': region,
            'description': '',
            'genres': '',
            'imdbId': '',
            'tmdbId': fetched.get('tmdbId', ''),
            'rating': rating_value,
            'ottList': ott_list_json,
            'primaryOtt': '',
            'watchUrl': '',
            'youtubeId': '',
            'audience': '',
            'editorNotes': '',
            'actors': actors_json,
            'confidence': 'needs_review',
            'bucket': 'new',
            'status': STATUS_REVIEW,
            'descriptionLock': False,
            'posterLock': False,
            'ottLock': False,
            'scrapedAt': datetime.now().isoformat(),
            'lastUpdatedAt': datetime.now().isoformat(),
            'lastReviewedAt': '',
            'forceRefresh': False,
        }
        
        return row
    
    def ingest_movies(self, movie_specs: List[Dict]):
        """
        Ingest list of movies from TMDB, skipping existing movies
        
        Args:
            movie_specs: List of dicts with 'tmdb_id' and optional 'language'
                Example: [
                    {'tmdb_id': '569094', 'language': 'Telugu'},
                    {'tmdb_id': '634649', 'language': 'Hindi'}
                ]
        
        Returns:
            dict with fetched, skipped, and errors
        """
        results = {
            'fetched': [],
            'skipped': [],
            'errors': [],
            'updated': []
        }
        
        for spec in movie_specs:
            tmdb_id = spec.get('tmdb_id')
            language = spec.get('language')
            
            if not tmdb_id:
                results['errors'].append((spec, 'Missing tmdb_id'))
                continue
            
            try:
                # Fetch from TMDB
                fetched = self.fetch_movie_from_tmdb(tmdb_id, language)
                
                # Generate key
                movie_key = generate_movie_key(
                    fetched['title'],
                    fetched['releaseDate'],
                    fetched['language'],
                    fetched.get('region', '')
                )
                
                # Check if should fetch
                if movie_key in self.existing_keys:
                    existing = self.existing_movies[movie_key]
                    
                    if existing.get('forceRefresh') == True:
                        # Merge and update
                        merged = self.merge_with_existing(existing, fetched)
                        results['updated'].append(merged)
                        print(f"  🔄 Updated: {fetched['title']}")
                    else:
                        results['skipped'].append((tmdb_id, movie_key, 'Already exists'))
                        print(f"  ⏭️  Skipped: {fetched['title']} (already in catalog)")
                else:
                    # New movie
                    row = self.add_new_movie(fetched)
                    results['fetched'].append(row)
                    print(f"  ✅ Fetched: {fetched['title']}")
                
            except Exception as e:
                results['errors'].append((tmdb_id, str(e)))
                print(f"  ❌ Error fetching {tmdb_id}: {e}")
        
        return results
    
    def ingest_from_tmdb_discover(self, config: Dict) -> Dict:
        """
        Ingest movies from TMDB discovery API
        
        Args:
            config: Discovery configuration with:
                - region: ISO 3166-1 code (e.g., 'IN')
                - languages: List of ISO 639-1 codes (e.g., ['hi', 'te', 'ta'])
                - release_date_gte: Release date from (YYYY-MM-DD)
                - release_date_lte: Release date to (YYYY-MM-DD)
                - pages: Number of pages to fetch per language (default: 1)
        
        Returns:
            dict with fetched, skipped, updated, and errors
        """
        region = config.get('region', 'IN')
        languages = config.get('languages', ['hi'])
        release_date_gte = config.get('release_date_gte')
        release_date_lte = config.get('release_date_lte')
        pages = config.get('pages', 1)
        
        print(f"\n🌍 Discovering movies from TMDB...")
        print(f"   Region: {region}")
        print(f"   Languages: {languages}")
        print(f"   Date range: {release_date_gte} to {release_date_lte}")
        print(f"   Pages per language: {pages}\n")
        
        # Collect all discovered movies
        discovered_movies = []
        
        for language in languages:
            language_name = TMDB_LANGUAGE_MAP.get(language, language.upper())
            print(f"\n🔍 Discovering {language_name} movies...")
            
            for page in range(1, pages + 1):
                try:
                    print(f"  📄 Fetching page {page}...")
                    discovery_result = self.tmdb_client.discover_movies(
                        region=region,
                        language=language,
                        release_date_gte=release_date_gte,
                        release_date_lte=release_date_lte,
                        page=page
                    )
                    
                    movies = discovery_result.get('results', [])
                    print(f"     Found {len(movies)} movies")
                    
                    for movie in movies:
                        tmdb_id = movie.get('id')
                        if tmdb_id:
                            discovered_movies.append({
                                'tmdb_id': str(tmdb_id),
                                'language': language_name
                            })
                    
                except Exception as e:
                    print(f"  ❌ Error discovering page {page}: {e}")
        
        print(f"\n📊 Total discovered: {len(discovered_movies)} movies")
        print(f"🎬 Fetching detailed data...\n")
        
        # Ingest all discovered movies
        results = self.ingest_movies(discovered_movies)
        
        return results
    
    def save_to_sheet(self, results: Dict):
        """
        Save ingestion results to sheet
        """
        if not results['fetched'] and not results['updated']:
            print("\n✨ No new or updated movies to save")
            return
        
        # Append new movies
        if results['fetched']:
            new_df = pd.DataFrame(results['fetched'])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
        
        # Update existing movies
        if results['updated']:
            for updated in results['updated']:
                movie_key = updated['movieKey']
                mask = self.df['movieKey'] == movie_key
                for col, value in updated.items():
                    self.df.loc[mask, col] = value
        
        # Save
        print(f"\n💾 Saving to {self.sheet_path}...")
        self.df.to_excel(self.sheet_path, index=False, engine='openpyxl')
        print(f"✅ Saved! {len(results['fetched'])} new, {len(results['updated'])} updated")


def main():
    """Ingest movies from TMDB API"""
    ingester = MovieIngester()
    
    # Example: TMDB movie IDs with language overrides
    # Get TMDB IDs from https://www.themoviedb.org/
    movie_specs = [
        {'tmdb_id': '569094', 'language': 'Telugu'},  # Spider-Man: Across the Spider-Verse
        {'tmdb_id': '634649', 'language': 'Hindi'},   # Spider-Man: No Way Home
        # Add more TMDB IDs...
    ]
    
    print(f"\n🚀 Ingesting {len(movie_specs)} movies from TMDB...\n")
    results = ingester.ingest_movies(movie_specs)
    
    # Save results
    ingester.save_to_sheet(results)
    
    # Print summary
    print(f"\n📊 Ingestion Summary:")
    print(f"   New movies: {len(results['fetched'])}")
    print(f"   Updated movies: {len(results['updated'])}")
    print(f"   Skipped (existing): {len(results['skipped'])}")
    print(f"   Errors: {len(results['errors'])}")


if __name__ == '__main__':
    print("🎬 TMDB Movie Ingestion Pipeline")
    print("   API: https://api.themoviedb.org/3")
    print("   Get your API key: https://www.themoviedb.org/settings/api")
    print()
    main()
