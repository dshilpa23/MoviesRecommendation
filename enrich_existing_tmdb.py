#!/usr/bin/env python3
"""
Enrich existing published movies that have tmdbId but missing data.
This script fetches complete TMDB data for movies that were imported before full enrichment.
"""

import pandas as pd
import time
from scraper import TMDBClient
from config import MASTER_SHEET_PATH

# Allowed OTT platforms
ALLOWED_PLATFORMS = {'sonyliv', 'netflix', 'amazon', 'sunnxt', 'hotstar', 'hulu', 'zee', 'jiohotstar', 'zee5'}

def normalize_platform(platform_str):
    """Normalize platform string to check against allowed list."""
    if not platform_str:
        return None
    normalized = platform_str.lower().strip()
    
    # Map all amazon variants to "amazon"
    if 'amazon' in normalized or 'prime' in normalized:
        return 'amazon'
    
    # Check other platforms
    for allowed in ALLOWED_PLATFORMS:
        if allowed in normalized:
            return allowed
    
    return None

def clean_ott_list(ott_list):
    """
    Clean OTT list by:
    1. Removing duplicates
    2. Keeping only allowed platforms
    3. Consolidating Amazon variants into single "Amazon Prime Video"
    """
    if not ott_list:
        return []
    
    # Handle string representation of list
    if isinstance(ott_list, str):
        try:
            # Try to parse string representation of list
            if ott_list.startswith('['):
                ott_list = eval(ott_list)
            else:
                ott_list = [ott_list]
        except:
            ott_list = [ott_list]
    
    if not isinstance(ott_list, list):
        ott_list = [ott_list]
    
    seen = set()
    cleaned = []
    amazon_found = False
    
    for ott in ott_list:
        if not ott:
            continue
        normalized = normalize_platform(ott)
        
        if normalized == 'amazon':
            if not amazon_found:
                cleaned.append('Amazon Prime Video')
                amazon_found = True
        elif normalized and normalized not in seen:
            cleaned.append(ott)
            seen.add(normalized)
    
    return cleaned

def enrich_existing_movies():
    """Enrich published movies that have tmdbId but missing actors/ottList."""
    
    # Initialize clients
    tmdb_client = TMDBClient()
    
    # Read the sheet directly
    df = pd.read_excel(MASTER_SHEET_PATH)
    
    # Find movies that need enrichment:
    # - Have tmdbId
    # - Missing actors or ottList
    # - Status is published
    needs_enrichment = df[
        (df['tmdbId'].notna()) & 
        (
            (df['actors'].isna()) |  # Missing actors
            (df['ottList'].isna()) |  # Missing OTT
            (df['actors'] == 'nan') |
            (df['ottList'] == 'nan')
        ) &
        (df['status'] == 'published')
    ].copy()
    
    print(f"Found {len(needs_enrichment)} published movies that need enrichment")
    
    if len(needs_enrichment) == 0:
        print("No movies need enrichment!")
        return
    
    # Show first few
    print("\nMovies to enrich:")
    for idx, row in needs_enrichment.head(10).iterrows():
        print(f"  - {row['title']} (tmdbId: {int(row['tmdbId'])})")
    
    if len(needs_enrichment) > 10:
        print(f"  ... and {len(needs_enrichment) - 10} more")
    
    # Ask for confirmation
    response = input(f"\nEnrich all {len(needs_enrichment)} movies? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        return
    
    # Enrich each movie
    enriched_count = 0
    failed_count = 0
    
    for idx, row in needs_enrichment.iterrows():
        tmdb_id = int(row['tmdbId'])
        title = row['title']
        
        try:
            print(f"\nEnriching: {title} (tmdbId: {tmdb_id})")
            
            # Fetch complete data from TMDB
            movie_details = tmdb_client.get_movie_details(tmdb_id)
            if not movie_details:
                print(f"  ❌ Failed to fetch details for {title}")
                failed_count += 1
                continue
            
            # Get credits (actors)
            credits = tmdb_client.get_movie_credits(tmdb_id)
            actors = []
            if credits and 'cast' in credits:
                actors = [actor['name'] for actor in credits['cast'][:3]]
            
            # Get watch providers (OTT)
            watch_providers = tmdb_client.get_watch_providers(tmdb_id)
            ott_platforms = []
            if watch_providers and 'results' in watch_providers:
                india_data = watch_providers['results'].get('IN', {})
                for provider_type in ['flatrate', 'free', 'ads']:
                    if provider_type in india_data:
                        ott_platforms.extend([p['provider_name'] for p in india_data[provider_type]])
            
            # Clean OTT list: keep only allowed platforms and consolidate amazon variants
            ott_platforms = clean_ott_list(ott_platforms)
            
            # Update the row
            df.at[idx, 'actors'] = str(actors) if actors else '[]'
            df.at[idx, 'ottList'] = str(ott_platforms) if ott_platforms else '[]'
            df.at[idx, 'releaseDate'] = movie_details.get('release_date', row['releaseDate'])
            df.at[idx, 'rating'] = movie_details.get('vote_average', row.get('rating', ''))
            
            print(f"  ✅ Enriched: actors={actors}, ottList={ott_platforms}, releaseDate={movie_details.get('release_date')}, rating={movie_details.get('vote_average')}")
            
            enriched_count += 1
            
            # Small delay to respect rate limits
            time.sleep(0.3)
            
        except Exception as e:
            print(f"  ❌ Error enriching {title}: {e}")
            failed_count += 1
    
    # Save back to Excel
    print(f"\n{'='*60}")
    print(f"Enrichment complete!")
    print(f"  ✅ Enriched: {enriched_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"\nSaving to {MASTER_SHEET_PATH}...")
    
    df.to_excel(MASTER_SHEET_PATH, index=False)
    print("✅ Saved!")
    print("\nNow run generate_json.py to export the enriched data.")

if __name__ == '__main__':
    enrich_existing_movies()
