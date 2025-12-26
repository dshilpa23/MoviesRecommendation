#!/usr/bin/env python3
"""
Local Admin Dashboard for MoviesRecommendation
Flask backend for editing Excel and running pipeline
"""

import os
import json
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import numpy as np

from utils.excel_handler import ExcelHandler
from utils.pipeline_runner import PipelineRunner
from utils.validation import ValidationEngine

# Initialize Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MASTER_SHEET = PROJECT_ROOT / 'movies_master.xlsx'
BACKUP_DIR = PROJECT_ROOT / 'admin' / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

# Initialize handlers
excel_handler = ExcelHandler(str(MASTER_SHEET))
pipeline = PipelineRunner(str(PROJECT_ROOT))
validator = ValidationEngine()

# Helper function to convert NaN to None for JSON serialization
def clean_value(val):
    """Convert pandas NaN/NaT to None for JSON serialization"""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (np.integer, np.floating)):
        return float(val) if isinstance(val, np.floating) else int(val)
    return val

# ============================================================================
# API: Dashboard Data
# ============================================================================

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Load all movies with optional filtering"""
    try:
        df = pd.read_excel(MASTER_SHEET)
        
        # Apply filters
        status = request.args.get('status')
        language = request.args.get('language')
        region = request.args.get('region')
        missing_ott = request.args.get('missing_ott') == 'true'
        missing_rating = request.args.get('missing_rating') == 'true'
        search = request.args.get('search', '').lower()
        
        if status and status != 'all':
            df = df[df['status'] == status]
        if language:
            df = df[df['language'] == language]
        if region:
            df = df[df['region'] == region]
        if missing_ott:
            df = df[(df['ottList'].isna()) | (df['ottList'] == '') | (df['ottList'] == '[]')]
        if missing_rating:
            df = df[(df['rating'].isna()) | (df['rating'] == '') | (df['rating'] == 0)]
        if search:
            df = df[df['title'].str.lower().str.contains(search, na=False)]
        
        # Convert to JSON with proper formatting
        movies = []
        for idx, row in df.iterrows():
            movie = {
                'id': int(idx),
                'title': clean_value(row.get('title', '')),
                'status': clean_value(row.get('status', 'draft')),
                'language': clean_value(row.get('language')),
                'region': clean_value(row.get('region')),
                'ott': [],
                'rating': clean_value(row.get('rating')),
                'release_date': clean_value(row.get('releaseDate')),
                'ottList': clean_value(row.get('ottList', ''))
            }
            
            # Parse ottList JSON string
            ott_str = row.get('ottList', '')
            if pd.notna(ott_str) and ott_str != '' and ott_str != '[]':
                try:
                    import ast
                    movie['ott'] = ast.literal_eval(str(ott_str))
                except:
                    movie['ott'] = []
            else:
                movie['ott'] = []
            
            # Ensure rating is a valid number
            if movie['rating'] is None:
                movie['rating'] = None
            elif isinstance(movie['rating'], (int, float)):
                movie['rating'] = float(movie['rating'])
            
            movies.append(movie)
        
        return jsonify({
            'success': True,
            'count': len(movies),
            'movies': movies
        })
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Get unique values for filter dropdowns"""
    try:
        df = pd.read_excel(MASTER_SHEET)
        
        return jsonify({
            'success': True,
            'statuses': sorted(df['status'].unique().tolist()),
            'languages': sorted(df['language'].unique().tolist()),
            'regions': sorted([r for r in df['region'].unique().tolist() if r])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API: Edit Movie
# ============================================================================

@app.route('/api/movie/<int:index>', methods=['PUT'])
def update_movie(index):
    """Update a single movie"""
    try:
        data = request.json
        
        # Map frontend field names to Excel column names
        excel_data = {}
        
        # Direct mappings
        if 'title' in data:
            excel_data['title'] = data['title']
        if 'language' in data:
            excel_data['language'] = data['language']
        if 'region' in data:
            excel_data['region'] = data['region']
        if 'status' in data:
            excel_data['status'] = data['status']
        if 'rating' in data:
            excel_data['rating'] = data['rating']
        
        # Map field name conversions
        if 'release_date' in data:
            excel_data['releaseDate'] = data['release_date']
        if 'ott' in data:
            # Convert list to JSON string
            import json
            excel_data['ottList'] = json.dumps(data['ott']) if data['ott'] else '[]'
        
        # Validate using the mapped Excel data
        validation_errors = validator.validate_movie(excel_data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'errors': validation_errors
            }), 400
        
        # Backup before modifying
        backup_file = _backup_excel()
        
        # Update Excel with mapped column names
        excel_handler.update_movie(index, excel_data)
        
        return jsonify({
            'success': True,
            'message': f'Movie updated. Backup: {Path(backup_file).name}'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API: Pipeline Operations
# ============================================================================

@app.route('/api/pipeline/enrich', methods=['POST'])
def enrich_movies():
    """Run enrichment pipeline"""
    try:
        backup_file = _backup_excel()
        
        result = pipeline.run_enrichment()
        
        return jsonify({
            'success': True,
            'message': 'Enrichment complete',
            'backup': Path(backup_file).name,
            'summary': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pipeline/generate-json', methods=['POST'])
def generate_json():
    """Generate JSON files from Excel"""
    try:
        backup_file = _backup_excel()
        
        result = pipeline.run_json_generation()
        
        return jsonify({
            'success': True,
            'message': 'JSON generated',
            'backup': Path(backup_file).name,
            'summary': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pipeline/preview', methods=['GET'])
def preview():
    """Preview generated JSON data"""
    try:
        preview_data = pipeline.get_preview()
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pipeline/publish', methods=['POST'])
def publish_to_s3():
    """Publish to S3 (optional)"""
    try:
        config = request.json
        s3_bucket = config.get('s3_bucket')
        aws_region = config.get('aws_region', 'us-east-1')
        
        result = pipeline.publish_to_s3(s3_bucket, aws_region)
        
        return jsonify({
            'success': True,
            'message': 'Published to S3',
            'summary': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API: Backups
# ============================================================================

@app.route('/api/backups', methods=['GET'])
def list_backups():
    """List all backup files"""
    try:
        backups = sorted(BACKUP_DIR.glob('*.xlsx'), key=os.path.getmtime, reverse=True)
        
        backup_list = [{
            'filename': b.name,
            'size_mb': round(b.stat().st_size / 1024 / 1024, 2),
            'modified': datetime.fromtimestamp(b.stat().st_mtime).isoformat()
        } for b in backups[:20]]
        
        return jsonify({
            'success': True,
            'backups': backup_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backups/<filename>/restore', methods=['POST'])
def restore_backup(filename):
    """Restore from backup"""
    try:
        backup_file = BACKUP_DIR / filename
        
        if not backup_file.exists():
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        # Create current backup before restoring
        _backup_excel()
        
        # Restore
        shutil.copy(backup_file, MASTER_SHEET)
        
        return jsonify({
            'success': True,
            'message': f'Restored from {filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Helper Functions
# ============================================================================

def _backup_excel():
    """Create timestamped backup of Excel file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'movies_master_{timestamp}.xlsx'
    shutil.copy(MASTER_SHEET, backup_file)
    return str(backup_file)


# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    """Serve admin dashboard"""
    return render_template('admin.html')


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'master_sheet': MASTER_SHEET.exists(),
        'project_root': str(PROJECT_ROOT)
    })


if __name__ == '__main__':
    print("="*80)
    print("LOCAL ADMIN DASHBOARD")
    print("="*80)
    print(f"\n✓ Master Sheet: {MASTER_SHEET}")
    print(f"✓ Backup Dir: {BACKUP_DIR}")
    print(f"\n🌐 Admin Dashboard: http://localhost:5000")
    print(f"\n⚠️  LOCAL ONLY - NOT PUBLICLY ACCESSIBLE\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
