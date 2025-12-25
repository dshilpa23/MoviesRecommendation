"""
Configuration file for movie catalog system
- Placeholder constants
- Canonical mappings
- Sheet schema definitions
- File paths
"""

from pathlib import Path

# ===== FILE PATHS =====
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
MASTER_SHEET_PATH = PROJECT_ROOT / "movies_master.xlsx"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# ===== PLACEHOLDER CONSTANTS =====
PLACEHOLDER_POSTER = "images/placeholder.jpg"
PLACEHOLDER_DESCRIPTION = ""
PLACEHOLDER_RATING = None
PLACEHOLDER_GENRES = []
PLACEHOLDER_OTT_LIST = []
PLACEHOLDER_RELEASE_DATE = ""
PLACEHOLDER_YOUTUBE_ID = ""
PLACEHOLDER_WATCH_URL = ""
PLACEHOLDER_REGION = ""

# ===== CANONICAL LANGUAGE MAPPING =====
CANONICAL_LANGUAGES = {
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
    'bollywood': 'Hindi',  # Alias
}

# ===== STATUS VALUES =====
STATUS_DRAFT = 'draft'
STATUS_REVIEW = 'review'
STATUS_PUBLISHED = 'published'

# ===== TMDB API CONFIGURATION =====
TMDB_API_KEY = "bdefe595e85835d5c203b5b0c71561b6"  # Get from https://www.themoviedb.org/settings/api
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_RATE_LIMIT = 40  # Requests per 10 seconds (TMDB allows 40/10s)
STATUS_HIDDEN = 'hidden'

VALID_STATUSES = [STATUS_DRAFT, STATUS_REVIEW, STATUS_PUBLISHED, STATUS_HIDDEN]

# ===== BUCKET VALUES =====
BUCKET_UPCOMING = 'upcoming'
BUCKET_NEW = 'new'
BUCKET_CATALOG = 'catalog'
BUCKET_BEST = 'best'

VALID_BUCKETS = [BUCKET_UPCOMING, BUCKET_NEW, BUCKET_CATALOG, BUCKET_BEST]

# ===== CONFIDENCE LEVELS =====
CONFIDENCE_HIGH = 'high'
CONFIDENCE_MEDIUM = 'medium'
CONFIDENCE_LOW = 'low'
CONFIDENCE_NEEDS_REVIEW = 'needs_review'

VALID_CONFIDENCE_LEVELS = [
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    CONFIDENCE_NEEDS_REVIEW
]

# ===== AUDIENCE VALUES =====
AUDIENCE_FAMILY = 'family'
AUDIENCE_ADULTS = 'adults'
AUDIENCE_TEENS = 'teens'
AUDIENCE_KIDS = 'kids'

VALID_AUDIENCES = [AUDIENCE_FAMILY, AUDIENCE_ADULTS, AUDIENCE_TEENS, AUDIENCE_KIDS]

# ===== OTT PLATFORM MAPPING =====
OTT_PLATFORMS = {
    'netflix': 'Netflix',
    'prime': 'Prime Video',
    'hotstar': 'Disney+ Hotstar',
    'zee5': 'Zee5',
    'sonyliv': 'Sony LIV',
    'jiocinema': 'JioCinema',
    'aha': 'Aha',
    'mx': 'MX Player',
    'voot': 'Voot',
    'all': 'Multiple Platforms'
}

# ===== SHEET SCHEMA DEFINITION =====
SHEET_COLUMNS = {
    # Identity & Dedup
    'movieId': str,
    'movieKey': str,
    'normalizedTitle': str,
    
    # Core Scraped Fields
    'title': str,
    'sourceUrl': str,
    'posterUrl': str,
    'releaseDate': str,  # YYYY-MM-DD format
    'releaseYear': int,
    'language': str,  # MUST be capitalized
    'region': str,
    'description': str,
    'genres': str,  # JSON array or comma-separated
    
    # External IDs
    'imdbId': str,  # tt1234567
    'tmdbId': str,  # 123456
    
    # Editorial Fields
    'rating': float,  # 0.0-10.0
    'ottList': str,  # JSON array or comma-separated
    'primaryOtt': str,  # Main platform
    'watchUrl': str,  # Direct watch link
    'youtubeId': str,  # Trailer ID
    'actors': str,  # JSON array of actor names
    'audience': str,  # family, adults, teens, kids
    'editorNotes': str,  # Internal comments
    'confidence': str,  # high, medium, low, needs_review
    'bucket': str,  # upcoming, new, catalog, best
    
    # Workflow Fields
    'status': str,  # draft, review, published, hidden
    'descriptionLock': bool,
    'posterLock': bool,
    'ottLock': bool,
    'scrapedAt': str,  # ISO datetime
    'lastUpdatedAt': str,  # ISO datetime
    'lastReviewedAt': str,  # ISO datetime
    'forceRefresh': bool,
}

# Required fields for published movies
REQUIRED_FIELDS_FOR_PUBLISH = [
    'movieId',
    'movieKey',
    'title',
    'language',
    'bucket',
]

# ===== JSON OUTPUT FILES =====
JSON_OUTPUT_FILES = {
    BUCKET_UPCOMING: 'upcoming-ott.json',
    BUCKET_NEW: 'ott-releases.json',
    BUCKET_BEST: 'best-india.json',
    BUCKET_CATALOG: 'catalog.json',
}

SEARCH_INDEX_FILE = 'search-index.json'

# ===== QUALITY CHECK THRESHOLDS =====
MIN_DESCRIPTION_LENGTH = 20
MIN_POSTER_URL_LENGTH = 10
WARN_IF_MISSING_RATING = True
WARN_IF_MISSING_OTT = True

# ===== SCRAPING SETTINGS =====
SCRAPE_TIMEOUT = 30  # seconds
SCRAPE_RETRY_COUNT = 3
SCRAPE_DELAY_BETWEEN_REQUESTS = 2  # seconds

# ===== UI BACKWARD COMPATIBILITY =====
# Fields that UI expects but may have different names in sheet
UI_FIELD_MAPPING = {
    'genre': 'genres',  # UI looks for both 'genre' and 'genres'
    'ott': 'primaryOtt',  # UI looks for 'ott' field
}
