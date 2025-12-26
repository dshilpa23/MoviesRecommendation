# Admin Dashboard - User Guide

## Overview

The Admin Dashboard is a **local-only web application** (running at `http://127.0.0.1:5000`) that provides editorial workflow management for the Movies Recommendation system. It allows you to:

- 📝 Edit movie metadata in an Excel-like grid UI
- 🔍 Filter movies by status, language, region, and data completeness
- ⚙️ Run enrichment and JSON generation pipelines
- 👀 Preview generated JSON before publishing
- 💾 Manage automatic backups
- ☁️ Publish to S3/CloudFront (optional)

## Quick Start

### Linux / macOS
```bash
cd /path/to/MoviesRecommendation
./start-admin.sh
```

### Windows
```cmd
cd C:\path\to\MoviesRecommendation
start-admin.bat
```

Once started, open your browser to: **http://127.0.0.1:5000**

## Architecture

```
MoviesRecommendation/
├── admin/
│   ├── app.py                 # Flask backend (REST API)
│   ├── requirements.txt       # Python dependencies
│   ├── templates/
│   │   └── admin.html        # Web UI
│   ├── static/
│   │   ├── admin.css         # Styling
│   │   └── admin.js          # Frontend logic
│   ├── utils/
│   │   ├── excel_handler.py  # Excel read/write
│   │   ├── validation.py     # Business rules
│   │   └── pipeline_runner.py # Pipeline execution
│   └── backups/              # Auto-backup directory
├── movies_master.xlsx         # Source of truth (Excel)
└── data/                      # Generated JSON files
```

## Features

### 1. Movies Grid Tab

**View and edit all movies in an Excel-like interface.**

#### Filters:
- **Search**: Find by movie title
- **Status**: Filter by `published`, `review`, or `draft`
- **Language**: Filter by movie language
- **Region**: Filter by region (US, India, etc.)
- **Missing OTT**: Show only movies without OTT platform data
- **Missing Rating**: Show only movies without ratings

#### Stats Bar:
Displays real-time counts:
- Total movies
- Published movies
- In-review movies
- Movies missing OTT data

#### Inline Editing:
1. Click the "Edit" button for any movie
2. Update fields in the modal:
   - Title
   - Status (published/review/draft)
   - Language
   - Region
   - OTT Platforms (comma-separated)
   - Rating (0-10)
   - Release Date
3. Click "Save" to update
4. **Auto-backup** is created before saving

#### Validation Rules:
Before publishing a movie (setting status="published"), it must have:
- ✅ At least one OTT platform
- ✅ A rating > 0

If validation fails, you'll see a clear error message.

### 2. Pipeline Tab

**Run the movie enrichment and JSON generation pipeline.**

#### Step 1: Enrich Excel
Fetches metadata from TMDB and updates movies_master.xlsx:
- Downloads TMDB data for recent releases
- Cleans and normalizes OTT platforms
- Adds missing ratings

**Button**: "Run Enrichment"

#### Step 2: Generate JSON
Exports movies_master.xlsx to public JSON files:
- `data/catalog.json` - All movies
- `data/upcoming-ott.json` - Upcoming releases
- `data/best-india.json` - Best rated (India)
- `data/ott-releases.json` - Recent releases

**Button**: "Generate JSON"

#### Step 3: Preview
Shows sample of the generated JSON before publishing:
- Lists generated files
- Shows sample data structure
- Helps verify output is correct

**Button**: "Preview JSON"

#### Step 4: Publish to S3
Uploads JSON files to AWS S3 (CloudFront):
- Prompts for S3 bucket name
- Prompts for AWS region
- Uploads with cache control headers
- **Requires AWS credentials** configured

**Button**: "Publish to S3"

#### Results Display:
Each step shows:
- ✅ Success/failure status
- 📋 Command output/logs
- 📊 Summary of changes

### 3. Backups Tab

**Manage automatic backups of movies_master.xlsx**

Every time you edit and save a movie:
1. Current Excel file is backed up
2. Backup stored in `admin/backups/`
3. Filename format: `movies_master_YYYYMMDD_HHMMSS.xlsx`

#### Backup Operations:
- **View**: See all backup files with timestamps and sizes
- **Restore**: Click "Restore" to recover from a backup
  - Requires confirmation
  - Overwrites current Excel with backup
  - Useful for undoing changes

### 4. Documentation Tab

Quick reference guide including:
- 🚀 Getting Started steps
- 📋 Editorial Workflow
- ✔️ Validation Rules
- 💾 Backup Management
- ⚙️ Configuration

## Editorial Workflow

### Typical Day:

1. **Morning**: Check dashboard for new movies
   ```
   Movies Grid → Filter by status="review"
   ```

2. **Add Missing Data**: 
   - Click "Edit" on incomplete movies
   - Add OTT platforms (Netflix, Prime Video, etc.)
   - Add ratings (1-10)

