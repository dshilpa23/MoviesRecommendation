# Movies Recommendation

A web-based application that provides movie and OTT release recommendations with search functionality.

## 📊 Data Flow: TMDB → UI

### Architecture Overview

```
┌─────────────────┐
│   TMDB API      │
│  (themoviedb    │
│     .org)       │
└────────┬────────┘
         │
         │ scraper.py fetches
         │ (discovery, details, credits, providers)
         ↓
┌─────────────────┐
│movies_master    │ ← SOURCE OF TRUTH
│    .xlsx        │   Edit manually here
└────────┬────────┘
         │
         │ generate_json.py reads
         │ Filters status=published
         │ Groups by bucket
         ↓
┌─────────────────┐
│   data/*.json   │ ← UI data files
│ - upcoming-ott  │
│ - ott-releases  │
│ - best-india    │
│ - search-index  │
└────────┬────────┘
         │
         │ app.js fetches
         │ (on page load)
         ↓
┌─────────────────┐
│   Browser UI    │
│ (index.html)    │
│ - Movie cards   │
│ - With actors!  │
└─────────────────┘
```

### 1. **Data Ingestion** (TMDB → Excel)
**File: `scraper.py`**
- Fetches movies from TMDB API using Discovery/Search endpoints
- Gets movie details: title, rating, genres, release date, poster URL
- Gets cast information from Credits API (top 3 actors)
- Gets OTT platforms from Watch Providers API
- **Output:** Saves everything to `movies_master.xlsx`

**Key Data Fetched:**
- `tmdbId`, `title`, `releaseDate`, `language`
- `rating` (0-10 scale from TMDB)
- `genres` (array: ["Action", "Drama"])
- `actors` (JSON array: ["Actor 1", "Actor 2", "Actor 3"])
- `posterUrl` (TMDB image URL)
- `ottList` (JSON array of streaming platforms)

### 2. **Source of Truth** (Storage)
**File: `movies_master.xlsx`**
- Excel spreadsheet with all movie data
- Contains all movies fetched from TMDB
- Has status column: `draft`, `review`, `published`, `hidden`
- Only `published` movies appear on UI
- Manual editing required to:
  - Set `status=published` to show movie on UI
  - Set `bucket` (upcoming/new/catalog/best)
  - Add/edit descriptions, lock fields, etc.

### 3. **JSON Generation** (Excel → JSON)
**File: `generate_json.py`**
- Reads `movies_master.xlsx`
- Filters only `status=published` movies
- Groups movies by `bucket` field
- **Creates 4 JSON files in `data/` folder:**
  - `data/upcoming-ott.json` ← bucket='upcoming'
  - `data/ott-releases.json` ← bucket='new'
  - `data/catalog.json` ← bucket='catalog'
  - `data/best-india.json` ← bucket='best'
  - `data/search-index.json` ← All movies (for search)

**What goes in each JSON:**
- Full movie objects with: title, posterUrl, releaseDate, language, rating, genres, actors, ottList, description, etc.
- Actors field: `"actors": ["Actor 1", "Actor 2", "Actor 3"]`

### 4. **UI Display** (JSON → Browser)
**Files: `index.html` + `app.js` + `styles.css`**

**How it works:**
1. Browser loads `index.html`
2. `app.js` fetches JSON files:
   - `data/upcoming-ott.json` → "Upcoming OTT" section
   - `data/ott-releases.json` → "New Releases OTT" section
   - `data/best-india.json` → "Best Rated" section
   - `data/search-index.json` → Search functionality
3. For each movie, creates a card with poster, title, badges, cast info, description, and watch button

### File Roles Summary

| File | Purpose | You Edit? |
|------|---------|-----------|
| `scraper.py` | Fetch from TMDB | No (unless changing features) |
| `movies_master.xlsx` | **Master data** | ✅ **YES** (set status, bucket, etc.) |
| `generate_json.py` | Excel → JSON | No (unless changing features) |
| `data/*.json` | UI reads these | ❌ Auto-generated |
| `index.html` | UI structure | Only for layout changes |
| `app.js` | UI logic | Only for feature changes |

## Project Structure

```
├── app.js                 # Main JavaScript application
├── index.html            # HTML interface
├── styles.css            # Styling
├── excel_to_json.py      # Python script to convert Excel to JSON
├── movies.json           # Movie data
├── movies.xlsx           # Excel source data
├── data/                 # Data directory
│   ├── best-india.json
│   ├── ott-releases.json
│   ├── upcoming-ott.json
│   ├── upcoming-theatrical.json
│   ├── search-index.json
│   └── index.html
└── Readme.md            # This file
```

## Features

- Browse upcoming OTT releases
- View new OTT releases
- Explore best Indian movies/shows
- Search movies by title
- Pagination support
- Language-based sorting

## How to Run

### Option 1: Using Python's Built-in Server (Recommended)

1. Navigate to the project directory:
   ```bash
   cd /workspaces/MoviesRecommendation
   ```

2. Start a local server using Python:
   ```bash
   # For Python 3
   python -m http.server 8000
   
   # Or for Python 2
   python -m SimpleHTTPServer 8000
   ```

3. Open your browser and visit:
   ```
   http://localhost:8000
   ```

### Option 2: Using Node.js/npm

If you have Node.js installed, you can use `http-server`:

1. Install http-server globally (if not already installed):
   ```bash
   npm install -g http-server
   ```

2. Start the server:
   ```bash
   http-server
   ```

3. Open your browser and visit the URL shown in the terminal (typically `http://localhost:8080`)

### Option 3: Direct File Opening

Simply open `index.html` in your web browser by double-clicking it, though some features may work better with a server.

## Data Preparation

If you need to update the movie data from Excel:

1. Ensure you have Python 3 installed
2. Install required Python packages:
   ```bash
   pip install requests beautifulsoup4
   ```
3. Run the Excel to JSON converter:
   ```bash
   python excel_to_json.py
   ```
   
   Or run the web scraper:
   ```bash
   python flicks.py
   ```

This will convert `movies.xlsx` to JSON format and update the data files.

## Requirements

- **Browser**: Any modern web browser (Chrome, Firefox, Safari, Edge)
- **Python** (optional): For running the local server or converting Excel data
  - `requests` - For web scraping
  - `beautifulsoup4` - For HTML parsing
- **Node.js** (optional): If using http-server

## Usage

1. **Search**: Use the search bar to find movies by title
2. **Browse**: Navigate through different categories using tabs
3. **Pagination**: Use pagination controls to view more movies
4. **Filter**: Movies are automatically sorted by language priority (Hindi → Telugu → Tamil → Malayalam)

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Notes

- Make sure to serve the files through a web server (not just opening as `file://`) to avoid CORS issues
- All data is loaded from JSON files in the `data/` directory
- The application uses vanilla JavaScript with no external dependencies


====

Run Locally using cmd --> python -m http.server 8000

===INstall---
pip install -U playwright beautifulsoup4 lxml
python -m playwright install chromium
python -m playwright install-deps chromium
sudo apt-get update
sudo apt-get install -y libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxdamage1 libxrandr2 libgbm1 libpangocairo-1.0-0 libpango-1.0-0 libasound2
