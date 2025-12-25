"""
Test script for TMDB Discovery API ingestion
Tests with a small sample to verify functionality
"""

from scraper import MovieIngester

def test_discovery():
    """Test TMDB discovery with small sample"""
    ingester = MovieIngester()
    
    # Small test configuration - just 1 page of Hindi movies
    config = {
        'region': 'IN',
        'languages': ['hi'],  # Just Hindi for testing
        'release_date_gte': '2024-12-01',
        'release_date_lte': '2024-12-31',
        'pages': 1  # Just 1 page for testing
    }
    
    print("🧪 Running TMDB Discovery Test\n")
    print("Configuration:")
    print(f"  Region: {config['region']}")
    print(f"  Languages: {config['languages']}")
    print(f"  Date Range: {config['release_date_gte']} to {config['release_date_lte']}")
    print(f"  Pages: {config['pages']}\n")
    
    results = ingester.ingest_from_tmdb_discover(config)
    
    # Print results
    print(f"\n✅ Test Complete!")
    print(f"\n📊 Results:")
    print(f"   New movies fetched: {len(results['fetched'])}")
    print(f"   Movies updated: {len(results['updated'])}")
    print(f"   Movies skipped: {len(results['skipped'])}")
    print(f"   Errors: {len(results['errors'])}")
    
    # Show sample of fetched movies
    if results['fetched']:
        print(f"\n🎬 Sample of new movies:")
        for i, movie in enumerate(results['fetched'][:5], 1):
            print(f"   {i}. {movie['title']} ({movie['language']}) - {movie['releaseDate']}")
            print(f"      Rating: {movie['rating']}, OTT: {movie['ottList']}")
            actors = movie.get('actors', '')
            if actors:
                print(f"      Actors: {actors}")
    
    # Save to sheet if any results
    if results['fetched'] or results['updated']:
        print(f"\n💾 Saving to sheet...")
        ingester.save_to_sheet(results)
        print(f"✅ Saved successfully!")
    
    return results


if __name__ == '__main__':
    test_discovery()
