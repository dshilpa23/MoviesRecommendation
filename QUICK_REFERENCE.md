# 🚀 Quick Reference - Movie Catalog System

## ⚡ Daily Operations

### 1. Enrich Movie Metadata (Genres, Ratings)
```bash
# Set your TMDb API key (one-time setup)
export TMDB_API_KEY='your_api_key_here'

# Run enrichment to fill missing genres and ratings
python enrich_metadata.py
# Fills: genres (from TMDb), ratings (0-10 scale)
# Time: ~2 minutes for 363 movies
# Report: reports/enrichment_YYYYMMDD_HHMMSS.json
```

### 2. Generate UI JSON Files
```bash
python generate_json.py
# Creates: upcoming-ott.json, ott-releases.json, best-india.json, search-index.json
# Updates: All movie data with enriched fields
```

### 3. Download Posters Locally (One-Time)
```bash
python download_posters.py
# Downloads ~363 images to images/posters/
# Wait for completion (~5 minutes)
# Updates posterUrl in spreadsheet to local paths
```

### 4. Start Admin Dashboard Server
```bash
# Option 1: Use the startup script (recommended)
bash start-admin.sh
# Opens admin dashboard at http://127.0.0.1:5000

# Option 2: Manual setup
python3 -m venv admin/.venv              # Create virtual environment (one-time)
source admin/.venv/bin/activate          # Activate venv
pip install -r admin/requirements.txt    # Install dependencies
python admin/app.py                      # Start Flask server
# Opens admin dashboard at http://127.0.0.1:5000

# Option 3: One-liner
python3 -m venv admin/.venv && source admin/.venv/bin/activate && pip install -r admin/requirements.txt && python admin/app.py
```

### 5. Test UI Locally
```bash
python -m http.server 8000
# Open: http://localhost:8000
```

---

## 📊 File Roles

| File | Role | Edit? |
|------|------|-------|
| `movies_master.xlsx` | ⭐ SOURCE OF TRUTH | ✅ YES (in Excel) |
| `data/*.json` | UI reads these | ❌ NO (auto-generated) |
| `images/posters/*` | Local images | ❌ NO (auto-downloaded) |
| `*.py` | Tools/scripts | Only if adding features |

---

## 🔄 Workflows

### Weekly Maintenance: Keep Data Fresh
```bash
# 1. Scrape new movies (if needed)
python scraper.py

# 2. Enrich missing metadata (genres, ratings) API Key UI https://www.themoviedb.org/settings/api user dshilpa
export TMDB_API_KEY='your_key'
python enrich_metadata.py

# 3. Review enrichment report
cat reports/enrichment_*.json | jq '.needsReviewCount'

# 4. Open spreadsheet and fix flagged movies
open movies_master.xlsx

# 5. Regenerate UI files
python generate_json.py

# 6. Test locally
python -m http.server 8000
```

### Add New Movies
```bash
# Method 1: Scraper (from StudioFlicks)
1. Edit scraper.py → add URLs to scrape
2. python scraper.py (skips existing, deduplicates)
3. python enrich_metadata.py (auto-fills genres/ratings)
4. Open movies_master.xlsx
5. Review new movies (check matchStatus column)
6. Set status=published
7. python generate_json.py

# Method 2: Manual Entry
1. Open movies_master.xlsx
2. Add row with: title, releaseDate, language, posterUrl
3. python enrich_metadata.py (auto-fills missing fields)
4. Set status=published
5. python generate_json.py
```

### Fix Existing Movie
```bash
1. Open movies_master.xlsx
2. Find movie, edit fields
3. Lock fields if needed (descriptionLock=TRUE)
4. python generate_json.py
```

### Update Images
```bash
1. Delete old image from images/posters/
2. In spreadsheet: set posterLock=FALSE
3. python download_posters.py
4. python generate_json.py
```

### Fix Missing Genres/Ratings
```bash
# Automatic enrichment
python enrich_metadata.py

# Check which movies need manual review
cat reports/enrichment_*.json | jq '.unresolvedExamples'

# Manual fixes in spreadsheet
open movies_master.xlsx
# Find rows with matchStatus='needs_review'
# Add genres manually as JSON: ["Action", "Drama"]
# Add rating manually: 7.5
# Save and regenerate
python generate_json.py
```

---

## 🎨 Key Fields in Spreadsheet

### Auto-Generated (Don't Edit)
- `movieId`, `movieKey`, `normalizedTitle`
- `scrapedAt`, `lastUpdatedAt`, `lastEnrichedAt`

### Edit Anytime
- `title`, `releaseDate`, `language` (MUST be capitalized: Hindi, Telugu, Tamil, Malayalam)
- `posterUrl`, `description`, `genres` (JSON array: ["Action", "Drama"])
- `rating` (0-10 scale), `ottList`, `watchUrl`
- `bucket` (upcoming/new/best/catalog)
- `status` (draft/review/published/hidden)

### Enrichment Fields (Auto-filled by enrich_metadata.py)
- `genres` → from TMDb (title-cased: Action, Drama, Thriller)
- `rating` → from TMDb (0-10 scale)
- `genreSource`, `ratingSource` → provenance tracking
- `confidence` → high/medium/low
- `matchStatus` → needs_review if uncertain
- `tmdbId` → saved for future lookups

