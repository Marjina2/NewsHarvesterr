#!/usr/bin/env python3
"""Test enhanced content extraction and save to Supabase"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_scraper():
    """Test with reliable sources and save to Supabase"""
    logger.info("Testing enhanced content extraction with reliable sources...")
    
    scraper = NewsScraper()
    storage = StorageIntegration()
    
    # Test with the most reliable sources
    test_sources = [
        {"name": "BBC News", "url": "https://www.bbc.com/news", "isActive": True},
        {"name": "Reuters", "url": "https://www.reuters.com", "isActive": True},
        {"name": "TechCrunch", "url": "https://techcrunch.com", "isActive": True},
        {"name": "The Guardian", "url": "https://www.theguardian.com", "isActive": True},
        {"name": "CNN", "url": "https://www.cnn.com", "isActive": True}
    ]
    
    logger.info(f"Testing with {len(test_sources)} reliable sources:")
    for source in test_sources:
        logger.info(f"  - {source['name']}")
    
    # Scrape articles
    logger.info("Starting enhanced scraping...")
    articles = scraper.scrape_all_sources(test_sources)
    
    if not articles:
        logger.error("No articles scraped!")
        return False
    
    logger.info(f"Successfully scraped {len(articles)} articles")
    
    # Analyze content quality
    enhanced_content_count = 0
    media_link_count = 0
    
    for article in articles:
        content = article.get('fullContent', '')
        if content and len(content) > 200:
            enhanced_content_count += 1
        
        if '[IMAGE:' in str(content) or '[VIDEO]' in str(content) or '[EMBEDDED]' in str(content):
            media_link_count += 1
    
    logger.info(f"Content quality analysis:")
    logger.info(f"  Articles with enhanced content: {enhanced_content_count}/{len(articles)}")
    logger.info(f"  Articles with media links: {media_link_count}/{len(articles)}")
    
    # Save to Supabase
    logger.info("Saving articles to Supabase...")
    success = storage.save_scraped_articles(articles)
    
    if success:
        logger.info(f"✅ Successfully saved {len(articles)} articles to Supabase")
        
        # Show sample content
        logger.info("\nSample article content:")
        if articles:
            sample = articles[0]
            logger.info(f"Title: {sample.get('title', 'N/A')}")
            logger.info(f"Source: {sample.get('source', 'N/A')}")
            logger.info(f"Content length: {len(sample.get('fullContent', ''))}")
            logger.info(f"Has media: {'Yes' if '[IMAGE:' in str(sample.get('fullContent', '')) else 'No'}")
            
        return True
    else:
        logger.error("❌ Failed to save articles to Supabase")
        return False

if __name__ == "__main__":
    success = test_enhanced_scraper()
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")