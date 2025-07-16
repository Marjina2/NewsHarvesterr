#!/usr/bin/env python3
"""Test all 17 sources and fix any issues"""

import sys
import os
sys.path.append('server')

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_sources():
    """Test all 17 sources individually"""
    scraper = NewsScraper()
    storage = StorageIntegration()
    
    # Get all active sources
    sources = storage.get_active_sources()
    logger.info(f"Testing {len(sources)} active sources...")
    
    working_sources = []
    failed_sources = []
    
    for source in sources:
        source_name = source['name']
        source_url = source['url']
        
        logger.info(f"\nTesting: {source_name}")
        logger.info(f"URL: {source_url}")
        
        try:
            # Test the specific scraper for this source
            articles = scraper.scrape_source(source_url, source_name)
            
            if articles and len(articles) > 0:
                logger.info(f"✅ {source_name}: {len(articles)} articles")
                working_sources.append({'name': source_name, 'count': len(articles)})
                
                # Show sample article
                sample = articles[0]
                logger.info(f"   Sample: {sample.get('title', 'N/A')[:100]}...")
                
            else:
                logger.warning(f"❌ {source_name}: No articles found")
                failed_sources.append(source_name)
                
        except Exception as e:
            logger.error(f"❌ {source_name}: Error - {str(e)}")
            failed_sources.append(source_name)
    
    # Summary
    logger.info(f"\n" + "="*50)
    logger.info(f"TESTING SUMMARY")
    logger.info(f"="*50)
    logger.info(f"Working sources: {len(working_sources)}")
    logger.info(f"Failed sources: {len(failed_sources)}")
    
    logger.info(f"\nWorking sources:")
    for source in working_sources:
        logger.info(f"  ✅ {source['name']}: {source['count']} articles")
    
    logger.info(f"\nFailed sources:")
    for source in failed_sources:
        logger.info(f"  ❌ {source}")
    
    # Test with working sources only
    if working_sources:
        logger.info(f"\nTesting scraping with working sources only...")
        working_source_configs = [s for s in sources if s['name'] in [ws['name'] for ws in working_sources]]
        
        # Take only first 5 working sources to test
        test_sources = working_source_configs[:5]
        
        logger.info(f"Running scraper with {len(test_sources)} working sources...")
        all_articles = scraper.scrape_all_sources(test_sources)
        
        if all_articles:
            logger.info(f"✅ Successfully scraped {len(all_articles)} articles from working sources")
            
            # Save to Supabase
            logger.info("Saving to Supabase...")
            success = storage.save_scraped_articles(all_articles)
            
            if success:
                logger.info(f"✅ Successfully saved {len(all_articles)} articles to Supabase")
            else:
                logger.error("❌ Failed to save articles to Supabase")
        else:
            logger.error("❌ No articles scraped from working sources")
    
    return working_sources, failed_sources

if __name__ == "__main__":
    working, failed = test_all_sources()
    print(f"\nResult: {len(working)} working, {len(failed)} failed")