### Lock Flags (Prevent Scraper Overwrite)
- `descriptionLock` → protects description
- `posterLock` → protects posterUrl
- `ottLock` → protects OTT data
- `forceRefresh` → allows re-scraping

---

## ✅ Quick Checks

### Check Enrichment Status
```bash
# View latest enrichment report
cat reports/enrichment_*.json | jq '.'

# Check how many genres/ratings filled
cat reports/enrichment_*.json | jq '{genres: .genreFilledCount, ratings: .ratingFilledCount, needsReview: .needsReviewCount}'

# See which movies need manual review
cat reports/enrichment_*.json | jq '.unresolvedExamples'
```

### Images Loading Locally?
```bash
# Check poster count
ls images/posters/ | wc -l
# Should show ~363

# Check JSON has local paths
grep "posterUrl" data/best-india.json | head -3
# Should show: "posterUrl": "images/posters/..."
```

### Genres and Ratings Working?
```bash
# Check first movie has enriched data
python -c "import json; m=json.load(open('data/best-india.json'))[0]; print(f\"Title: {m['title']}\nGenres: {m.get('genres')}\nRating: {m.get('rating')}\")"

# Count movies with ratings
grep -o '"rating": [0-9]' data/best-india.json | wc -l
```

### Languages Capitalized?
```bash
# Check spreadsheet or JSON
grep "language" data/best-india.json | head -5
# Should show: "language": "Hindi" (NOT "hindi")
```

### Center Alignment Working?
```
Open http://localhost:8000
- Content should be centered
- Ads on left/right (if screen > 1300px)
- Max width: 1200px for content
```

---

## 🆘 Troubleshooting

### "No genres or ratings showing"
```bash
# Run enrichment
export TMDB_API_KEY='your_key'
python enrich_metadata.py

# Regenerate JSON
python generate_json.py

# Refresh browser
```

### "Some movies missing genres/ratings"
```bash
# Check enrichment report
cat reports/enrichment_*.json | jq '.needsReviewCount'

# See which movies failed
cat reports/enrichment_*.json | jq '.unresolvedExamples'

# Common reasons:
# - Missing release year → add in spreadsheet
# - Title mismatch → add tmdbId manually
# - Not in TMDb → add genres/rating manually in spreadsheet
```

### "Images not loading"
```bash
# Re-download posters
python download_posters.py

# Regenerate JSON
python generate_json.py

# Check image exists
ls images/posters/gen_jawan_2023_hindi.jpg
```

### "Duplicate movies"
```bash
# Check movieKey in spreadsheet
# If duplicate, delete one row
# Regenerate JSON
python generate_json.py
```

### "UI broken after changes"
```bash
# Check JSON format
python -m json.tool data/best-india.json | head

# Check for errors
python generate_json.py
# Review quality report
cat reports/generation_*.json
```

---

## � Complete Maintenance Checklist

### Monthly Full Update
```bash
# 1. Get latest TMDb API key (if expired)
export TMDB_API_KEY='your_key'

# 2. Scrape new releases
python scraper.py

# 3. Enrich all missing metadata
python enrich_metadata.py

# 4. Review report and fix flagged movies
cat reports/enrichment_*.json | jq '.unresolvedExamples'
open movies_master.xlsx

# 5. Download any new posters
python download_posters.py

# 6. Regenerate all UI files
python generate_json.py

# 7. Test UI
python -m http.server 8000

# 8. Check quality
cat reports/generation_*.json | jq '.'

# 9. Commit changes
git add movies_master.xlsx data/ images/posters/
git commit -m "Monthly data update: enriched metadata and new movies"
git push
```

### After Adding New Movies
```bash
python enrich_metadata.py  # Auto-fill genres/ratings
python generate_json.py     # Update UI
```

### After Editing Spreadsheet
```bash
python generate_json.py     # Always regenerate after edits
```

### Get TMDb API Key (Free)
```
1. Visit: https://www.themoviedb.org/settings/api
2. Sign up (free account)
3. Request API key (takes 1 minute)
4. Copy "API Key (v3 auth)"
5. export TMDB_API_KEY='your_key'
```

---

## �📝 Language Rules

**MUST BE CAPITALIZED:**
- Hindi (not hindi)
- Telugu (not telugu)
- Tamil (not tamil)
- Malayalam (not malayalam)

**Find/Replace in Excel:**
```
hindi → Hindi
telugu → Telugu
tamil → Tamil
malayalam → Malayalam
```

Then regenerate: `python generate_json.py`

---

## 🎯 Quality Report

After generating JSON, check:
```bash
cat reports/generation_*.json
```

Look for:
- `missing_language` → needs editorial fix
- `missing_poster` → needs poster download
- `missing_description` → optional
- `invalid_language_case` → needs capitalization

---

## 📦 Dependencies

```bash
pip install pandas openpyxl requests Pillow playwright beautifulsoup4 lxml
```

---

## 🔒 Remember

✅ **Sheet is source of truth** - edit there, not JSON  
✅ **Generate after edits** - always run `generate_json.py`  
✅ **Local images** - no external calls  
✅ **Languages capitalized** - Hindi not hindi  
✅ **Lock edited fields** - prevent scraper overwrite  

---

**Questions?** See `SHEET_ARCHITECTURE.md` or `IMPLEMENTATION_SUMMARY.md`
