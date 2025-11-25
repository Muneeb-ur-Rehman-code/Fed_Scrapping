"""Main script for Federal Reserve FEDS papers scraper"""

import sys
import json
import time
from pathlib import Path
from scrapers.fed_scraper import FedScraper
from utils.csv_writer import CSVWriter
from utils.excel_writer import ExcelWriter
from utils.author_analyzer import AuthorAnalyzer
from utils.dependencies import validate_dependencies


def load_config():
    """Load configuration from config.json"""
    config_file = Path('config.json')
    
    if not config_file.exists():
        print("❌ ERROR: config.json not found!")
        print("Please ensure config.json exists in the project root.")
        sys.exit(1)
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print("✅ Loaded configuration from config.json")
        return config
    except Exception as e:
        print(f"❌ ERROR: Could not load config.json: {str(e)}")
        sys.exit(1)


def get_year_range():
    """Get year range from user input"""
    print("\n" + "="*60)
    print("🎯 FEDERAL RESERVE PAPERS SCRAPER")
    print("="*60 + "\n")
    
    print("📅 Enter year range to scrape (1996-2025)")
    print("   Examples: '2020-2025' or '1996-2000'")
    
    while True:
        year_input = input("\n🔹 Year range (YYYY-YYYY): ").strip()
        
        try:
            if '-' not in year_input:
                print("❌ Invalid format. Please use YYYY-YYYY format.")
                continue
            
            parts = year_input.split('-')
            if len(parts) != 2:
                print("❌ Invalid format. Please use YYYY-YYYY format.")
                continue
            
            start_year = int(parts[0].strip())
            end_year = int(parts[1].strip())
            
            if start_year < 1996 or end_year > 2025:
                print("⚠️  Years should be between 1996 and 2025")
                continue
            
            if start_year > end_year:
                print("❌ Start year cannot be greater than end year")
                continue
            
            print(f"\n✅ Will scrape papers from {start_year} to {end_year}")
            return start_year, end_year
            
        except ValueError:
            print("❌ Invalid year format. Please enter valid years.")
            continue


def main():
    """Main execution function"""
    
    try:
        # Validate dependencies
        print("🔧 Checking dependencies...\n")
        if not validate_dependencies():
            sys.exit(1)
        
        # Load config
        config = load_config()
        
        # Get user input
        start_year, end_year = get_year_range()
        
        # Configuration
        output_dir = config['scraper_settings']['output_dir']
        headless_mode = config['scraper_settings']['headless_mode']
        debug_mode = config['scraper_settings']['debug_mode']
        csv_output = config['scraper_settings']['csv_output']
        excel_output = config['scraper_settings']['excel_output']
        
        print("\n" + "="*60)
        print("🚀 Starting scraper...")
        print(f"   Year Range: {start_year}-{end_year}")
        print(f"   Output Directory: {output_dir}/")
        print(f"   Headless: {headless_mode}")
        print(f"   Debug: {debug_mode}")
        print("="*60 + "\n")
        
        # Initialize components
        scraper = FedScraper(headless=headless_mode, debug=debug_mode, config=config)
        csv_writer = CSVWriter(output_dir=output_dir)
        excel_writer = ExcelWriter(output_dir=output_dir)
        author_analyzer = AuthorAnalyzer(config=config)
        
        # Get existing FEDS numbers to avoid duplicates
        existing_feds_numbers = csv_writer.get_existing_feds_numbers()
        
        all_papers = []
        total_scraped = 0
        
        try:
            # Setup driver
            scraper.setup_driver()
            
            # Scrape papers year by year
            for year, year_papers in scraper.scrape_years_range(start_year, end_year, existing_feds_numbers):
                if year_papers:
                    # Save incrementally after each year
                    if csv_output:
                        csv_writer.save_papers(year_papers, mode='append')
                    
                    all_papers.extend(year_papers)
                    total_scraped += len(year_papers)
                    
                    print(f"\n💾 Saved {len(year_papers)} papers from year {year}")
                    print(f"📊 Total papers scraped so far: {total_scraped}")
            
            # Process author analytics
            if all_papers:
                print("\n" + "="*60)
                print("📈 GENERATING RESEARCHER ANALYTICS")
                print("="*60)
                
                author_analyzer.process_papers(all_papers)
                analytics_data = author_analyzer.generate_analytics()
                ambiguous_pairs = author_analyzer.get_ambiguous_pairs()
                
                # Save analytics
                if csv_output:
                    csv_writer.save_researcher_analytics(analytics_data)
                    if ambiguous_pairs:
                        csv_writer.save_ambiguous_authors(ambiguous_pairs)
                
                # Create Excel file
                if excel_output:
                    print("\n📊 Creating Excel file...")
                    excel_writer.save_to_excel()
            
            # Final summary
            print("\n" + "="*60)
            print("🎉 SCRAPING COMPLETED!")
            print("="*60)
            print(f"📊 Total papers scraped: {total_scraped}")
            print(f"📁 Output directory: {output_dir}/")
            
            if csv_output:
                print(f"   ✅ CSV files saved")
            if excel_output:
                print(f"   ✅ Excel file created: fed_papers_data.xlsx")
            
            if ambiguous_pairs:
                print(f"\n⚠️  {len(ambiguous_pairs)} author pairs need manual review")
                print(f"   See: {output_dir}/ambiguous_authors_review.csv")
            
            print("="*60 + "\n")
            
        finally:
            # Always close browser
            scraper.close()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()