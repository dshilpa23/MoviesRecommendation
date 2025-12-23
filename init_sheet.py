"""
Initialize master spreadsheet and migrate existing data
Creates movies_master.xlsx with proper schema and imports from existing JSON files
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from config import (
    MASTER_SHEET_PATH, DATA_DIR, SHEET_COLUMNS,
    STATUS_PUBLISHED, BUCKET_BEST, BUCKET_NEW, BUCKET_UPCOMING,
    PLACEHOLDER_RATING, PLACEHOLDER_GENRES, PLACEHOLDER_OTT_LIST
)
from utils import (
    generate_movie_key, generate_movie_id, normalize_language,
    extract_year_from_date, parse_genres, parse_ott_list
)


def create_empty_sheet() -> pd.DataFrame:
    """Create empty DataFrame with proper column schema"""
    df = pd.DataFrame(columns=list(SHEET_COLUMNS.keys()))
    
    # Set proper dtypes
    for col, dtype in SHEET_COLUMNS.items():
        if dtype == bool:
            df[col] = df[col].astype('boolean')
        elif dtype == int:
            df[col] = df[col].astype('Int64')  # Nullable integer
        elif dtype == float:
            df[col] = df[col].astype('Float64')  # Nullable float
    
    return df


def migrate_movie_from_json(movie_json: Dict) -> Dict:
    """
    Convert JSON movie object to sheet row format
    Applies normalization and generates IDs
    """
    title = movie_json.get('title', '')
    release_date = movie_json.get('releaseDate', '')
    language_raw = movie_json.get('language', '')
    region = movie_json.get('region', '')
    
    # Normalize language
    language = normalize_language(language_raw)
    
    # Generate IDs
    movie_key = generate_movie_key(title, release_date, language, region)
    movie_id = generate_movie_id(
        imdb_id=movie_json.get('imdbId'),
        tmdb_id=movie_json.get('tmdbId'),
        movie_key=movie_key
    )
    
    # Parse genres and OTT
    genres = parse_genres(movie_json.get('genres') or movie_json.get('genre', []))
    ott_list = parse_ott_list(movie_json.get('ottList', []))
    primary_ott = movie_json.get('ott', 'all')
    
    # Extract year
    release_year = extract_year_from_date(release_date) or 0
    
    # Build row
    row = {
        # Identity
        'movieId': movie_id,
        'movieKey': movie_key,
        'normalizedTitle': movie_key.split('_')[0] if '_' in movie_key else title.lower(),
        
        # Core fields
        'title': title,
        'sourceUrl': movie_json.get('sourceUrl', ''),
        'posterUrl': movie_json.get('posterUrl', ''),
        'releaseDate': release_date,
        'releaseYear': release_year,
        'language': language,  # Normalized/capitalized
        'region': region,
        'description': movie_json.get('description', ''),
        'genres': json.dumps(genres) if genres else '',
        
        # External IDs
        'imdbId': movie_json.get('imdbId', ''),
        'tmdbId': movie_json.get('tmdbId', ''),
        
        # Editorial (preserve from JSON if exists)
        'rating': movie_json.get('rating') if movie_json.get('rating') else None,
        'ottList': json.dumps(ott_list) if ott_list else '',
        'primaryOtt': primary_ott if primary_ott != 'all' else '',
        'watchUrl': movie_json.get('watchUrl', ''),
        'youtubeId': movie_json.get('youtubeId', ''),
        'audience': movie_json.get('audience', ''),
        'editorNotes': '',
        'confidence': 'medium',  # Default
        'bucket': movie_json.get('_bucket', BUCKET_BEST),  # Infer from source
        
        # Workflow
        'status': STATUS_PUBLISHED,  # Existing data is published
        'descriptionLock': False,
        'posterLock': False,
        'ottLock': False,
        'scrapedAt': datetime.now().isoformat(),
        'lastUpdatedAt': datetime.now().isoformat(),
        'lastReviewedAt': '',
        'forceRefresh': False,
    }
    
    return row


def migrate_from_json_files():
    """
    Migrate existing JSON files to master sheet
    Imports from: best-india.json, ott-releases.json, upcoming-ott.json
    """
    print("🚀 Initializing master spreadsheet...")
    
    # Create empty sheet
    df = create_empty_sheet()
    
    # Files to import
    import_files = [
        ('best-india.json', BUCKET_BEST),
        ('ott-releases.json', BUCKET_NEW),
        ('upcoming-ott.json', BUCKET_UPCOMING),
    ]
    
    all_rows = []
    stats = {
        'total': 0,
        'by_file': {},
        'by_language': {},
        'duplicates': 0,
    }
    
    existing_keys = set()
    
    for filename, bucket in import_files:
        filepath = DATA_DIR / filename
        
        if not filepath.exists():
            print(f"⚠️  File not found: {filename}")
            continue
        
        print(f"📂 Importing from {filename}...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            file_count = 0
            file_dupes = 0
            
            for movie in movies:
                # Set bucket from filename
                movie['_bucket'] = bucket
                
                # Convert to row
                row = migrate_movie_from_json(movie)
                
                # Check for duplicates
                if row['movieKey'] in existing_keys:
                    file_dupes += 1
                    stats['duplicates'] += 1
                    print(f"  ⚠️  Duplicate: {row['title']} (key: {row['movieKey']})")
                    continue
                
                existing_keys.add(row['movieKey'])
                all_rows.append(row)
                file_count += 1
                
                # Track language stats
                lang = row['language']
                stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1
            
            stats['by_file'][filename] = file_count
            stats['total'] += file_count
            print(f"  ✅ Imported {file_count} movies ({file_dupes} duplicates skipped)")
            
        except Exception as e:
            print(f"  ❌ Error importing {filename}: {e}")
    
    # Create DataFrame
    if all_rows:
        df = pd.DataFrame(all_rows)
        
        # Save to Excel
        print(f"\n💾 Saving to {MASTER_SHEET_PATH}...")
        df.to_excel(MASTER_SHEET_PATH, index=False, engine='openpyxl')
        print(f"✅ Master spreadsheet created!")
        
        # Print stats
        print(f"\n📊 Migration Statistics:")
        print(f"   Total movies: {stats['total']}")
        print(f"   Duplicates skipped: {stats['duplicates']}")
        print(f"\n   By file:")
        for filename, count in stats['by_file'].items():
            print(f"     {filename}: {count}")
        print(f"\n   By language:")
        for lang, count in sorted(stats['by_language'].items(), key=lambda x: -x[1]):
            print(f"     {lang}: {count}")
    else:
        print("❌ No movies to import!")


if __name__ == '__main__':
    migrate_from_json_files()
