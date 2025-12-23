# 📚 Movie Catalog System - Sheet-First Architecture

**Branch:** `feature/sheet-first-architecture`

## 🎯 Overview

This is a production-grade movie catalog system where:
- ✅ Movies are scraped **only once**
- ✅ Editorial data is managed in a **spreadsheet** (single source of truth)
- ✅ UI consumes **static JSON files only**
- ✅ No runtime scraping or external API calls in the browser

---

## 📊 Architecture Workflow

```
┌──────────────────┐
│  New Movie URLs  │ (Manual/Scheduled)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  scraper.py      │ Check if movieKey exists
│  Dedup Check     │ Skip if already scraped
└────────┬─────────┘
         │ (new only)
         ▼
┌──────────────────┐
│  Scrape Once     │ Extract: title, poster, date, etc.
│  (Playwright)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ movies_master    │ Append new row
│    .xlsx         │ Auto-generate movieId, movieKey
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Editorial Review │ Editor curates in Excel/Sheets
│ Lock fields      │ Set ratings, OTT, confidence
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ generate_json.py │ Export to UI JSON files
│ Static Export    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  UI (app.js)     │ Reads JSON only
│  No scraping     │ Never calls sourceUrl
└──────────────────┘
```

---

## 📁 File Structure

```
/workspaces/MoviesRecommendation/
├── movies_master.xlsx          # ⭐ SOURCE OF TRUTH (spreadsheet)
│
├── utils.py                    # Dedup, normalization utilities
├── config.py                   # Constants, schema, paths
├── init_sheet.py               # One-time: Create sheet from existing JSON
├── scraper.py                  # Scrape-once logic with dedup
├── generate_json.py            # Export sheet → JSON for UI
│
├── data/                       # UI reads from here (generated)
│   ├── upcoming-ott.json
│   ├── ott-releases.json
│   ├── best-india.json
│   └── search-index.json
│
├── reports/                    # Generation quality reports
│   └── generation_*.json
│
├── app.js                      # ✅ UI unchanged (reads JSON)
├── index.html                  # ✅ UI unchanged
└── styles.css                  # ✅ UI unchanged
```

