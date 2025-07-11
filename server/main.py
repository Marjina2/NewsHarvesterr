#!/usr/bin/env python3
import sys
import os
import json
import logging
from services.scheduler import NewsScraperScheduler
from services.scraper import NewsScraper, load_sources_from_json
from services.ai_rephraser import AIRephraser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_config(is_active: bool):
    """Update scraper configuration"""
    config = {
        "interval_minutes": 20,
        "is_active": is_active,
        "last_run": None
    }
    
    try:
        with open("scraper_config.json", 'r') as f:
            existing_config = json.load(f)
            config.update(existing_config)
    except FileNotFoundError:
        pass
    
    config["is_active"] = is_active
    
    with open("scraper_config.json", 'w') as f:
        json.dump(config, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [start|stop|test]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        logger.info("Starting news scraper service")
        update_config(True)
        scheduler = NewsScraperScheduler()
        scheduler.start_scheduler()
        
    elif command == "stop":
        logger.info("Stopping news scraper service")
        update_config(False)
        
    elif command == "test":
        logger.info("Testing scraper functionality")
        
        # Test scraping
        scraper = NewsScraper()
        sources = load_sources_from_json()
        articles = scraper.scrape_all_sources(sources)
        
        print(f"Scraped {len(articles)} articles")
        for article in articles[:3]:  # Show first 3
            print(f"- {article['title']}")
        
        # Test rephrasing
        if articles:
            rephraser = AIRephraser()
            rephrased = rephraser.rephrase_headline(articles[0]['title'], articles[0]['source'])
            print(f"\nOriginal: {articles[0]['title']}")
            print(f"Rephrased: {rephrased}")
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
