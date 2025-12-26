#!/usr/bin/env python3
"""
Update OTT list in ott-releases.json:
1. Keep only allowed platforms: sonyliv, netflix, amazon, sunnxt, hotstar, hulu, zee
2. Consolidate multiple Amazon variants into a single "Amazon Prime Video" entry
"""

import json
import os

ALLOWED_PLATFORMS = {
    'sonyliv', 'netflix', 'amazon', 'sunnxt', 'hotstar', 'hulu', 'zee'
}

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
    3. Consolidating Amazon variants
    """
    if not ott_list or not isinstance(ott_list, list):
        return []
    
    seen = set()
    cleaned = []
    
    for ott in ott_list:
        if not ott:
            continue
        normalized = normalize_platform(ott)
        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(ott)  # Keep original string if it's the first occurrence
    
    # Now consolidate - remove duplicates and keep only one amazon
    final = []
    amazon_found = False
    
    for ott in cleaned:
        normalized = normalize_platform(ott)
        if normalized == 'amazon':
            if not amazon_found:
                final.append('Amazon Prime Video')
                amazon_found = True
        else:
            final.append(ott)
    
    return final

def update_ott_releases():
    """Update the ott-releases.json file."""
    file_path = '/workspaces/MoviesRecommendation/data/ott-releases.json'
    
    # Read the JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        movies = json.load(f)
    
    stats = {
        'total': len(movies),
        'modified': 0,
        'had_invalid_platforms': 0,
        'had_multiple_amazon': 0
    }
    
    # Process each movie
    for movie in movies:
        original_list = movie.get('ottList', [])
        
        # Check for multiple amazon entries
        if isinstance(original_list, list):
            amazon_count = sum(1 for ott in original_list if normalize_platform(ott) == 'amazon')
            if amazon_count > 1:
                stats['had_multiple_amazon'] += 1
        
        # Clean the OTT list
        cleaned_list = clean_ott_list(original_list)
        
        # Check if list was modified
        if cleaned_list != original_list:
            stats['modified'] += 1
            if len(original_list) > 0 and len(cleaned_list) == 0:
                # Had invalid platforms
                stats['had_invalid_platforms'] += 1
        
        movie['ottList'] = cleaned_list
    
    # Write the updated JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Updated {file_path}")
    print(f"\nStats:")
    print(f"  Total movies: {stats['total']}")
    print(f"  Modified: {stats['modified']}")
    print(f"  Had multiple Amazon entries: {stats['had_multiple_amazon']}")
    print(f"  Had only invalid platforms: {stats['had_invalid_platforms']}")
    print(f"\nAllowed platforms: {', '.join(sorted(ALLOWED_PLATFORMS))}")

if __name__ == '__main__':
    update_ott_releases()
