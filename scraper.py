"""
Movie Scraper with Deduplication
Scrapes movies only once, respects existing data and editorial locks

Data Source: StudioFlicks
- Endpoint: https://www.studioflicks.com/wp-admin/admin-ajax.php
- Movie pages: https://www.studioflicks.com/movie/{slug}/
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import requests
from bs4 import BeautifulSoup
import re
import time

from config import MASTER_SHEET_PATH, STATUS_REVIEW
from utils import generate_movie_key, generate_movie_id, normalize_language, extract_year_from_date


class MovieScraper:
    """
    Scraper that enforces scrape-once policy
    """
    
    def __init__(self, sheet_path=MASTER_SHEET_PATH):
        self.sheet_path = sheet_path
        self.df = None
        self.existing_keys = set()
        self.existing_movies = {}
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
    
    def should_scrape(self, source_url: str, preview_data: Optional[Dict] = None) -> Tuple[bool, str, str]:
        """
        Check if URL should be scraped
        
        Args:
            source_url: URL to potentially scrape
            preview_data: Optional preview data (title, year, language) to generate key
        
        Returns:
            (should_scrape, movie_key, reason)
        """
        if not preview_data:
            return (True, '', 'No preview data, must scrape to check')
        
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
    
    def scrape_movie(self, source_url: str) -> Dict:
        """
        Scrape movie data from StudioFlicks movie page
        """
        print(f"🕷️  Scraping: {source_url}")
        
        try:
            # Fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(source_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_elem = soup.select_one('h1.entry-title, h1.movie-title, .movie-header h1')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract poster
            poster_elem = soup.select_one('.movie-poster img, .wp-post-image, article img')
            poster_url = poster_elem.get('src', '') if poster_elem else ''
            
            # Extract release date
            release_date = ''
            date_elem = soup.select_one('.release-date, .movie-meta .date, time')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # Try to parse date formats
                match = re.search(r'(\d{4})', date_text)
                if match:
                    release_date = f"{match.group(1)}-01-01"
            
            # Extract language
            language = 'Hindi'  # Default
            lang_elem = soup.select_one('.language, .movie-meta .lang')
            if lang_elem:
                lang_text = lang_elem.get_text(strip=True)
                if any(l in lang_text.lower() for l in ['telugu', 'tamil', 'malayalam', 'hindi']):
                    language = lang_text
            
            # Extract description
            desc_elem = soup.select_one('.movie-description, .entry-content p, article p')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract genres
            genres = []
            genre_elems = soup.select('.genre, .movie-genre, .post-categories a')
            for g in genre_elems:
                genre = g.get_text(strip=True)
                if genre:
                    genres.append(genre)
            
            scraped_data = {
                'title': title,
                'sourceUrl': source_url,
                'posterUrl': poster_url,
                'releaseDate': release_date,
                'language': language,
                'region': '',
                'description': description[:500] if description else '',  # Limit length
                'genres': genres,
                'imdbId': '',
                'tmdbId': '',
            }
            
            time.sleep(1)  # Rate limiting
            return scraped_data
            
        except Exception as e:
            print(f"  ❌ Error scraping {source_url}: {e}")
            raise
    
    def merge_with_existing(self, existing: Dict, scraped: Dict) -> Dict:
        """
        Merge scraped data with existing, respecting locks
        
        Rules:
        - Editorial fields: NEVER overwrite
        - Locked fields: Check lock flags
        - Empty fields: Update from scrape
        """
        merged = existing.copy()
        
        # Editorial fields - always preserve
        editorial_fields = [
            'rating', 'ottList', 'primaryOtt', 'watchUrl', 
            'youtubeId', 'audience', 'editorNotes', 'confidence', 'bucket'
        ]
        
        # Locked field checks
        if existing.get('descriptionLock') == True:
            # Don't update description
            pass
        elif not existing.get('description'):
            merged['description'] = scraped.get('description', '')
        
        if existing.get('posterLock') == True:
            # Don't update poster
            pass
        elif not existing.get('posterUrl'):
            merged['posterUrl'] = scraped.get('posterUrl', '')
        
        if existing.get('ottLock') == True:
            # Don't update OTT
            pass
        
        # Update other scraped fields if empty
        scraped_fields = ['title', 'releaseDate', 'language', 'genres', 'imdbId', 'tmdbId']
        for field in scraped_fields:
            if not existing.get(field) and scraped.get(field):
                merged[field] = scraped[field]
        
        # Update metadata
        merged['lastUpdatedAt'] = datetime.now().isoformat()
        if existing.get('forceRefresh'):
            merged['forceRefresh'] = False  # Reset flag
        
        return merged
    
    def add_new_movie(self, scraped: Dict) -> Dict:
        """
        Convert scraped data to sheet row format
        """
        title = scraped.get('title', '')
        release_date = scraped.get('releaseDate', '')
        language_raw = scraped.get('language', '')
        region = scraped.get('region', '')
        
        # Normalize
        language = normalize_language(language_raw)
        
        # Generate IDs
        movie_key = generate_movie_key(title, release_date, language, region)
        movie_id = generate_movie_id(
            imdb_id=scraped.get('imdbId'),
            tmdb_id=scraped.get('tmdbId'),
            movie_key=movie_key
        )
        
        # Build row
        import json
        row = {
            'movieId': movie_id,
            'movieKey': movie_key,
            'normalizedTitle': movie_key.split('_')[0] if '_' in movie_key else title.lower(),
            'title': title,
            'sourceUrl': scraped.get('sourceUrl', ''),
            'posterUrl': scraped.get('posterUrl', ''),
            'releaseDate': release_date,
            'releaseYear': extract_year_from_date(release_date) or 0,
            'language': language,
            'region': region,
            'description': scraped.get('description', ''),
            'genres': json.dumps(scraped.get('genres', [])),
            'imdbId': scraped.get('imdbId', ''),
            'tmdbId': scraped.get('tmdbId', ''),
            'rating': None,
            'ottList': '',
            'primaryOtt': '',
            'watchUrl': '',
            'youtubeId': '',
            'audience': '',
            'editorNotes': '',
            'confidence': 'needs_review',  # New movies need review
            'bucket': 'new',  # Default bucket
            'status': STATUS_REVIEW,  # Not published yet
            'descriptionLock': False,
            'posterLock': False,
            'ottLock': False,
            'scrapedAt': datetime.now().isoformat(),
            'lastUpdatedAt': datetime.now().isoformat(),
            'lastReviewedAt': '',
            'forceRefresh': False,
        }
        
        return row
    
    def scrape_urls(self, urls: List[str]):
        """
        Scrape list of URLs, skipping existing movies
        
        Returns:
            dict with scraped, skipped, and errors
        """
        results = {
            'scraped': [],
            'skipped': [],
            'errors': [],
            'updated': []
        }
        
        for url in urls:
            try:
                # Step 1: Quick check (you might extract preview from URL or do light scrape)
                # For now, we'll scrape and then check
                scraped = self.scrape_movie(url)
                
                # Generate key
                movie_key = generate_movie_key(
                    scraped['title'],
                    scraped['releaseDate'],
                    scraped['language'],
                    scraped.get('region', '')
                )
                
                # Check if should scrape
                if movie_key in self.existing_keys:
                    existing = self.existing_movies[movie_key]
                    
                    if existing.get('forceRefresh') == True:
                        # Merge and update
                        merged = self.merge_with_existing(existing, scraped)
                        results['updated'].append(merged)
                        print(f"  🔄 Updated: {scraped['title']}")
                    else:
                        results['skipped'].append((url, movie_key, 'Already exists'))
                        print(f"  ⏭️  Skipped: {scraped['title']} (already in catalog)")
                else:
                    # New movie
                    row = self.add_new_movie(scraped)
                    results['scraped'].append(row)
                    print(f"  ✅ Scraped: {scraped['title']}")
                
            except Exception as e:
                results['errors'].append((url, str(e)))
                print(f"  ❌ Error scraping {url}: {e}")
        
        return results
    
    def save_to_sheet(self, results: Dict):
        """
        Save scraping results to sheet
        """
        if not results['scraped'] and not results['updated']:
            print("\n✨ No new or updated movies to save")
            return
        
        # Append new movies
        if results['scraped']:
            new_df = pd.DataFrame(results['scraped'])
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
        print(f"✅ Saved! {len(results['scraped'])} new, {len(results['updated'])} updated")


def main():
    """Scrape movies from StudioFlicks"""
    scraper = MovieScraper()
    
    # Example: Real StudioFlicks movie URLs to test with
    urls = [
        'https://www.studioflicks.com/movie/pushpa-2-the-rule/',
        'https://www.studioflicks.com/movie/game-changer/',
        # Add more URLs from StudioFlicks...
    ]
    
    print(f"\n🚀 Scraping {len(urls)} URLs from StudioFlicks...\n")
    results = scraper.scrape_urls(urls)
    
    # Save results
    scraper.save_to_sheet(results)
    
    # Print summary
    print(f"\n📊 Scraping Summary:")
    print(f"   New movies: {len(results['scraped'])}")
    print(f"   Updated movies: {len(results['updated'])}")
    print(f"   Skipped (existing): {len(results['skipped'])}")
    print(f"   Errors: {len(results['errors'])}")


if __name__ == '__main__':
    print("🚀 StudioFlicks Movie Scraper")
    print("   Endpoint: https://www.studioflicks.com/wp-admin/admin-ajax.php")
    print()
    main()
