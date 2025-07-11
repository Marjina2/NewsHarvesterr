import requests
import json
import time
from typing import List, Dict, Optional
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIRephraser:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENROUTER_KEY') or ""
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "mistralai/mistral-7b-instruct:free"
        
        if not self.api_key:
            logger.warning("OpenRouter API key not found. AI rephrasing will be disabled.")
    
    def rephrase_headline(self, original_headline: str, source: str) -> Optional[str]:
        """Rephrase a single headline using Mistral AI"""
        if not self.api_key:
            logger.warning("API key not available, skipping rephrasing")
            return None
            
        try:
            prompt = f"""You are a professional news editor. Please rephrase the following news headline to make it more engaging and clear while preserving the original meaning and factual accuracy. 

Original headline: "{original_headline}"
Source: {source}

Please provide only the rephrased headline without any additional text or explanations."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv('REPLIT_DOMAINS', 'http://localhost:5000').split(',')[0],
                "X-Title": "News Scraper"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                rephrased = result['choices'][0]['message']['content'].strip()
                # Remove quotes if present
                if rephrased.startswith('"') and rephrased.endswith('"'):
                    rephrased = rephrased[1:-1]
                return rephrased
            else:
                logger.error("No choices in API response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error rephrasing headline: {str(e)}")
            return None
    
    def rephrase_articles(self, articles: List[Dict]) -> List[Dict]:
        """Rephrase multiple articles"""
        rephrased_articles = []
        
        for article in articles:
            original_title = article.get('title', '')
            source = article.get('source', '')
            
            logger.info(f"Rephrasing: {original_title[:50]}...")
            
            rephrased_title = self.rephrase_headline(original_title, source)
            
            rephrased_article = {
                'source': source,
                'original': original_title,
                'rephrased': rephrased_title or f"[AI Error] {original_title}",
                'url': article.get('url', ''),
                'timestamp': article.get('timestamp', time.strftime('%Y-%m-%dT%H:%M:%SZ'))
            }
            
            rephrased_articles.append(rephrased_article)
            
            # Rate limiting - be respectful to the API
            time.sleep(1)
        
        return rephrased_articles

def load_articles_from_json(filename: str = "raw_news.json") -> List[Dict]:
    """Load articles from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Articles file {filename} not found")
        return []
    except Exception as e:
        logger.error(f"Error loading articles: {str(e)}")
        return []

def save_rephrased_articles(articles: List[Dict], filename: str = "rephrased_news.json"):
    """Save rephrased articles to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} rephrased articles to {filename}")
    except Exception as e:
        logger.error(f"Error saving rephrased articles: {str(e)}")

if __name__ == "__main__":
    rephraser = AIRephraser()
    articles = load_articles_from_json()
    
    if articles:
        rephrased = rephraser.rephrase_articles(articles)
        save_rephrased_articles(rephrased)
    else:
        logger.warning("No articles found to rephrase")