3. **Publish Approved Movies**:
   - Change status to "published"
   - Dashboard validates before allowing save
   - If validation fails, complete missing data first

4. **Update Public Site**:
   - Go to Pipeline tab
   - Click "Run Enrichment" (optional, fetches new TMDB data)
   - Click "Generate JSON"
   - Click "Preview JSON" to verify
   - Click "Publish to S3" to go live

5. **Backup**: Automatic with every save

## Data Flow

```
movies_master.xlsx (Source)
        ↓
   [Enrichment] ← TMDB API
        ↓
   [JSON Generation] ← utils.parse_ott_list()
        ↓
   data/*.json (Local)
        ↓
   [S3 Upload] (Optional)
        ↓
   CloudFront CDN → Public Website
```

## Validation Rules

### Must Have Before Publishing:
| Field | Requirement | Example |
|-------|-------------|---------|
| Title | Required | "Akhanda 2" |
| Status | Must be "published" | published |
| Language | Optional | Tamil, Telugu, Hindi |
| Region | Optional | India, US |
| OTT | At least 1 platform | Netflix, Prime Video |
| Rating | Must be > 0 | 7.5, 8 |

### Allowed OTT Platforms:
- Netflix
- Prime Video (Amazon)
- Disney+ Hotstar
- ZEE5
- SonyLIV
- SunNXT
- Aha

### Status Values:
| Status | Meaning | Public Display |
|--------|---------|---|
| published | Ready for public | ✅ Shows on site |
| review | Under editorial review | ❌ Hidden from public |
| draft | Work in progress | ❌ Hidden from public |

## API Reference

All endpoints are local-only (127.0.0.1:5000).

### Movies
- `GET /api/movies` - List movies with filters
- `PUT /api/movie/<id>` - Update single movie

### Pipeline
- `POST /api/pipeline/enrich` - Run enrichment
- `POST /api/pipeline/generate-json` - Generate JSON
- `GET /api/pipeline/preview` - Preview JSON
- `POST /api/pipeline/publish` - Upload to S3

### Backups
- `GET /api/backups` - List backups
- `POST /api/backups/<filename>/restore` - Restore backup

## Troubleshooting

### "Failed to load movies"
**Fix**: 
1. Ensure `movies_master.xlsx` exists in project root
2. Check that file is not locked/open in another program
3. Restart the dashboard

### "Enrichment failed"
**Check**:
1. TMDB API key configured in `config.py`
2. Internet connection working
3. TMDB API rate limits not exceeded

### "Publish to S3 failed"
**Verify**:
1. AWS credentials configured (`~/.aws/credentials`)
2. S3 bucket exists and is accessible
3. AWS region is correct
4. IAM permissions include `s3:PutObject`

### "Can't save movie without rating"
**Solution**: 
1. Edit movie and add rating > 0
2. Then save
3. Rating of 0 is invalid; must be 0.1 or higher

### Port 5000 already in use
**Fix**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Restart dashboard
./start-admin.sh
```

## Security

⚠️ **IMPORTANT**: The dashboard is **local-only** for security:

- ✅ Only accessible at `127.0.0.1:5000` (localhost)
- ✅ Not publicly accessible on the internet
- ✅ No authentication required (assumes trusted local use)
- ❌ Do NOT expose to public networks
- ❌ Do NOT use AWS keys that have broad permissions

### Best Practices:
1. Create AWS IAM user with **S3-only** permissions
2. Use bucket policies to restrict write access
3. Keep AWS credentials in `~/.aws/credentials` (never commit)
4. Use environment variables for secrets

## Configuration

### AWS S3 Publishing

Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### TMDB API Key

Edit `config.py`:
```python
TMDB_API_KEY = "your_api_key_here"
```

## Performance Tips

1. **Filter before editing**: Use search/filters to find specific movies
2. **Batch updates**: Edit multiple movies then publish once
3. **Backup before major changes**: Dashboard does this automatically
4. **Monitor backups**: Delete old backups monthly (admin/backups/)

## File Locations

| File | Purpose | Locked When |
|------|---------|---|
| `movies_master.xlsx` | Source of truth | Editing or generating JSON |
| `data/catalog.json` | All published movies | Generating or uploading |
| `data/upcoming-ott.json` | Upcoming releases | Generating or uploading |
| `admin/backups/*.xlsx` | Backup copies | (Never locked) |

## Support

For issues or questions:
1. Check Troubleshooting section above
2. Review logs in pipeline output
3. Check console for JavaScript errors (F12)
4. Verify Excel file not open in other programs

## Updates

To update admin dashboard dependencies:
```bash
cd /path/to/MoviesRecommendation
source admin/.venv/bin/activate  # or activate on Windows
pip install --upgrade -r admin/requirements.txt
```

---

**Dashboard Version**: 1.0  
**Last Updated**: 2024  
**Status**: Production Ready
