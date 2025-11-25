"""Excel writer utility for saving scraped data"""

import pandas as pd
from pathlib import Path
import json


class ExcelWriter:
    """Handle Excel file operations for scraped data"""
    
    def __init__(self, output_dir="data"):
        """Initialize Excel writer"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_to_excel(self, papers_file="feds_papers_complete.csv", 
                      analytics_file="researcher_analytics.csv",
                      ambiguous_file="ambiguous_authors_review.csv",
                      output_file="fed_papers_data.xlsx"):
        """Convert CSV files to Excel with multiple sheets"""
        
        try:
            output_path = self.output_dir / output_file
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Papers sheet
                papers_csv = self.output_dir / papers_file
                if papers_csv.exists():
                    df_papers = pd.read_csv(papers_csv)
                    df_papers.to_excel(writer, sheet_name='Papers', index=False)
                    print(f"  📊 Added {len(df_papers)} papers to Excel")
                
                # Researcher analytics sheet
                analytics_csv = self.output_dir / analytics_file
                if analytics_csv.exists():
                    df_analytics = pd.read_csv(analytics_csv)
                    # Parse JSON string back to readable format
                    if 'papers_by_year' in df_analytics.columns:
                        df_analytics['papers_by_year'] = df_analytics['papers_by_year'].apply(
                            lambda x: str(json.loads(x) if x and x != '' else {})
                        )
                    df_analytics.to_excel(writer, sheet_name='Researcher Analytics', index=False)
                    print(f"  📊 Added analytics for {len(df_analytics)} researchers to Excel")
                
                # Ambiguous authors sheet
                ambiguous_csv = self.output_dir / ambiguous_file
                if ambiguous_csv.exists():
                    df_ambiguous = pd.read_csv(ambiguous_csv)
                    df_ambiguous.to_excel(writer, sheet_name='Authors Review', index=False)
                    print(f"  📊 Added {len(df_ambiguous)} ambiguous author pairs to Excel")
            
            print(f"\n✅ Excel file saved: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating Excel file: {str(e)}")
            return False