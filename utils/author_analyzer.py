"""Author name canonicalization and analytics"""

import json
import re
from collections import defaultdict, Counter
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


class AuthorAnalyzer:
    """Analyze and canonicalize author names"""
    
    def __init__(self, config=None):
        """Initialize analyzer"""
        self.config = config or {}
        self.auto_match_threshold = config.get('author_matching', {}).get('auto_match_threshold', 95)
        self.review_min = config.get('author_matching', {}).get('review_threshold_min', 80)
        self.review_max = config.get('author_matching', {}).get('review_threshold_max', 95)
        
        self.canonical_names = {}  # Map variations to canonical names
        self.author_papers = defaultdict(list)  # Map canonical names to papers
        self.ambiguous_pairs = []  # Pairs needing manual review
    
    def normalize_name(self, name):
        """Basic normalization of author name"""
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Standardize initials (P.A. -> P. A.)
        name = re.sub(r'([A-Z])\.([A-Z])', r'\1. \2', name)
        
        # Remove trailing dots from single initials
        name = re.sub(r'\b([A-Z])\.\s*', r'\1. ', name)
        
        return name.strip()
    
    def get_canonical_name(self, name):
        """Get or create canonical version of author name"""
        normalized = self.normalize_name(name)
        
        # Check if already mapped
        if normalized in self.canonical_names:
            return self.canonical_names[normalized]
        
        # Check for fuzzy matches with existing canonical names
        canonical_list = list(set(self.canonical_names.values()))
        
        if canonical_list:
            # Find best match
            best_match, score = process.extractOne(normalized, canonical_list, scorer=fuzz.token_set_ratio)
            
            if score >= self.auto_match_threshold:
                # Automatic match
                self.canonical_names[normalized] = best_match
                return best_match
            elif self.review_min <= score < self.review_max:
                # Needs review
                self.ambiguous_pairs.append({
                    'author1': normalized,
                    'author2': best_match,
                    'similarity_score': score,
                    'matching_confidence': 'Medium',
                    'action_needed': 'Manual Review'
                })
                # For now, treat as separate author
                self.canonical_names[normalized] = normalized
                return normalized
            else:
                # Different authors
                self.canonical_names[normalized] = normalized
                return normalized
        else:
            # First author
            self.canonical_names[normalized] = normalized
            return normalized
    
    def process_papers(self, papers):
        """Process all papers and build author analytics"""
        print("\n👥 Processing author data...")
        
        # Process each paper
        for paper in papers:
            if not paper.get('authors'):
                continue
            
            # Split authors (handle 'and' and commas)
            authors_text = paper['authors']
            authors_text = re.sub(r'\s+and\s+', ', ', authors_text)
            authors = [a.strip() for a in authors_text.split(',') if a.strip()]
            
            for author in authors:
                canonical = self.get_canonical_name(author)
                
                self.author_papers[canonical].append({
                    'feds_number': paper.get('feds_number', ''),
                    'year': paper.get('year', 0),
                    'title': paper.get('title', ''),
                    'jel_codes': paper.get('jel_codes', ''),
                    'field_category': paper.get('field_category', '')
                })
        
        print(f"  ✅ Processed {len(self.canonical_names)} unique author variations")
        print(f"  ✅ Identified {len(self.author_papers)} canonical authors")
        if self.ambiguous_pairs:
            print(f"  ⚠️  {len(self.ambiguous_pairs)} author pairs need manual review")
    
    def generate_analytics(self):
        """Generate analytics for each author"""
        analytics_data = []
        
        for canonical_name, papers in self.author_papers.items():
            if not papers:
                continue
            
            # Calculate metrics
            years = [p['year'] for p in papers if p['year']]
            papers_by_year = Counter(years)
            
            # Get fields and JEL codes (currently empty)
            fields = []
            jel_codes = []
            
            analytics_data.append({
                'author_name': canonical_name,
                'total_papers': len(papers),
                'first_paper_year': min(years) if years else '',
                'latest_paper_year': max(years) if years else '',
                'papers_by_year': json.dumps(dict(papers_by_year)),
                'top_fields': '',  # Empty as requested
                'top_jel_codes': ''  # Empty as requested
            })
        
        # Sort by total papers descending
        analytics_data.sort(key=lambda x: x['total_papers'], reverse=True)
        
        return analytics_data
    
    def get_ambiguous_pairs(self):
        """Get list of ambiguous author pairs for review"""
        return self.ambiguous_pairs