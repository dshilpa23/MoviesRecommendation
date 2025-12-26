"""
Utility functions for movie catalog management
- Identity generation (movieKey, movieId)
- Title normalization for deduplication
- Language normalization (capitalization)
"""

import re
from typing import Optional


def normalize_title(title: str) -> str:
    """
    Normalize title for deduplication.
    
    Rules:
    - Convert to lowercase
    - Remove punctuation
    - Collapse multiple spaces
    - Remove common suffixes
    
    Examples:
        "Jawan (2023)" -> "jawan"
        "Leo: The Movie" -> "leo"
        "Rocketry - The Nambi Effect" -> "rocketry_the_nambi_effect"
    """
    if not title:
        return ""
    
    # Convert to lowercase
    title = title.lower().strip()
    
    # Remove year in parentheses: (2023), (2024)
    title = re.sub(r'\s*\(\d{4}\)\s*', '', title)
    
    # Remove punctuation except spaces
    title = re.sub(r'[^\w\s]', '', title)
    
    # Collapse multiple spaces to single underscore
    title = re.sub(r'\s+', '_', title.strip())
    
    # Remove common suffixes
    suffixes = [
        '_movie', '_film', '_the_movie', '_the_film',
        '_part_i', '_part_ii', '_part_1', '_part_2',
        '_part_one', '_part_two'
    ]
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[:-len(suffix)]
    
    return title


def normalize_language(language: str) -> str:
    """
    Normalize language to canonical capitalized form.
    
    Rules:
    - Always capitalize: Hindi, Telugu, Tamil, Malayalam, English
    - Handle common variations
    
    Examples:
        "hindi" -> "Hindi"
        "TELUGU" -> "Telugu"
        "malayalam" -> "Malayalam"
    """
    if not language:
        return ""
    
    # Canonical mapping
    canonical = {
        'hindi': 'Hindi',
        'telugu': 'Telugu',
        'tamil': 'Tamil',
        'malayalam': 'Malayalam',
        'english': 'English',
        'kannada': 'Kannada',
        'bengali': 'Bengali',
        'marathi': 'Marathi',
        'punjabi': 'Punjabi',
        'gujarati': 'Gujarati',
        'bollywood': 'Hindi',  # Map bollywood to Hindi
    }
    
    lang_lower = language.lower().strip()
    return canonical.get(lang_lower, language.capitalize())


def extract_year_from_date(date_str: str) -> Optional[int]:
    """
    Extract year from date string.
    
    Handles:
        "2024-01-01" -> 2024
        "2023" -> 2023
        "2024-12-25 10:30" -> 2024
        "" -> None
    """
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # Try to extract 4-digit year
    match = re.search(r'\b(\d{4})\b', date_str)
    if match:
        year = int(match.group(1))
        # Validate reasonable year range
        if 1900 <= year <= 2100:
            return year
    
    return None


def generate_movie_key(
    title: str,
    release_date: str,
    language: str,
    region: Optional[str] = None
) -> str:
    """
    Generate deterministic deduplication key.
    
    Format: {normalized_title}_{year}_{language}_{region}
    
    Examples:
        generate_movie_key("Jawan", "2023-09-07", "Hindi")
        -> "jawan_2023_hindi"
        
        generate_movie_key("Pushpa 2", "2024-12-06", "Telugu", "AP")
        -> "pushpa_2_2024_telugu_ap"
    """
    norm_title = normalize_title(title)
    year = extract_year_from_date(release_date) or 0
    norm_lang = normalize_language(language).lower()
    
    key_parts = [norm_title, str(year), norm_lang]
    
    if region:
        key_parts.append(region.lower().strip())
    
    return "_".join(key_parts)


