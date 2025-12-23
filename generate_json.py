"""
JSON Generator - Export UI-ready JSON from master spreadsheet
Generates section-specific JSON files with proper placeholders and normalization
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config import (
    MASTER_SHEET_PATH, DATA_DIR, REPORTS_DIR,
    JSON_OUTPUT_FILES, SEARCH_INDEX_FILE,
    STATUS_PUBLISHED, VALID_BUCKETS,
    PLACEHOLDER_POSTER, PLACEHOLDER_RATING,
    MIN_DESCRIPTION_LENGTH, MIN_POSTER_URL_LENGTH
)
from utils import parse_genres, parse_ott_list, validate_language


class JSONGenerator:
    """Generate UI-ready JSON files from master spreadsheet"""
    
    def __init__(self, sheet_path=MASTER_SHEET_PATH):
        self.sheet_path = sheet_path
        self.df = None
        self.report = {
            'generated_at': datetime.now().isoformat(),
            'total_in_sheet': 0,
            'published': 0,
            'files_generated': {},
            'quality_issues': {
                'missing_language': [],
                'missing_poster': [],
                'missing_description': [],
                'short_description': [],
                'missing_ott': [],
                'invalid_language_case': [],
                'low_confidence': [],
            },
            'editorial_stats': {
                'locked_descriptions': 0,
                'locked_posters': 0,
                'locked_ott': 0,
            },
            'warnings': []
        }
    
    def load_sheet(self):
        """Load master spreadsheet"""
        print(f"📂 Loading {self.sheet_path}...")
        self.df = pd.read_excel(self.sheet_path, engine='openpyxl')
        self.report['total_in_sheet'] = len(self.df)
        
        # Filter only published movies
        self.df = self.df[self.df['status'] == STATUS_PUBLISHED]
        self.report['published'] = len(self.df)
        
        print(f"   Total movies in sheet: {self.report['total_in_sheet']}")
        print(f"   Published movies: {self.report['published']}")
    
    def clean_for_ui(self, row: pd.Series) -> Dict:
        """Convert DataFrame row to UI-ready dict"""
        
        # Parse complex fields
        genres = parse_genres(row.get('genres', ''))
        ott_list = parse_ott_list(row.get('ottList', ''))
        
        # Get primary OTT (backward compatibility)
        primary_ott = row.get('primaryOtt', '')
        if pd.isna(primary_ott) or not primary_ott:
            primary_ott = ott_list[0] if ott_list else 'all'
        
        # Build clean dict
        movie = {
            'title': str(row.get('title', '')),
            'sourceUrl': str(row.get('sourceUrl', '')),
            'posterUrl': str(row.get('posterUrl', '')),
            'releaseDate': self._format_date(row.get('releaseDate')),
            'language': str(row.get('language', '')),
            'region': str(row.get('region', '')) if pd.notna(row.get('region')) else '',
            'ott': primary_ott,  # UI backward compat
            'ottList': ott_list,
            'genres': genres,
            'genre': genres,  # UI backward compat
            'description': str(row.get('description', '')) if pd.notna(row.get('description')) else '',
        }
        
        # Optional fields (only include if not null)
        if pd.notna(row.get('rating')) and row.get('rating'):
            movie['rating'] = float(row.get('rating'))
        
        if pd.notna(row.get('youtubeId')) and row.get('youtubeId'):
            movie['youtubeId'] = str(row.get('youtubeId'))
        
        if pd.notna(row.get('watchUrl')) and row.get('watchUrl'):
            movie['watchUrl'] = str(row.get('watchUrl'))
        
        return movie
    
    def _format_date(self, date_value) -> str:
        """Format date consistently"""
        if pd.isna(date_value) or not date_value:
            return ''
        if isinstance(date_value, str):
            return date_value
        try:
            return date_value.strftime('%Y-%m-%d')
        except:
            return str(date_value)
    
    def quality_check(self, row: pd.Series):
        """Perform quality checks and record issues"""
        title = row.get('title', 'Unknown')
        
        # Check language
        language = row.get('language', '')
        if not language or pd.isna(language):
            self.report['quality_issues']['missing_language'].append(title)
        else:
            # Check capitalization
            is_valid, normalized = validate_language(language)
            if not is_valid:
                self.report['quality_issues']['invalid_language_case'].append({
                    'title': title,
                    'current': language,
                    'should_be': normalized
                })
        
        # Check poster
        poster = row.get('posterUrl', '')
        if not poster or pd.isna(poster) or len(str(poster)) < MIN_POSTER_URL_LENGTH:
            self.report['quality_issues']['missing_poster'].append(title)
        
        # Check description
        description = row.get('description', '')
        if not description or pd.isna(description):
            self.report['quality_issues']['missing_description'].append(title)
        elif len(str(description)) < MIN_DESCRIPTION_LENGTH:
            self.report['quality_issues']['short_description'].append(title)
        
        # Check OTT
        ott_list = parse_ott_list(row.get('ottList', ''))
        primary_ott = row.get('primaryOtt', '')
        if not ott_list and (not primary_ott or primary_ott == 'all'):
            self.report['quality_issues']['missing_ott'].append(title)
        
        # Check confidence
        confidence = row.get('confidence', '')
        if confidence == 'low' or confidence == 'needs_review':
            self.report['quality_issues']['low_confidence'].append({
                'title': title,
                'confidence': confidence
            })
        
        # Track locks
        if row.get('descriptionLock') == True:
            self.report['editorial_stats']['locked_descriptions'] += 1
        if row.get('posterLock') == True:
            self.report['editorial_stats']['locked_posters'] += 1
        if row.get('ottLock') == True:
            self.report['editorial_stats']['locked_ott'] += 1
    
    def generate_bucket_file(self, bucket: str):
        """Generate JSON file for specific bucket"""
        filename = JSON_OUTPUT_FILES.get(bucket)
        if not filename:
            print(f"⚠️  No output file defined for bucket: {bucket}")
            return
        
        # Filter by bucket
        subset = self.df[self.df['bucket'] == bucket]
        
        if len(subset) == 0:
            print(f"   ⚠️  No movies found for bucket: {bucket}")
            return
        
        # Convert to UI format
        movies = []
        for _, row in subset.iterrows():
            self.quality_check(row)
            movie = self.clean_for_ui(row)
            movies.append(movie)
        
        # Save to file
        output_path = DATA_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(movies, f, indent=2, ensure_ascii=False)
        
        self.report['files_generated'][filename] = {
            'count': len(movies),
            'bucket': bucket,
            'path': str(output_path)
        }
        
        print(f"   ✅ {filename}: {len(movies)} movies")
    
    def generate_search_index(self):
        """Generate search index with minimal fields"""
        print(f"\n🔍 Generating search index...")
        
        search_movies = []
        for _, row in self.df.iterrows():
            search_movies.append({
                'title': str(row.get('title', '')),
                'language': str(row.get('language', '')),
                'releaseDate': self._format_date(row.get('releaseDate')),
                'genres': parse_genres(row.get('genres', '')),
                'bucket': str(row.get('bucket', '')),
            })
        
        output_path = DATA_DIR / SEARCH_INDEX_FILE
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(search_movies, f, ensure_ascii=False)
        
        self.report['files_generated'][SEARCH_INDEX_FILE] = {
            'count': len(search_movies),
            'type': 'search_index',
            'path': str(output_path)
        }
        
        print(f"   ✅ {SEARCH_INDEX_FILE}: {len(search_movies)} entries")
    
    def generate_report(self):
        """Generate and save quality report"""
        print(f"\n📊 Quality Report:")
        
        # Add warnings
        issues = self.report['quality_issues']
        
        if issues['missing_language']:
            count = len(issues['missing_language'])
            self.report['warnings'].append(f"{count} movies missing language")
            print(f"   ⚠️  {count} movies missing language")
        
        if issues['invalid_language_case']:
            count = len(issues['invalid_language_case'])
            self.report['warnings'].append(f"{count} movies with incorrect language capitalization")
            print(f"   ⚠️  {count} movies with incorrect language capitalization")
            for item in issues['invalid_language_case'][:5]:  # Show first 5
                print(f"      - {item['title']}: '{item['current']}' → '{item['should_be']}'")
        
        if issues['missing_poster']:
            count = len(issues['missing_poster'])
            self.report['warnings'].append(f"{count} movies missing poster")
            print(f"   ⚠️  {count} movies missing poster")
        
        if issues['missing_description']:
            count = len(issues['missing_description'])
            self.report['warnings'].append(f"{count} movies missing description")
            print(f"   ⚠️  {count} movies missing description")
        
        if issues['missing_ott']:
            count = len(issues['missing_ott'])
            self.report['warnings'].append(f"{count} movies missing OTT platform")
            print(f"   ⚠️  {count} movies missing OTT platform")
        
        if issues['low_confidence']:
            count = len(issues['low_confidence'])
            self.report['warnings'].append(f"{count} movies need review (low confidence)")
            print(f"   ⚠️  {count} movies need review (low confidence)")
        
        # Save report
        report_filename = f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = REPORTS_DIR / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved: {report_path}")
    
    def generate_all(self):
        """Generate all JSON files"""
        print("\n🚀 Starting JSON generation...\n")
        
        # Load sheet
        self.load_sheet()
        
        # Generate bucket files
        print(f"\n📦 Generating bucket files...")
        for bucket in VALID_BUCKETS:
            self.generate_bucket_file(bucket)
        
        # Generate search index
        self.generate_search_index()
        
        # Generate report
        self.generate_report()
        
        print(f"\n✅ JSON generation complete!")
        print(f"   Files generated: {len(self.report['files_generated'])}")
        print(f"   Total movies exported: {self.report['published']}")


def main():
    generator = JSONGenerator()
    generator.generate_all()


if __name__ == '__main__':
    main()
