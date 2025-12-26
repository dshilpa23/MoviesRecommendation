# Admin Dashboard - Quick Start Card

## Launch Dashboard

### Linux / macOS:
```bash
./start-admin.sh
```

### Windows:
```cmd
start-admin.bat
```

**Then open**: http://127.0.0.1:5000

---

## 4 Main Tabs

### 1️⃣ Movies Grid
- View all movies in table
- **Search**: Find by title
- **Filter**: By status, language, region, completeness
- **Edit**: Click "Edit" button to update movie data
- **Save**: Auto-backup created before saving
- **Validation**: Can't publish without OTT + rating

### 2️⃣ Pipeline
**Run these in order:**
1. **Enrich** → Fetch TMDB data
2. **Generate JSON** → Export to public JSON files
3. **Preview** → See generated data
4. **Publish** → Upload to S3 (optional)

### 3️⃣ Backups
- Auto-backup on every save
- **Restore**: Click restore button to revert changes
- Located in: `admin/backups/`

### 4️⃣ Documentation
- Workflow guides
- Validation rules
- Configuration help

---

## Common Tasks

### Add a Movie to Catalog
1. Go to **Movies Grid**
2. Click **Edit** on movie
3. Set Status → "published"
4. Add OTT platforms (Netflix, Prime Video, etc.)
5. Add Rating (1-10)
6. Click **Save**
7. Go to **Pipeline** → **Generate JSON**
8. Click **Preview** to verify
9. Click **Publish** to go live

### Fix Incomplete Movie
1. **Movies Grid** → Filter "Missing Rating"
2. Click **Edit**
3. Add missing data (rating, OTT)
4. Click **Save**

### Undo Recent Changes
1. Go to **Backups**
2. Find backup from before changes
3. Click **Restore**
4. Confirm

### Update Public Website
1. **Pipeline** → **Run Enrichment** (optional)
2. **Pipeline** → **Generate JSON**
3. **Pipeline** → **Preview JSON**
4. **Pipeline** → **Publish to S3**

---

## Validation Rules

### Can't Publish Without:
- ❌ OTT Platform (Netflix, Prime Video, etc.)
- ❌ Rating > 0

### Allowed OTT Platforms:
- Netflix
- Prime Video
- Disney+ Hotstar
- ZEE5
- SonyLIV
- SunNXT
- Aha

### Status Values:
- **published** = Shows on website
- **review** = Hidden (under editorial review)
- **draft** = Hidden (work in progress)

---

## File Locations

| What | Where |
|------|-------|
| Web UI | http://127.0.0.1:5000 |
| Source data | `movies_master.xlsx` |
| Generated JSON | `data/` folder |
| Backups | `admin/backups/` |
| Config | `config.py` |

---

## Troubleshooting

**Port 5000 busy?**
```bash
lsof -i :5000
kill -9 <PID>
./start-admin.sh
```

**Excel file locked?**
- Close it in Excel before editing in dashboard

**Can't publish?**
- Check movie has rating > 0 and at least 1 OTT platform
- See error message in grid

**S3 upload fails?**
- Check AWS credentials in `~/.aws/credentials`
- Verify bucket exists
- Check IAM permissions

---

## Dashboard Structure

```
admin/
├── app.py                 ← Flask backend
├── requirements.txt       ← Dependencies
├── templates/admin.html   ← Web UI
├── static/
│   ├── admin.css         ← Styling
│   └── admin.js          ← Interactivity
├── utils/
│   ├── excel_handler.py  ← Excel read/write
│   ├── validation.py     ← Business rules
│   └── pipeline_runner.py ← Run pipelines
└── backups/              ← Auto-backups here
```

---

## Security Notes

✅ **Local-only**: Only accessible at 127.0.0.1:5000  
✅ **No auth needed**: Assumes trusted local environment  
❌ **Never expose publicly**: Don't share dashboard URL  
❌ **Keep AWS keys safe**: Use IAM user with S3-only access  

---

**Need Help?** See `ADMIN_GUIDE.md` for detailed documentation
