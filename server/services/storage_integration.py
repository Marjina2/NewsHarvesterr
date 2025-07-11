import requests
import json
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageIntegration:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        
    def get_active_sources(self) -> List[Dict]:
        """Get active news sources from the Node.js storage"""
        try:
            response = requests.get(f"{self.base_url}/api/sources", timeout=10)
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
            for article in articles:
                article_data = {
                    'sourceName': article['source'],
                    'originalTitle': article['title'],
                    'originalUrl': article.get('url', ''),
                }
                
                response = requests.post(
                    f"{self.base_url}/api/articles",
                    json=article_data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to save article: {article['title'][:50]}...")
                    continue
                    
                logger.info(f"Saved article: {article['title'][:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving articles to storage: {str(e)}")
            return False
    
    def get_pending_articles(self) -> List[Dict]:
        """Get articles that need AI rephrasing"""
        try:
            response = requests.get(f"{self.base_url}/api/articles/pending", timeout=10)
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
                timeout=10
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error updating last run: {str(e)}")
            return False