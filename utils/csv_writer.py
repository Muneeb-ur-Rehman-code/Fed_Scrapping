"""CSV writer utility for saving scraped data"""

import csv
import os
from pathlib import Path


class CSVWriter:
    """Handle CSV file operations for scraped data"""
    
    def __init__(self, output_dir="data"):
        """Initialize CSV writer"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_existing_feds_numbers(self, filename="feds_papers_complete.csv"):
        """Get set of existing FEDS numbers from CSV"""
        filepath = self.output_dir / filename
        existing_numbers = set()
        
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('feds_number'):
                            existing_numbers.add(row['feds_number'])
                print(f"  📄 Found {len(existing_numbers)} existing papers in {filename}")
            except Exception as e:
                print(f"  ⚠️  Error reading existing CSV: {str(e)}")
        
        return existing_numbers
    
    def save_papers(self, papers, filename="feds_papers_complete.csv", mode='append'):
        """Save papers data to CSV"""
        if not papers:
            return
        
        filepath = self.output_dir / filename
        file_exists = filepath.exists()
        
        fieldnames = [
            'feds_number', 'year', 'publication_date', 'title', 
            'authors', 'jel_codes', 'field_category', 'paper_url',
            'abstract', 'source', 'scrape_timestamp', 'pdf_url'
        ]
        
        try:
            write_mode = 'a' if mode == 'append' and file_exists else 'w'
            
            with open(filepath, write_mode, encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if write_mode == 'w' or not file_exists:
                    writer.writeheader()
                
                for paper in papers:
                    # Ensure all fields exist
                    for field in fieldnames:
                        if field not in paper:
                            paper[field] = ''
                    
                    writer.writerow(paper)
            
            print(f"  💾 Saved {len(papers)} papers to {filename}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error saving to CSV: {str(e)}")
            return False
    
    def save_researcher_analytics(self, analytics_data, filename="researcher_analytics.csv"):
        """Save researcher analytics to CSV"""
        if not analytics_data:
            return
        
        filepath = self.output_dir / filename
        
        fieldnames = [
            'author_name', 'total_papers', 'first_paper_year',
            'latest_paper_year', 'papers_by_year', 'top_fields', 'top_jel_codes'
        ]
        
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for author_data in analytics_data:
                    writer.writerow(author_data)
            
            print(f"  💾 Saved analytics for {len(analytics_data)} researchers to {filename}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error saving researcher analytics: {str(e)}")
            return False
    
    def save_ambiguous_authors(self, ambiguous_pairs, filename="ambiguous_authors_review.csv"):
        """Save ambiguous author pairs for manual review"""
        if not ambiguous_pairs:
            return
        
        filepath = self.output_dir / filename
        
        fieldnames = ['author1', 'author2', 'similarity_score', 'matching_confidence', 'action_needed']
        
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for pair in ambiguous_pairs:
                    writer.writerow(pair)
            
            print(f"  💾 Saved {len(ambiguous_pairs)} ambiguous author pairs for review to {filename}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error saving ambiguous authors: {str(e)}")
            return False