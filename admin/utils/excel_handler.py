"""
Excel Handler - Read/write movies_master.xlsx with validation
"""

import pandas as pd
from pathlib import Path


class ExcelHandler:
    """Handle Excel operations for movies master sheet"""
    
    def __init__(self, excel_path):
        self.excel_path = Path(excel_path)
    
    def read_all(self):
        """Read entire Excel file"""
        return pd.read_excel(self.excel_path)
    
    def update_movie(self, row_index, data):
        """Update a single movie record"""
        df = self.read_all()
        
        # Update row with provided data
        for col, value in data.items():
            if col in df.columns:
                df.at[row_index, col] = value
        
        # Write back to Excel
        df.to_excel(self.excel_path, index=False)
        
        return {'rows_updated': 1, 'fields_updated': len(data)}
    
    def bulk_update(self, updates):
        """Bulk update multiple movies
        
        updates: list of {'index': int, 'data': dict}
        """
        df = self.read_all()
        
        total_fields = 0
        for update in updates:
            row_index = update['index']
            data = update['data']
            
            for col, value in data.items():
                if col in df.columns:
                    df.at[row_index, col] = value
                    total_fields += 1
        
        # Write back to Excel
        df.to_excel(self.excel_path, index=False)
        
        return {
            'rows_updated': len(updates),
            'fields_updated': total_fields
        }
    
    def get_column_stats(self):
        """Get statistics about data completeness"""
        df = self.read_all()
        
        stats = {
            'total_rows': len(df),
            'missing_by_field': {}
        }
        
        for col in df.columns:
            missing = df[col].isna().sum() + (df[col] == '').sum()
            stats['missing_by_field'][col] = {
                'missing': int(missing),
                'percentage': round(missing / len(df) * 100, 1)
            }
        
        return stats
