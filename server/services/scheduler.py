import schedule
import time
import json
import logging
from datetime import datetime
from .scraper import NewsScraper, save_articles_to_json, load_sources_from_json
from .ai_rephraser import AIRephraser, save_rephrased_articles
from .storage_integration import StorageIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraperScheduler:
    def __init__(self):
        self.scraper = NewsScraper()
        self.rephraser = AIRephraser()
        self.storage = StorageIntegration()
        self.is_running = False
        
    def load_config(self) -> dict:
        """Load scraper configuration"""
        try:
            with open("scraper_config.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "interval_minutes": 20,
                "is_active": False,
                "last_run": None
            }
    
    def save_config(self, config: dict):
        """Save scraper configuration"""
        try:
            with open("scraper_config.json", 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def scrape_and_rephrase(self):
        """Main scraping and rephrasing job"""
        logger.info("Starting scheduled scrape and rephrase job")
        
        try:
            # Get active sources from storage
            sources = self.storage.get_active_sources()
            if not sources:
                logger.warning("No active sources configured")
                return
            
            # Scrape articles
            articles = self.scraper.scrape_all_sources(sources)
            if not articles:
                logger.warning("No articles scraped")
                return
            
            logger.info(f"Scraped {len(articles)} articles")
            
            # Save articles to storage
            if self.storage.save_scraped_articles(articles):
                logger.info("Successfully saved articles to storage")
            else:
                logger.error("Failed to save articles to storage")
                return
            
            # Process pending articles for rephrasing (optimized batch processing)
            pending_articles = self.storage.get_pending_articles()
            logger.info(f"Found {len(pending_articles)} pending articles for rephrasing")
            
            # Process in smaller batches for better performance
            batch_size = 10
            processed_count = 0
            
            for i in range(0, len(pending_articles), batch_size):
                batch = pending_articles[i:i + batch_size]
                
                for article in batch:
                    try:
                        # Update status to processing
                        self.storage.update_article_status(article['id'], 'processing')
                        
                        # Rephrase the article
                        rephrased_title = self.rephraser.rephrase_headline(
                            article['originalTitle'], 
                            article.get('sourceName', 'Unknown')
                        )
                        
                        if rephrased_title:
                            # Update with rephrased title
                            self.storage.update_article_status(
                                article['id'], 
                                'completed', 
                                rephrased_title
                            )
                            logger.info(f"Rephrased: {rephrased_title[:50]}...")
                        else:
                            # Mark as failed
                            self.storage.update_article_status(article['id'], 'failed')
                            logger.warning(f"Failed to rephrase: {article['originalTitle'][:50]}...")
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing article {article['id']}: {str(e)}")
                        self.storage.update_article_status(article['id'], 'failed')
                
                # Add a small delay between batches to avoid overwhelming the API
                if i + batch_size < len(pending_articles):
                    time.sleep(0.5)
            
            # Update last run time in storage and local config
            self.storage.update_scraper_last_run()
            config = self.load_config()
            config["last_run"] = datetime.now().isoformat()
            self.save_config(config)
            
            logger.info(f"Completed job: {len(articles)} articles scraped, {processed_count} processed")
            
        except Exception as e:
            logger.error(f"Error in scheduled job: {str(e)}")
    
    def start_scheduler(self):
        """Start the scheduler"""
        self.is_running = True
        logger.info("News scraper scheduler started")
        
        # Reset last run when starting to ensure fresh scrape
        config = self.load_config()
        config["last_run"] = None
        self.save_config(config)
        
        while self.is_running:
            config = self.load_config()
            
            if not config.get("is_active", False):
                logger.info("Scraper is not active, waiting...")
                time.sleep(60)  # Check every minute
                continue
            
            # Schedule the job
            interval = config.get("interval_minutes", 20)
            schedule.clear()
            schedule.every(interval).minutes.do(self.scrape_and_rephrase)
            
            # Run immediately if no last run
            if not config.get("last_run"):
                logger.info("Running initial scrape...")
                self.scrape_and_rephrase()
            
            # Run scheduled jobs
            while self.is_running and config.get("is_active", False):
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
                # Reload config to check for changes
                config = self.load_config()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("News scraper scheduler stopped")

if __name__ == "__main__":
    scheduler = NewsScraperScheduler()
    
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        scheduler.stop_scheduler()