---

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
pip install pandas openpyxl playwright beautifulsoup4 lxml
python -m playwright install chromium
```

### 2. Initialize Master Spreadsheet (One-Time)

```bash
# Migrate existing JSON data to Excel
python init_sheet.py
```

This creates `movies_master.xlsx` with 363 movies from your existing JSON files.

---

## 🚀 Usage

### **Workflow 1: Scrape New Movies** (Scrape Once)

```bash
# Edit scraper.py with your URLs
python scraper.py
```

**What happens:**
1. Checks if `movieKey` already exists in sheet
2. Skips movies already in catalog
3. Only scrapes **new** movies
4. Appends to `movies_master.xlsx` with `status=review`

**Re-scraping:** Only allowed if `forceRefresh=True` is set in sheet for that movie.

---

### **Workflow 2: Editorial Curation**

1. Open `movies_master.xlsx` in Excel/Google Sheets
2. Review movies with `status=review`
3. Edit fields:
   - **Rating** (0.0-10.0)
   - **ottList** (JSON array: `["netflix", "prime"]`)
   - **bucket** (`upcoming`, `new`, `best`, `catalog`)
   - **confidence** (`high`, `medium`, `low`, `needs_review`)
4. **Lock fields** to prevent scraper overwrites:
   - `descriptionLock = TRUE` → description won't be overwritten
   - `posterLock = TRUE` → poster won't be overwritten
   - `ottLock = TRUE` → OTT data won't be overwritten
5. Set `status=published` when ready

**Important:** Languages MUST be capitalized: `Hindi`, `Telugu`, `Tamil`, `Malayalam` (not `hindi`, `telugu`)

---

### **Workflow 3: Generate UI JSON**

```bash
# Export published movies to JSON files
python generate_json.py
```

**What happens:**
1. Reads `movies_master.xlsx`
2. Filters `status=published` movies only
3. Generates section-specific JSON files:
   - `data/upcoming-ott.json` (bucket=upcoming)
   - `data/ott-releases.json` (bucket=new)
   - `data/best-india.json` (bucket=best)
   - `data/search-index.json` (all published)
4. Normalizes languages to capitalized form
5. Adds placeholders for missing data
6. Creates quality report in `reports/`

**UI Reads These Files** — No scraping at runtime!

---

## 📋 Spreadsheet Schema

### Core Columns

| Column | Type | Purpose | Editable |
|--------|------|---------|----------|
| `movieId` | string | Stable ID (imdb/tmdb/generated) | ❌ Auto |
| `movieKey` | string | Dedup key: `title_year_lang` | ❌ Auto |
| `title` | string | Movie title | ✅ |
| `releaseDate` | date | YYYY-MM-DD format | ✅ |
| `language` | string | **MUST be capitalized** (Hindi, Telugu) | ✅ |
| `posterUrl` | string | Poster image URL | ✅ |
| `description` | text | Plot summary | ✅ |
| `genres` | json/text | `["action", "drama"]` | ✅ |
| `sourceUrl` | string | Origin URL (metadata only) | ❌ |

### Editorial Columns

| Column | Type | Purpose | Editable |
|--------|------|---------|----------|
| `rating` | float | 0.0-10.0 | ✅ |
| `ottList` | json/text | `["netflix", "prime"]` | ✅ |
| `primaryOtt` | string | Main platform | ✅ |
| `watchUrl` | string | Direct watch link | ✅ |
| `youtubeId` | string | Trailer ID | ✅ |
| `bucket` | enum | `upcoming`, `new`, `best`, `catalog` | ✅ |
| `confidence` | enum | `high`, `medium`, `low`, `needs_review` | ✅ |
| `status` | enum | `draft`, `review`, `published`, `hidden` | ✅ |

### Workflow Columns

| Column | Type | Purpose | Editable |
|--------|------|---------|----------|
| `descriptionLock` | bool | Prevent scraper overwrite | ✅ |
| `posterLock` | bool | Prevent poster overwrite | ✅ |
| `ottLock` | bool | Prevent OTT overwrite | ✅ |
| `forceRefresh` | bool | Allow re-scraping | ✅ |
| `scrapedAt` | datetime | First scrape timestamp | ❌ Auto |
| `lastUpdatedAt` | datetime | Last modification | ❌ Auto |

---

## 🔒 Rules & Constraints

### **Non-Negotiable Rules**

1. ✅ **UI never fetches `sourceUrl`** — All data from JSON
2. ✅ **Scraper skips existing movies** — Unless `forceRefresh=True`
3. ✅ **Editorial fields never overwritten** — Locked fields protected
4. ✅ **Sheet is source of truth** — JSON is generated output
5. ✅ **Languages must be capitalized** — `Hindi` not `hindi`

### **Deduplication Logic**

```python
movieKey = "{normalized_title}_{year}_{language}_{region}"
# Example: "jawan_2023_hindi"
```

- Normalize title: lowercase, remove punctuation, collapse spaces
- Extract year from releaseDate
- Use canonical language (capitalized)
- Optional region suffix

### **Placeholder Policy**

| Field | Missing Value | UI Behavior |
|-------|---------------|-------------|
| `posterUrl` | `""` | Show placeholder image |
| `description` | `""` | Hide description section |
| `rating` | `null` | Hide rating badge |
| `ottList` | `[]` | Show "TBA" or hide |
| `genres` | `[]` | Hide genre section |
| `releaseDate` | `""` | Show "Coming Soon" |

---

## 📊 Quality Reports

After running `generate_json.py`, check `reports/generation_*.json`:

```json
{
  "generated_at": "2025-12-22T23:11:51",
  "total_in_sheet": 363,
  "published": 363,
  "files_generated": {
    "upcoming-ott.json": {"count": 5, "bucket": "upcoming"},
    "ott-releases.json": {"count": 143, "bucket": "new"},
    "best-india.json": {"count": 215, "bucket": "best"},
    "search-index.json": {"count": 363, "type": "search_index"}
  },
  "quality_issues": {
    "missing_language": ["Movie Title 1", ...],
    "missing_poster": [...],
    "invalid_language_case": [
      {"title": "Leo", "current": "hindi", "should_be": "Hindi"}
    ]
  },
  "warnings": [
    "34 movies missing language",
    "363 movies missing description"
  ]
}
```

**Use this to find movies needing editorial attention.**

---

## 🛠️ Common Tasks

### Fix Language Capitalization

Open `movies_master.xlsx` and search/replace:
- `hindi` → `Hindi`
- `telugu` → `Telugu`
- `tamil` → `Tamil`
- `malayalam` → `Malayalam`

Then regenerate JSON.

### Add New Movies Without Re-Scraping Existing

```bash
# Edit scraper.py with new URLs only
python scraper.py
# Review new movies in sheet
# Set status=published
python generate_json.py
```

### Force Re-Scrape a Movie

In `movies_master.xlsx`:
1. Find the movie row
2. Set `forceRefresh = TRUE`
3. Run `python scraper.py`
4. Scraper will update unlocked fields only

### Migrate More Data

```python
# Edit init_sheet.py to add more JSON files
import_files = [
    ('best-india.json', BUCKET_BEST),
    ('ott-releases.json', BUCKET_NEW),
    ('your-new-file.json', BUCKET_CATALOG),  # Add here
]
```

---

## ✅ Self-Verification Checklist

Before merging to main, confirm:

- [ ] All work isolated in `feature/sheet-first-architecture` branch
- [ ] UI does not call any external URLs
- [ ] Movies are scraped once only (dedup works)
- [ ] Sheet is the single source of truth
- [ ] Language values are capitalized everywhere
- [ ] Missing data does not break UI
- [ ] JSON files generated successfully
- [ ] Quality report shows valid stats
- [ ] Existing UI functionality unchanged

---

## 🔄 Workflow Summary

**Guiding Principle:**
```
Scrape once → Curate in sheet → Generate JSON → UI reads only
```

**Never:**
- ❌ Manually edit JSON files
- ❌ Scrape from UI at runtime
- ❌ Overwrite editorial data
- ❌ Use lowercase languages

**Always:**
- ✅ Edit movies in Excel/Sheets
- ✅ Run `generate_json.py` after edits
- ✅ Check quality reports
- ✅ Lock fields to prevent overwrites

---

## 📞 Support

Questions? Check:
1. Quality report: `reports/generation_*.json`
2. Spreadsheet: `movies_master.xlsx`
3. This README

---

**Status:** ✅ Ready for testing and validation
**Next Step:** Run end-to-end test and verify UI functionality
