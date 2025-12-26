"""
Pipeline Runner - Execute enrichment, JSON generation, and publishing
"""

import subprocess
import json
from pathlib import Path


class PipelineRunner:
    """Run pipeline commands and capture results"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.venv_python = self.project_root / '.venv' / 'bin' / 'python'
    
    def run_enrichment(self):
        """Run enrich_existing_tmdb.py"""
        try:
            script = self.project_root / 'enrich_existing_tmdb.py'
            
            # Run with no user input (dry-run mode)
            result = subprocess.run(
                [str(self.venv_python), str(script)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': 'Enrichment timeout (5 minutes)'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def run_json_generation(self):
        """Run generate_json.py"""
        try:
            script = self.project_root / 'generate_json.py'
            
            result = subprocess.run(
                [str(self.venv_python), str(script)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': 'JSON generation timeout (1 minute)'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_preview(self):
        """Get preview of generated JSON files"""
        try:
            preview = {}
            
            json_files = {
                'upcoming': self.project_root / 'data' / 'upcoming-ott.json',
                'new': self.project_root / 'data' / 'ott-releases.json',
                'best': self.project_root / 'data' / 'best-india.json',
            }
            
            for key, filepath in json_files.items():
                if filepath.exists():
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        preview[key] = {
                            'count': len(data),
                            'sample': data[:2] if data else []
                        }
            
            return preview
        except Exception as e:
            return {'error': str(e)}
    
    def publish_to_s3(self, bucket, region='us-east-1'):
        """Publish JSON files to S3
        
        Requires AWS credentials configured
        """
        try:
            import boto3
            
            s3 = boto3.client('s3', region_name=region)
            
            json_files = {
                'upcoming': self.project_root / 'data' / 'upcoming-ott.json',
                'new': self.project_root / 'data' / 'ott-releases.json',
                'best': self.project_root / 'data' / 'best-india.json',
                'search': self.project_root / 'data' / 'search-index.json',
            }
            
            uploaded = []
            for key, filepath in json_files.items():
                if filepath.exists():
                    s3.upload_file(
                        str(filepath),
                        bucket,
                        f'data/{filepath.name}',
                        ExtraArgs={'ContentType': 'application/json', 'CacheControl': 'max-age=300'}
                    )
                    uploaded.append(filepath.name)
            
            return {
                'status': 'success',
                'bucket': bucket,
                'files_uploaded': uploaded,
                'count': len(uploaded)
            }
        except ImportError:
            return {'status': 'error', 'message': 'boto3 not installed. Install with: pip install boto3'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
