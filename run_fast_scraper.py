#!/usr/bin/env python3
"""
Fast scraper implementation for real-time frontend updates
Processes articles in batches and saves immediately to Supabase
"""

import sys
import os
sys.path.append('server')

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
import time
import concurrent.futures
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastScraper:
    def __init__(self):
        self.scraper = NewsScraper()
        self.storage = StorageIntegration()
        
    def process_source_batch(self, sources, batch_size=3):
        """Process sources in batches for faster processing"""
        logger.info(f"Processing {len(sources)} sources in batches of {batch_size}")
        
        total_saved = 0
        
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {[s['name'] for s in batch]}")
            
            # Process batch concurrently
            batch_articles = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_source = {
                    executor.submit(self.scraper.scrape_source, source['url'], source['name']): source
                    for source in batch
                }
                
                for future in concurrent.futures.as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        articles = future.result(timeout=30)  # 30 second timeout per source
                        if articles:
                            logger.info(f"✅ {source['name']}: {len(articles)} articles")
                            batch_articles.extend(articles[:10])  # Limit to 10 articles per source
                        else:
                            logger.warning(f"❌ {source['name']}: No articles found")
                    except Exception as e:
                        logger.error(f"❌ {source['name']}: Error - {str(e)}")
            
            # Save batch to database immediately
            if batch_articles:
                logger.info(f"Saving {len(batch_articles)} articles from batch...")
                success = self.storage.save_scraped_articles(batch_articles)
                if success:
                    total_saved += len(batch_articles)
                    logger.info(f"✅ Saved {len(batch_articles)} articles to database")
                else:
                    logger.error(f"❌ Failed to save batch articles")
            
            # Small delay between batches
            time.sleep(1)
        
        return total_saved
    
    def run_fast_scrape(self):
        """Run fast scraper with real-time updates"""
        logger.info("Starting FAST scraper with real-time updates...")
        
        # Get working sources
        working_sources = [
            {'name': 'BBC News', 'url': 'https://www.bbc.com/news'},
            {'name': 'Ars Technica', 'url': 'https://arstechnica.com'},
            {'name': 'TechCrunch', 'url': 'https://techcrunch.com'},
            {'name': 'Hacker News', 'url': 'https://news.ycombinator.com'},
            {'name': 'India Today', 'url': 'https://www.indiatoday.in'},
            {'name': 'The Hindu', 'url': 'https://www.thehindu.com'},
            {'name': 'NDTV', 'url': 'https://www.ndtv.com'},
            {'name': 'Reuters', 'url': 'https://www.reuters.com'},
            {'name': 'CNN', 'url': 'https://www.cnn.com'},
        ]
        
        start_time = time.time()
        
        # Process in batches for faster updates
        total_saved = self.process_source_batch(working_sources, batch_size=3)
        
        # Update scraper last run
        self.storage.update_scraper_last_run()
        
        end_time = time.time()
        
        logger.info(f"🎉 FAST scraper completed!")
        logger.info(f"   Total time: {end_time - start_time:.2f} seconds")
        logger.info(f"   Articles saved: {total_saved}")
        logger.info(f"   Sources processed: {len(working_sources)}")
        logger.info(f"   Average per source: {total_saved / len(working_sources):.1f} articles")
        
        return total_saved

def main():
    """Main function to run fast scraper"""
    fast_scraper = FastScraper()
    total_articles = fast_scraper.run_fast_scrape()
    print(f"\n✅ Fast scraper completed successfully with {total_articles} articles!")
    
    return total_articles

if __name__ == "__main__":
    main()