"""
Bulk TMDB Ingestion - Last 5 Years
Fetches all Indian movies from 2020-2025 for Hindi, Telugu, Tamil, Malayalam
"""

from scraper import MovieIngester
from datetime import datetime

def main():
    """Ingest movies from last 5 years"""
    ingester = MovieIngester()
    
    # Configuration: Last 5 years (2020-2025) for Indian languages
    config = {
        'region': 'IN',
        # 'languages': ['hi', 'te', 'ta', 'ml'],  # Hindi, Telugu, Tamil, Malayalam
        'languages': ['ml'],
        'release_date_gte': '2025-01-01',
        'release_date_lte': '2026-01-31',
        'pages': 50  # Fetch 50 pages per language (1000 movies per language)
    }
    
    print("="*80)
    print("TMDB BULK INGESTION - LAST 5 YEARS")
    print("="*80)
    print(f"\n📅 Date Range: {config['release_date_gte']} to {config['release_date_lte']}")
    print(f"🌍 Region: {config['region']}")
    print(f"🗣️  Languages: Hindi, Telugu, Tamil, Malayalam")
    print(f"📄 Pages per language: {config['pages']} (up to {config['pages']*20} movies per language)")
    print(f"\n⏱️  This will take approximately 30-60 minutes due to rate limiting...")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    import time
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return
    
    print("\n🚀 Starting ingestion...\n")
    
    # Process one language at a time with incremental saves
    all_results = {
        'fetched': [],
        'updated': [],
        'skipped': [],
        'errors': []
    }
    
    language_names = {'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'ml': 'Malayalam'}
    
    for i, language in enumerate(config['languages'], 1):
        lang_name = language_names.get(language, language.upper())
        print(f"\n{'='*80}")
        print(f"PROCESSING {lang_name.upper()} ({i}/{len(config['languages'])})")
        print(f"{'='*80}\n")
        
        # Create config for single language
        lang_config = {
            'region': config['region'],
            'languages': [language],
            'release_date_gte': config['release_date_gte'],
            'release_date_lte': config['release_date_lte'],
            'pages': config['pages']
        }
        
        try:
            # Ingest this language
            results = ingester.ingest_from_tmdb_discover(lang_config)
            
            # Save immediately after each language
            print(f"\n💾 Saving {lang_name} movies to sheet...")
            ingester.save_to_sheet(results)
            
            # Accumulate results
            all_results['fetched'].extend(results['fetched'])
            all_results['updated'].extend(results['updated'])
            all_results['skipped'].extend(results['skipped'])
            all_results['errors'].extend(results['errors'])
            
            # Language summary
            print(f"\n✅ {lang_name} Complete:")
            print(f"   New: {len(results['fetched'])}, Updated: {len(results['updated'])}, Skipped: {len(results['skipped'])}, Errors: {len(results['errors'])}")
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted during {lang_name} processing")
            print(f"💾 Progress saved up to this point!")
            break
        except Exception as e:
            print(f"\n❌ Error processing {lang_name}: {e}")
            continue
    
    # Print final summary
    print("\n" + "="*80)
    print("✅ INGESTION COMPLETE" if i == len(config['languages']) else "⚠️  INGESTION INTERRUPTED")
    print("="*80)
    print(f"\n📊 Final Statistics:")
    print(f"   Languages processed: {i}/{len(config['languages'])}")
    print(f"   New movies added: {len(all_results['fetched'])}")
    print(f"   Movies updated: {len(all_results['updated'])}")
    print(f"   Movies skipped (duplicates): {len(all_results['skipped'])}")
    print(f"   Errors encountered: {len(all_results['errors'])}")
    
    if all_results['errors']:
        print(f"\n❌ Errors (showing first 10):")
        for tmdb_id, error in all_results['errors'][:10]:
            print(f"   - TMDB ID {tmdb_id}: {error}")
    
    print(f"\n📝 Next Steps:")
    print(f"   1. Open movies_master.xlsx to review new movies")
    print(f"   2. Update status from 'review' to 'published' for movies you want in UI")
    print(f"   3. Run: python generate_json.py")
    print("\n")


if __name__ == '__main__':
    main()
