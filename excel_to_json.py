import json
import os
import pandas as pd
from urllib.parse import urlparse, parse_qs

INPUT_XLSX = "movies.xlsx"
SHEET = "movies"
OUT_DIR = "data"

def norm(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    return s if s else None

def extract_youtube_id(value):
    v = norm(value)
    if not v:
        return None
    if "://" not in v:
        return v
    try:
        parsed = urlparse(v)
    except Exception:
        return v
    if "youtu.be" in parsed.netloc:
        return parsed.path.lstrip("/") or None
    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        return vid or None
    return v

def norm_lower(s):
    v = norm(s)
    return v.lower() if v else None

def map_category(s):
    v = norm_lower(s)
    if not v:
        return None
    if v in ("best india", "best-india", "best_india"):
        return "best"
    return v

def split_genre(s):
    s = norm(s)
    if not s:
        return []
    return [g.strip() for g in s.split(",") if g.strip()]

def split_list(s):
    s = norm(s)
    if not s:
        return []
    return [item.strip() for item in s.split(",") if item.strip()]

def safe_float(x):
    if pd.isna(x) or x is None or str(x).strip() == "":
        return None
    try:
        return float(x)
    except Exception:
        return None

def prune_obj(d):
    cleaned = {k: v for k, v in d.items() if v not in (None, "", [], {})}
    return cleaned if cleaned else None

def row_to_movie(r):
    youtube_id = extract_youtube_id(r.get("youtubeId")) or extract_youtube_id(r.get("youtubeld"))
    poster_url = None
    if youtube_id:
        poster_url = f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg"

    hotstar = prune_obj({
        "market": norm(r.get("hotstarMarket")),
        "type": norm(r.get("hotstarType")),
        "slug": norm(r.get("hotstarSlug")),
        "id": norm(r.get("hotstarId")),
    })

    zee5 = prune_obj({
        "market": norm(r.get("zee5Market")),
        "type": norm(r.get("zee5Type")),
        "slug": norm(r.get("zee5Slug")),
        "id": norm(r.get("zee5Id")),
    })

    movie = {
        "title": norm(r.get("title")),
        "region": norm_lower(r.get("region")),
        "language": norm_lower(r.get("language")),
        "category": map_category(r.get("category")),        # best/new/upcoming
        "releaseType": norm_lower(r.get("releaseType")),    # ott/theatrical
        "ott": norm_lower(r.get("ott")),
        # "watchUrl": norm(r.get("watchUrl")),
        # "watchLink": norm(r.get("watchLink")),
        # "netflixTitleId": norm(r.get("netflixTitleId")),
        "ottList": split_list(r.get("ottList")),
        "hotstar": hotstar,
        "zee5": zee5,
        "releaseDate": norm(r.get("releaseDate")),
        "rating": safe_float(r.get("rating")),
        "audience": norm(r.get("audience")),
        "genre": split_genre(r.get("genre")),
        "description": norm(r.get("description")),
        "poster": norm(r.get("poster")),
        "posterUrl": poster_url,
        "youtubeId": youtube_id,
    }

    # drop null/empty fields (keeps JSON clean)
    movie = {k: v for k, v in movie.items() if v not in (None, "", [], {})}
    return movie

def write_json(filename, items):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print("Wrote:", path, "items:", len(items))

def main():
    try:
        df = pd.read_excel(INPUT_XLSX, sheet_name=SHEET)
    except Exception as e:
        print(f"Error reading sheet '{SHEET}': {e}")
        print("\nAvailable sheets:")
        xls = pd.ExcelFile(INPUT_XLSX)
        print(xls.sheet_names)
        return

    df.columns = [c.strip() for c in df.columns]
    movies = [row_to_movie(r) for r in df.to_dict(orient="records")]

    upcoming_ott = [m for m in movies if m.get("category") == "upcoming" and m.get("releaseType") == "ott"]
    new_ott = [m for m in movies if m.get("category") == "new" and m.get("releaseType") == "ott"]
    # upcoming_theatrical = [m for m in movies if m.get("category") == "upcoming" and m.get("releaseType") == "theatrical"]
    best_india = [m for m in movies if m.get("category") == "best" and m.get("region") == "india"]


    write_json("upcoming-ott.json", upcoming_ott)
    write_json("ott-releases.json", new_ott)
    # write_json("upcoming-theatrical.json", upcoming_theatrical)
    write_json("best-india.json", best_india)

if __name__ == "__main__":
    main()
