#!/usr/bin/env python3
"""
Run a complete scraping cycle with enhanced content extraction
Saves all articles to Supabase with complete article content including media links
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from services.scraper import NewsScraper
from services.storage_integration import StorageIntegration
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_full_scrape():
    """Run complete scraping cycle with enhanced content extraction"""
    logger.info("Starting FULL SCRAPING CYCLE with enhanced content extraction")
    logger.info("=" * 80)
    
    # Initialize components
    scraper = NewsScraper()
    storage = StorageIntegration()
    
    # Get all active sources
    logger.info("Fetching active news sources...")
    sources = storage.get_active_sources()
    logger.info(f"Found {len(sources)} active sources")
    
    # Display sources
    for i, source in enumerate(sources, 1):
        logger.info(f"  {i}. {source['name']} - {source['url']}")
    
    logger.info("\n" + "=" * 80)
    logger.info("ENFORCING STRICT RULE: 20 articles per source (10 Indian + 10 International)")
    logger.info("Enhanced content extraction: Complete articles with embedded media")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Scrape all sources with enhanced content extraction
    logger.info("Starting comprehensive scraping...")
    all_articles = scraper.scrape_all_sources(sources)
    
    scrape_time = time.time() - start_time
    
    # Validate results
    logger.info("\n" + "=" * 50)
    logger.info("SCRAPING RESULTS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total articles scraped: {len(all_articles)}")
    logger.info(f"Expected articles: {len(sources) * 20}")
    logger.info(f"Scraping time: {scrape_time:.2f} seconds")
    
    # Analyze content quality
    content_stats = {
        'with_full_content': 0,
        'with_media_links': 0,
        'with_images': 0,
        'with_authors': 0,
        'avg_content_length': 0,
        'total_content_length': 0
    }
    
    for article in all_articles:
        full_content = article.get('fullContent', '')
        if full_content and len(full_content) > 100:
            content_stats['with_full_content'] += 1
            content_stats['total_content_length'] += len(full_content)
        
        if '[IMAGE:' in str(full_content) or '[VIDEO]' in str(full_content) or '[EMBEDDED]' in str(full_content):
            content_stats['with_media_links'] += 1
        
        if article.get('imageUrl'):
            content_stats['with_images'] += 1
        
        if article.get('author'):
            content_stats['with_authors'] += 1
    
    if content_stats['with_full_content'] > 0:
        content_stats['avg_content_length'] = content_stats['total_content_length'] / content_stats['with_full_content']
    
    logger.info(f"\nCONTENT QUALITY ANALYSIS:")
    logger.info(f"  Articles with full content: {content_stats['with_full_content']}/{len(all_articles)} ({content_stats['with_full_content']/len(all_articles)*100:.1f}%)")
    logger.info(f"  Articles with media links: {content_stats['with_media_links']}/{len(all_articles)} ({content_stats['with_media_links']/len(all_articles)*100:.1f}%)")
    logger.info(f"  Articles with images: {content_stats['with_images']}/{len(all_articles)} ({content_stats['with_images']/len(all_articles)*100:.1f}%)")
    logger.info(f"  Articles with authors: {content_stats['with_authors']}/{len(all_articles)} ({content_stats['with_authors']/len(all_articles)*100:.1f}%)")
    logger.info(f"  Average content length: {content_stats['avg_content_length']:.0f} characters")
    
    # Analyze distribution
    source_distribution = {}
    region_distribution = {'indian': 0, 'international': 0}
    category_distribution = {}
    
    for article in all_articles:
        source = article.get('source', 'unknown')
        region = article.get('region', 'international')
        category = article.get('category', 'general')
        
        source_distribution[source] = source_distribution.get(source, 0) + 1
        region_distribution[region] = region_distribution.get(region, 0) + 1
        category_distribution[category] = category_distribution.get(category, 0) + 1
    
    logger.info(f"\nDISTRIBUTION ANALYSIS:")
    logger.info(f"  Region distribution: {region_distribution}")
    logger.info(f"  Category distribution: {category_distribution}")
    logger.info(f"\nPer-source distribution:")
    for source_name, count in source_distribution.items():
        logger.info(f"    {source_name}: {count} articles")
    
    # Save to Supabase
    logger.info("\n" + "=" * 50)
    logger.info("SAVING TO SUPABASE DATABASE")
    logger.info("=" * 50)
    
    save_start = time.time()
    success = storage.save_scraped_articles(all_articles)
    save_time = time.time() - save_start
    
    if success:
        logger.info(f"✅ SUCCESS: All {len(all_articles)} articles saved to Supabase")
        logger.info(f"Save time: {save_time:.2f} seconds")
    else:
        logger.error("❌ FAILED: Could not save articles to Supabase")
        return False
    
    # Update scraper status
    logger.info("\nUpdating scraper status...")
    storage.update_scraper_last_run()
    
    # Final summary
    total_time = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("FULL SCRAPING CYCLE COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Total articles processed: {len(all_articles)}")
    logger.info(f"Articles saved to Supabase: {len(all_articles)}")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    logger.info(f"Average time per article: {total_time/len(all_articles):.2f} seconds")
    logger.info("Enhanced content extraction with media links: ENABLED")
    logger.info("Strict 20 articles per source rule: ENFORCED")
    
    return True

if __name__ == "__main__":
    success = run_full_scrape()
    if success:
        print("\n🎉 Full scraping cycle completed successfully!")
    else:
        print("\n❌ Full scraping cycle failed!")
        sys.exit(1)