def generate_movie_id(
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    movie_key: Optional[str] = None
) -> str:
    """
    Generate stable movie ID.
    
    Preference:
    1. imdb_id (most stable)
    2. tmdb_id
    3. generated from movie_key
    
    Examples:
        generate_movie_id(imdb_id="tt1234567") -> "imdb_tt1234567"
        generate_movie_id(tmdb_id="123456") -> "tmdb_123456"
        generate_movie_id(movie_key="jawan_2023_hindi") -> "gen_jawan_2023_hindi"
    """
    if imdb_id:
        return f"imdb_{imdb_id}"
    
    if tmdb_id:
        return f"tmdb_{tmdb_id}"
    
    if movie_key:
        return f"gen_{movie_key}"
    
    raise ValueError("Must provide at least one of: imdb_id, tmdb_id, movie_key")


def parse_genres(genres_value) -> list:
    """
    Parse genres field to list.
    
    Handles:
        - JSON arrays: ["action", "drama"]
        - Comma-separated strings: "action, drama"
        - Lists: ["action", "drama"]
        - Empty/null: []
    """
    import json
    
    if not genres_value:
        return []
    
    # Already a list
    if isinstance(genres_value, list):
        return [str(g).strip() for g in genres_value if g]
    
    # Try JSON parse
    if isinstance(genres_value, str):
        # Try JSON first
        try:
            parsed = json.loads(genres_value)
            if isinstance(parsed, list):
                return [str(g).strip() for g in parsed if g]
        except:
            pass
        
        # Try comma-separated
        if ',' in genres_value:
            return [g.strip() for g in genres_value.split(',') if g.strip()]
        
        # Single genre
        return [genres_value.strip()]
    
    return []


def parse_ott_list(ott_value) -> list:
    """
    Parse OTT platform list with filtering and consolidation.
    
    Handles:
        - JSON arrays: ["netflix", "prime"]
        - Comma-separated: "netflix, prime"
        - Lists: ["netflix", "prime"]
        - Single value: "netflix"
        - "all" -> []
    
    Filters to allowed platforms: sonyliv, netflix, amazon, sunnxt, hotstar, hulu, zee
    Consolidates multiple Amazon variants into single "Amazon Prime Video"
    """
    import json
    
    ALLOWED_PLATFORMS = {'sonyliv', 'netflix', 'amazon', 'sunnxt', 'hotstar', 'hulu', 'zee'}
    
    if not ott_value:
        return []
    
    if ott_value == "all":
        return []
    
    raw_list = []
    
    # Already a list
    if isinstance(ott_value, list):
        raw_list = [str(o).strip().lower() for o in ott_value if o and o != "all"]
    
    # Try JSON parse
    elif isinstance(ott_value, str):
        # Try JSON first
        try:
            parsed = json.loads(ott_value)
            if isinstance(parsed, list):
                raw_list = [str(o).strip().lower() for o in parsed if o and o != "all"]
        except:
            pass
        
        if not raw_list:
            # Try comma-separated
            if ',' in ott_value:
                raw_list = [o.strip().lower() for o in ott_value.split(',') if o.strip() and o.strip() != "all"]
            
            # Single platform
            elif ott_value.strip() != "all":
                raw_list = [ott_value.strip().lower()]
    
    # Filter and consolidate
    seen = set()
    cleaned = []
    amazon_found = False
    
    for ott in raw_list:
        if not ott:
            continue
        
        # Normalize platform
        normalized = None
        if 'amazon' in ott or 'prime' in ott:
            normalized = 'amazon'
        else:
            for allowed in ALLOWED_PLATFORMS:
                if allowed in ott:
                    normalized = allowed
                    break
        
        # Add to cleaned list
        if normalized == 'amazon':
            if not amazon_found:
                cleaned.append('Amazon Prime Video')
                amazon_found = True
        elif normalized and normalized not in seen:
            cleaned.append(ott)
            seen.add(normalized)
    
    return cleaned


def validate_language(language: str) -> tuple[bool, str]:
    """
    Validate language is in canonical form.
    
    Returns:
        (is_valid, normalized_language)
    
    Examples:
        validate_language("Hindi") -> (True, "Hindi")
        validate_language("hindi") -> (False, "Hindi")
        validate_language("TELUGU") -> (False, "Telugu")
    """
    if not language:
        return (False, "")
    
    normalized = normalize_language(language)
    is_valid = language == normalized
    
    return (is_valid, normalized)
