"""
Validation Engine - Enforce business rules for movie records
"""

import pandas as pd


class ValidationEngine:
    """Validate movie data against business rules"""
    
    ALLOWED_PLATFORMS = {'prime video', 'netflix', 'disney+ hotstar', 'zee5', 'sonyliv', 'sunnxt', 'aha'}
    ALLOWED_STATUSES = {'published', 'review', 'draft'}
    
    def validate_movie(self, movie_data):
        """Validate a single movie record
        
        Args: movie_data should use Excel column names (releaseDate, ottList, etc.)
        Returns: list of error messages (empty if valid)
        """
        errors = []
        
        # Rule 1: If status is 'published', must have OTT
        if movie_data.get('status') == 'published':
            ott = movie_data.get('ottList', '')
            
            if not ott or ott == '[]' or (isinstance(ott, str) and not ott.strip()):
                errors.append('PUBLISH_BLOCKED: Missing OTT platform. Add OTT before publishing.')
        
        # Rule 2: If status is 'published', must have rating > 0
        if movie_data.get('status') == 'published':
            rating = movie_data.get('rating')
            
            try:
                rating_val = float(rating) if rating else 0
            except (ValueError, TypeError):
                rating_val = 0
            
            if rating_val <= 0:
                errors.append('PUBLISH_BLOCKED: Missing or zero rating. Add rating before publishing.')
        
        # Rule 3: Status must be valid
        status = movie_data.get('status', '').lower()
        if status and status not in self.ALLOWED_STATUSES:
            errors.append(f'Invalid status: {status}. Allowed: {", ".join(self.ALLOWED_STATUSES)}')
        
        return errors
    
    def can_publish(self, movie_data):
        """Check if movie can be published"""
        errors = self.validate_movie({**movie_data, 'status': 'published'})
        return len(errors) == 0, errors
