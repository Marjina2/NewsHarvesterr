import requests
import json
import logging
import os
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageIntegration:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ.get("MASTER_TOKEN", "")}'
        }
        
    def get_active_sources(self) -> List[Dict]:
        """Get active news sources from the Node.js storage"""
        try:
            response = requests.get(f"{self.base_url}/api/sources", headers=self.headers, timeout=10)
            response.raise_for_status()
            sources = response.json()
            
            # Filter for active sources and convert to scraper format
            active_sources = []
            for source in sources:
                if source.get('isActive', False):
                    active_sources.append({
                        'name': source['name'],
                        'url': source['url'],
                        'isActive': True
                    })
            
            return active_sources
            
        except Exception as e:
            logger.error(f"Error getting sources from storage: {str(e)}")
            return []
    
    def save_scraped_articles(self, articles: List[Dict]) -> bool:
        """Save scraped articles to the Node.js storage"""
        try:
            saved_count = 0
            for article in articles:
                # Ensure the title meets minimum length requirement
                title = article.get('title', '').strip()
                if len(title) < 10:  # Skip articles with very short titles
                    logger.warning(f"Skipping article with short title: {title}")
                    continue
                
                # Clean and validate URL
                url = article.get('url', '').strip()
                if not url or not url.startswith(('http://', 'https://')):
                    url = None
                
                # Clean image URL
                image_url = article.get('imageUrl', '')
                if image_url and not image_url.startswith(('http://', 'https://')):
                    image_url = None
                
                # Convert publishedAt to ISO string if it's a date
                published_at = article.get('publishedAt')
                if published_at and hasattr(published_at, 'isoformat'):
                    published_at = published_at.isoformat()
                elif published_at and isinstance(published_at, str):
                    # Already a string, keep as is
                    pass
                else:
                    published_at = None
                
                article_data = {
                    'sourceName': article['source'],
                    'originalTitle': title,
                    'originalUrl': url,
                    'fullContent': article.get('fullContent'),
                    'excerpt': article.get('excerpt'),
                    'publishedAt': published_at,
                    'imageUrl': image_url,
                    'author': article.get('author'),
                    'category': article.get('category', 'general'),
                    'region': article.get('region', 'international'),
                }
                
                response = requests.post(
                    f"{self.base_url}/api/articles",
                    json=article_data,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to save article: {article['title'][:50]}... - Status: {response.status_code}")
                    if response.status_code == 400:
                        logger.warning(f"Validation error: {response.text}")
                    continue
                    
                saved_count += 1
                logger.info(f"Saved article: {article['title'][:50]}...")
            
            logger.info(f"Successfully saved {saved_count} out of {len(articles)} articles")
            return True
            
        except Exception as e:
            logger.error(f"Error saving articles to storage: {str(e)}")
            return False
    
    def get_pending_articles(self) -> List[Dict]:
        """Get articles that need AI rephrasing"""
        try:
            response = requests.get(f"{self.base_url}/api/articles/pending", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting pending articles: {str(e)}")
            return []
    
    def update_article_status(self, article_id: int, status: str, rephrased_title: Optional[str] = None) -> bool:
        """Update article status after AI processing"""
        try:
            data = {'status': status}
            if rephrased_title:
                data['rephrasedTitle'] = rephrased_title
            
            response = requests.put(
                f"{self.base_url}/api/articles/{article_id}",
                json=data,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error updating article status: {str(e)}")
            return False
    
    def update_scraper_last_run(self) -> bool:
        """Update the scraper's last run timestamp"""
        try:
            response = requests.post(
                f"{self.base_url}/api/scraper/last-run",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error updating last run: {str(e)}")
            return False