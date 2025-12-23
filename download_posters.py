"""
Download movie posters locally to avoid external image calls
Updates posterUrl in spreadsheet to local paths
"""

import pandas as pd
import requests
from pathlib import Path
from urllib.parse import urlparse
import time
from datetime import datetime

from config import MASTER_SHEET_PATH

# Create images directory
IMAGES_DIR = Path(__file__).parent / "images" / "posters"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Also create placeholder
PLACEHOLDER_DIR = Path(__file__).parent / "images"
PLACEHOLDER_DIR.mkdir(exist_ok=True)


def download_image(url: str, movie_id: str, retries=3) -> str:
    """
    Download image from URL to local directory
    
    Returns:
        Local path relative to project root (images/posters/...)
        or empty string if failed
    """
    if not url or pd.isna(url) or url == "":
        return ""
    
    try:
        # Parse URL to get extension
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix or '.jpg'
        
        # Create local filename
        safe_id = movie_id.replace('/', '_').replace('\\', '_')
        local_filename = f"{safe_id}{ext}"
        local_path = IMAGES_DIR / local_filename
        
        # Skip if already downloaded
        if local_path.exists():
            print(f"  ⏭️  Already exists: {local_filename}")
            return f"images/posters/{local_filename}"
        
        # Download with retries
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10, stream=True)
                response.raise_for_status()
                
                # Save image
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  ✅ Downloaded: {local_filename}")
                return f"images/posters/{local_filename}"
                
            except Exception as e:
                if attempt < retries - 1:
                    print(f"  ⚠️  Retry {attempt + 1}/{retries}: {movie_id}")
                    time.sleep(2)
                else:
                    print(f"  ❌ Failed: {movie_id} - {e}")
                    return ""
    
    except Exception as e:
        print(f"  ❌ Error: {movie_id} - {e}")
        return ""


def create_placeholder_image():
    """Create a simple placeholder image if none exists"""
    placeholder_path = PLACEHOLDER_DIR / "placeholder.jpg"
    
    if placeholder_path.exists():
        print("✅ Placeholder already exists")
        return
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create 300x450 gray placeholder
        img = Image.new('RGB', (300, 450), color=(60, 60, 60))
        draw = ImageDraw.Draw(img)
        
        # Draw text
        text = "No Poster\nAvailable"
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        position = ((300 - text_width) // 2, (450 - text_height) // 2)
        draw.text(position, text, fill=(200, 200, 200), align='center')
        
        img.save(placeholder_path, 'JPEG')
        print(f"✅ Created placeholder: {placeholder_path}")
        
    except ImportError:
        print("⚠️  Pillow not installed. Install with: pip install Pillow")
        print("   Creating empty placeholder file instead")
        placeholder_path.touch()


def download_all_posters():
    """Download all posters from spreadsheet"""
    print("🚀 Starting poster download...\n")
    
    # Load spreadsheet
    print(f"📂 Loading {MASTER_SHEET_PATH}...")
    df = pd.read_excel(MASTER_SHEET_PATH, engine='openpyxl')
    print(f"   Found {len(df)} movies\n")
    
    # Stats
    stats = {
        'total': len(df),
        'downloaded': 0,
        'skipped': 0,
        'failed': 0,
        'already_local': 0,
    }
    
    # Process each movie
    print("📥 Downloading posters...\n")
    
    for idx, row in df.iterrows():
        movie_id = row.get('movieId', f'movie_{idx}')
        title = row.get('title', 'Unknown')
        poster_url = row.get('posterUrl', '')
        
        # Skip if already local path
        if poster_url.startswith('images/'):
            stats['already_local'] += 1
            continue
        
        # Skip if empty
        if not poster_url or pd.isna(poster_url):
            stats['skipped'] += 1
            continue
        
        print(f"[{idx + 1}/{len(df)}] {title[:40]}...")
        
        # Download
        local_path = download_image(poster_url, movie_id)
        
        if local_path:
            # Update DataFrame
            df.at[idx, 'posterUrl'] = local_path
            df.at[idx, 'posterLock'] = True  # Lock to prevent re-download
            stats['downloaded'] += 1
        else:
            stats['failed'] += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save updated spreadsheet
    print(f"\n💾 Saving updated spreadsheet...")
    df.to_excel(MASTER_SHEET_PATH, index=False, engine='openpyxl')
    print(f"✅ Saved!\n")
    
    # Print stats
    print(f"📊 Download Summary:")
    print(f"   Total movies: {stats['total']}")
    print(f"   Downloaded: {stats['downloaded']}")
    print(f"   Already local: {stats['already_local']}")
    print(f"   Skipped (no URL): {stats['skipped']}")
    print(f"   Failed: {stats['failed']}")
    
    # Create placeholder
    print(f"\n🖼️  Creating placeholder...")
    create_placeholder_image()
    
    print(f"\n✅ Complete! Run generate_json.py to update UI files.")


if __name__ == '__main__':
    download_all_posters()
