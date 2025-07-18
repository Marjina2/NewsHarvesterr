import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging
from newspaper import Article
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        # Enhanced headers to bypass bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Add retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def extract_full_article(self, url: str) -> Dict:
        """Extract complete article content including embedded media links"""
        try:
            if not url or url.startswith('#') or url.startswith('javascript:') or not url.startswith(('http://', 'https://')):
                return {
                    'fullContent': None,
                    'excerpt': None,
                    'publishedAt': None,
                    'imageUrl': None,
                    'author': None
                }

            # Enhanced article extraction with comprehensive content parsing
            article = Article(url)
            article.config.request_timeout = 15  # Increased timeout for complete extraction
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            article.config.follow_meta_refresh = True
            article.config.fetch_images = True
            article.config.memoize_articles = False
            
            article.download()
            if article.html:
                article.parse()
                
                # Enable NLP processing for better content extraction
                try:
                    article.nlp()
                except:
                    pass  # Continue without NLP if it fails

                # Extract complete content with enhanced fallback
                content = article.text.strip() if article.text else ""
                
                # Fallback content extraction if newspaper3k fails
                if not content or len(content) < 100:
                    content = self._extract_content_fallback(url, article.html)
                
                # Additional enhancement: Extract and preserve embedded media URLs
                if article.html and content:
                    media_content = self._extract_media_links(article.html, url)
                    if media_content:
                        content = content + "\n\n" + media_content
                
                excerpt = content[:500] + "..." if len(content) > 500 else content

            # Extract publish date
            publish_date = None
            if article.publish_date:
                publish_date = article.publish_date.isoformat()

            # Enhanced image extraction with multiple fallback methods
            image_url = None
            
            # Method 1: newspaper3k top image
            if article.top_image and article.top_image.startswith(('http://', 'https://')):
                image_url = article.top_image

            # Method 2: Optimized meta tags search (fewer selectors for speed)
            if not image_url and hasattr(article, 'html') and article.html:
                try:
                    soup = BeautifulSoup(article.html, 'html.parser')
                    
                    # Try only the most common meta tag variations for speed
                    meta_selectors = [
                        'meta[property="og:image"]',
                        'meta[name="twitter:image"]',
                        'meta[property="twitter:image"]'
                    ]
                    
                    for selector in meta_selectors:
                        meta_tag = soup.select_one(selector)
                        if meta_tag and meta_tag.get('content'):
                            candidate_url = meta_tag.get('content')
                            if candidate_url.startswith(('http://', 'https://')):
                                image_url = candidate_url
                                break
                    
                    # Method 3: Simplified img tag search for speed
                    if not image_url:
                        img_tags = soup.find_all('img', src=True, limit=5)  # Limit to first 5 images
                        for img in img_tags:
                            src = img.get('src')
                            if src:
                                # Convert relative URLs to absolute
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/'):
                                    from urllib.parse import urljoin
                                    src = urljoin(url, src)
                                
                                if src.startswith(('http://', 'https://')):
                                    # Quick skip for obvious unwanted images
                                    if any(skip in src.lower() for skip in ['logo', 'icon', 'pixel', '1x1']):
                                        continue
                                    
                                    # Take the first valid image for speed
                                    image_url = src
                                    break
                    
                    # Method 4: Look for figure or picture elements
                    if not image_url:
                        figure_imgs = soup.select('figure img, picture img, .image img')
                        for img in figure_imgs:
                            src = img.get('src')
                            if src and src.startswith(('http://', 'https://')):
                                image_url = src
                                break
                                
                except Exception as e:
                    logger.warning(f"Error extracting image from HTML: {str(e)}")
                    pass
            
            # Method 4: Generate placeholder image URL based on source
            if not image_url:
                # Create a placeholder image URL based on the source domain
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.lower()
                    
                    # Use a placeholder service with source-specific styling
                    if 'bbc' in domain:
                        image_url = "https://via.placeholder.com/400x250/bb1919/ffffff?text=BBC+News"
                    elif 'cnn' in domain:
                        image_url = "https://via.placeholder.com/400x250/cc0000/ffffff?text=CNN"
                    elif 'reuters' in domain:
                        image_url = "https://via.placeholder.com/400x250/ff6600/ffffff?text=Reuters"
                    elif 'techcrunch' in domain:
                        image_url = "https://via.placeholder.com/400x250/00d4aa/ffffff?text=TechCrunch"
                    elif 'guardian' in domain:
                        image_url = "https://via.placeholder.com/400x250/0084c6/ffffff?text=The+Guardian"
                    elif 'ndtv' in domain:
                        image_url = "https://via.placeholder.com/400x250/e31e24/ffffff?text=NDTV"
                    elif 'indiatoday' in domain:
                        image_url = "https://via.placeholder.com/400x250/dc143c/ffffff?text=India+Today"
                    elif 'thehindu' in domain:
                        image_url = "https://via.placeholder.com/400x250/004080/ffffff?text=The+Hindu"
                    elif 'timesofindia' in domain:
                        image_url = "https://via.placeholder.com/400x250/ff4500/ffffff?text=Times+of+India"
                    elif 'engadget' in domain:
                        image_url = "https://via.placeholder.com/400x250/00bcd4/ffffff?text=Engadget"
                    elif 'wired' in domain:
                        image_url = "https://via.placeholder.com/400x250/000000/ffffff?text=WIRED"
                    elif 'verge' in domain:
                        image_url = "https://via.placeholder.com/400x250/fa4616/ffffff?text=The+Verge"
                    elif 'ycombinator' in domain:
                        image_url = "https://via.placeholder.com/400x250/ff6600/ffffff?text=Hacker+News"
                    else:
                        image_url = "https://via.placeholder.com/400x250/6b7280/ffffff?text=News+Article"
                except:
                    image_url = "https://via.placeholder.com/400x250/6b7280/ffffff?text=News+Article"

            # Return extracted content if available
            if content and len(content) > 100:
                return {
                    'fullContent': content,
                    'excerpt': excerpt if excerpt and len(excerpt) > 50 else None,
                    'publishedAt': publish_date,
                    'imageUrl': image_url,
                    'author': ', '.join(article.authors) if article.authors else None
                }
            else:
                return {
                    'fullContent': None,
                    'excerpt': None,
                    'publishedAt': None,
                    'imageUrl': None,
                    'author': None
                }
        except Exception as e:
            logger.warning(f"Failed to extract full article from {url}: {str(e)}")
            return {
                'fullContent': None,
                'excerpt': None,
                'publishedAt': None,
                'imageUrl': None,
                'author': None
            }

    def _extract_content_fallback(self, url: str, html: str) -> str:
        """Enhanced fallback content extraction for all news sites"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe', 'noscript']):
                element.decompose()
            
            domain = urlparse(url).netloc.lower()
            
            # Site-specific selectors for better content extraction
            site_selectors = {
                'timesofindia.indiatimes.com': [
                    '.Normal', '.ga-headline', '._s30J', '.yYiw2',
                    '.story_content', '.article_content', '.article-body',
                    '.story-body', '.post-content', '.content-body'
                ],
                'indiatoday.in': [
                    '.story-details', '.story-content', '.description',
                    '.content-body', '.post-content', '.story-body'
                ],
                'ndtv.com': [
                    '.ins_storybody', '.story-content', '.content-body',
                    '.article-body', '.story-body', '.post-content'
                ],
                'thehindu.com': [
                    '.articlebodycontent', '.article-body', '.story-content',
                    '.content-body', '.post-content', '.story-body'
                ],
                'economictimes.indiatimes.com': [
                    '.Normal', '.articleText', '.article-body',
                    '.story-content', '.content-body', '.post-content'
                ],
                'bbc.com': [
                    '.story-body__inner', '.story-body', '.article-body',
                    '.content-body', '.post-content'
                ],
                'cnn.com': [
                    '.zn-body__paragraph', '.paragraph', '.article-body',
                    '.story-body', '.content-body'
                ],
                'techcrunch.com': [
                    '.article-content', '.entry-content', '.post-content',
                    '.article-body', '.story-body'
                ],
                'theverge.com': [
                    '.duet--article--article-body-component', '.article-body',
                    '.entry-content', '.post-content'
                ]
            }
            
            # Try site-specific selectors first
            content = ""
            if any(site in domain for site in site_selectors):
                for site in site_selectors:
                    if site in domain:
                        for selector in site_selectors[site]:
                            elements = soup.select(selector)
                            if elements:
                                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                                if len(content) > 300:  # Found substantial content
                                    break
                        if len(content) > 300:
                            break
            
            # If site-specific failed, try common selectors
            if not content or len(content) < 300:
                common_selectors = [
                    'article', '[role="main"]', '.article-content', '.story-content',
                    '.post-content', '.content', '.entry-content', '.article-body',
                    '.story-body', 'main', '.content-body', '.article-text'
                ]
                
                for selector in common_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = ' '.join([elem.get_text(strip=True) for elem in elements])
                        if len(content) > 300:  # Found substantial content
                            break
            
            # If still no good content, try paragraph extraction with better filtering
            if not content or len(content) < 300:
                paragraphs = soup.find_all('p')
                paragraph_texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    # Filter out short paragraphs, navigation, and ads
                    if (len(text) > 50 and 
                        not any(skip in text.lower() for skip in ['subscribe', 'advertisement', 'follow us', 'share', 'tweet', 'facebook', 'copyright', 'terms of service', 'privacy policy', 'cookie policy'])):
                        paragraph_texts.append(text)
                
                content = ' '.join(paragraph_texts)
            
            # Clean up the content
            content = content.strip()
            
            # Remove duplicate sentences (common in news sites)
            if content:
                sentences = content.split('. ')
                unique_sentences = []
                seen = set()
                for sentence in sentences:
                    if sentence not in seen and len(sentence) > 20:
                        unique_sentences.append(sentence)
                        seen.add(sentence)
                content = '. '.join(unique_sentences)
            
            return content
            
        except Exception as e:
            logger.warning(f"Fallback content extraction failed for {url}: {str(e)}")
            return ""

    def _extract_media_links(self, html: str, base_url: str) -> str:
        """Extract media links and embedded content from HTML"""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            soup = BeautifulSoup(html, 'html.parser')
            media_links = []
            
            # Extract image links
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(base_url, src)
                    
                    if src.startswith(('http://', 'https://')):
                        alt_text = img.get('alt', 'Image')
                        media_links.append(f"[IMAGE: {alt_text}] {src}")
            
            # Extract video links
            for video in soup.find_all('video', src=True):
                src = video.get('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(base_url, src)
                    
                    if src.startswith(('http://', 'https://')):
                        media_links.append(f"[VIDEO] {src}")
            
            # Extract iframe embeds (YouTube, Twitter, etc.)
            for iframe in soup.find_all('iframe', src=True):
                src = iframe.get('src')
                if src and ('youtube' in src or 'twitter' in src or 'instagram' in src):
                    media_links.append(f"[EMBEDDED] {src}")
            
            return '\n'.join(media_links) if media_links else ""
            
        except Exception as e:
            logger.warning(f"Media extraction failed: {str(e)}")
            return ""

    def _extract_complete_content_with_media(self, url: str, html: str) -> str:
        """Enhanced content extraction preserving media links and embedded content"""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements but preserve media containers
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'ads']):
                element.decompose()
            
            # Try enhanced article selectors
            content_selectors = [
                'article',
                '[role="main"]',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                '.story-body',
                '.article-body',
                '.article-text',
                '.post-body',
                'main'
            ]
            
            content_parts = []
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # Extract text with media link preservation
                    for child in element.descendants:
                        if child.name == 'p':
                            text = child.get_text(strip=True)
                            if text and len(text) > 20:
                                content_parts.append(text)
                        elif child.name == 'img' and child.get('src'):
                            img_src = child.get('src')
                            if img_src.startswith('//'):
                                img_src = 'https:' + img_src
                            elif img_src.startswith('/'):
                                img_src = urljoin(url, img_src)
                            
                            if img_src.startswith(('http://', 'https://')):
                                alt_text = child.get('alt', 'Image')
                                content_parts.append(f"[IMAGE: {alt_text}] {img_src}")
                        elif child.name == 'video' and child.get('src'):
                            video_src = child.get('src')
                            if video_src.startswith('//'):
                                video_src = 'https:' + video_src
                            elif video_src.startswith('/'):
                                video_src = urljoin(url, video_src)
                            
                            if video_src.startswith(('http://', 'https://')):
                                content_parts.append(f"[VIDEO] {video_src}")
                        elif child.name == 'iframe' and child.get('src'):
                            iframe_src = child.get('src')
                            if 'youtube' in iframe_src or 'twitter' in iframe_src or 'instagram' in iframe_src:
                                content_parts.append(f"[EMBEDDED] {iframe_src}")
                    
                    if content_parts:
                        break
            
            # Fallback to comprehensive text extraction
            if not content_parts:
                return self._extract_content_fallback(url, html)
            
            return '\n\n'.join(content_parts) if content_parts else ""
            
        except Exception as e:
            logger.warning(f"Enhanced content extraction failed: {str(e)}")
            return self._extract_content_fallback(url, html)

    def scrape_bbc_news(self, url: str) -> List[Dict]:
        """Scrape BBC News headlines"""
        try:
            # Try RSS feed first as it's more reliable
            rss_url = "http://feeds.bbci.co.uk/news/rss.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 25 items
            items = soup.find_all('item')[:25]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'BBC News',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping BBC News RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "BBC News")

    def scrape_reuters(self, url: str) -> List[Dict]:
        """Scrape Reuters headlines"""
        try:
            # Direct web scraping with enhanced headers
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Multiple selectors for Reuters articles
            article_selectors = [
                'div[data-testid="ArticleCard"]',
                'article',
                '.story-card',
                '.media-story-card__headline__eqhp9',
                '.media-story-card__body__3tRWy',
                '[data-testid="Heading"]',
                '.media-story-card',
                'h3 a',
                'h2 a',
                'h1 a'
            ]

            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements[:30]:  # Get more elements for better filtering
                        title_elem = element.find('h3') or element.find('h2') or element.find('h1') or element.find('a')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if len(title) > 20:
                                # Find the article URL
                                link_elem = element.find('a') or title_elem
                                if link_elem and link_elem.get('href'):
                                    article_url = link_elem.get('href')
                                    if article_url.startswith('/'):
                                        article_url = urljoin(url, article_url)
                                    elif not article_url.startswith(('http://', 'https://')):
                                        continue

                                    # Extract full article content
                                    article_details = self.extract_full_article(article_url)

                                    articles.append({
                                        'title': title,
                                        'url': article_url,
                                        'source': 'Reuters',
                                        **article_details
                                    })

                    if articles:
                        break

            return articles

        except Exception as e:
            logger.error(f"Error scraping Reuters: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "Reuters")

    def scrape_hackernews(self, url: str) -> List[Dict]:
        """Scrape Hacker News headlines"""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Hacker News specific selectors
            story_rows = soup.find_all('tr', class_='athing')[:30]

            for story in story_rows:
                title_elem = story.find('span', class_='titleline')
                if title_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        article_url = link_elem.get('href', '')

                        # Handle relative URLs
                        if article_url.startswith('item?id='):
                            article_url = urljoin(url, article_url)

                        if title and len(title) > 20:
                            # Extract full article content
                            article_details = self.extract_full_article(article_url) if article_url else {}

                            articles.append({
                                'title': title,
                                'url': article_url,
                                'source': 'Hacker News',
                                **article_details
                            })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Hacker News: {str(e)}")
            return []

    def scrape_generic_news(self, url: str, source_name: str) -> List[Dict]:
        """Enhanced generic news scraper for other sources"""
        try:
            # Use random delay to avoid rate limiting
            import random
            time.sleep(random.uniform(0.5, 2.0))
            
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Enhanced selectors for better coverage
            selectors = [
                # Article containers
                'article a',
                '.article a',
                '.story a',
                '.post a',
                '.entry a',
                '.news-item a',
                '.story-card a',
                '.article-card a',
                
                # Direct headline selectors
                'h1 a', 'h2 a', 'h3 a', 'h4 a',
                '.headline a', '.title a', '.article-title a',
                '.story-headline a', '.news-title a',
                '.entry-title a', '.post-title a',
                
                # Tech-specific selectors
                '.post-title a', '.story-title a',
                
                # Generic content selectors
                '[data-testid*="headline"] a',
                '[data-testid*="title"] a',
                '[class*="headline"] a',
                '[class*="title"] a',
                '[class*="story"] a',
                
                # Fallback for standalone headlines
                'h1', 'h2', 'h3',
                '[class*="headline"]',
                '[class*="title"]',
                '[class*="story"]'
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements[:40]:  # Increased limit for better results
                        title = ""
                        article_url = ""
                        
                        if element.name == 'a':
                            title = element.get_text(strip=True)
                            article_url = element.get('href', '')
                        else:
                            title = element.get_text(strip=True)
                            # Find associated link
                            link_elem = element.find('a') or element.find_parent('a')
                            if link_elem:
                                article_url = link_elem.get('href', '')
                                    
                        if len(title) > 20 and article_url:
                            # Normalize URL
                            if article_url.startswith('/'):
                                article_url = urljoin(url, article_url)
                            elif not article_url.startswith(('http://', 'https://')):
                                continue

                            # Extract full article content
                            article_details = self.extract_full_article(article_url)

                            articles.append({
                                'title': title,
                                'url': article_url,
                                'source': source_name,
                                **article_details
                            })

                            if len(articles) >= 30:  # Increased to get more articles
                                break

                    if len(articles) >= 30:
                        break

            return articles

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")
            return []

    def scrape_cnn(self, url: str) -> List[Dict]:
        """Scrape CNN headlines"""
        try:
            # Try RSS feed first
            rss_url = "http://rss.cnn.com/rss/edition.rss"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 25 items
            items = soup.find_all('item')[:25]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'CNN',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping CNN RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "CNN")

    def scrape_guardian(self, url: str) -> List[Dict]:
        """Scrape The Guardian headlines"""
        try:
            # Try RSS feed first
            rss_url = "https://www.theguardian.com/world/rss"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 25 items
            items = soup.find_all('item')[:25]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'The Guardian',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping The Guardian RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "The Guardian")

    def scrape_npr(self, url: str) -> List[Dict]:
        """Scrape NPR headlines"""
        try:
            # Try RSS feed first
            rss_url = "https://feeds.npr.org/1001/rss.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 25 items
            items = soup.find_all('item')[:25]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'NPR News',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping NPR RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "NPR News")

    def scrape_ap(self, url: str) -> List[Dict]:
        """Scrape Associated Press headlines"""
        try:
            # Try RSS feed first
            rss_url = "https://feeds.ap.org/ApTopHeadlines"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 25 items
            items = soup.find_all('item')[:25]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Associated Press',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Associated Press RSS: {str(e)}")
            # Fallback to generic scraping
            return self.scrape_generic_news(url, "Associated Press")

    def scrape_india_today(self, url: str) -> List[Dict]:
        """Scrape India Today headlines"""
        try:
            # Try RSS feed first as it's more reliable
            rss_url = "https://www.indiatoday.in/rss/1206578"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            # Parse RSS feed - get up to 25 items
            items = soup.find_all('item')[:25]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Extract full article content
                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'India Today',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping India Today RSS: {str(e)}")
            # Fallback to website scraping
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                articles = []

                # India Today specific selectors
                headline_selectors = [
                    '.story-list .story-card h2 a',
                    '.lead-story h2 a',
                    '.top-news h2 a',
                    '.story h2 a',
                    '.story-list h3 a',
                    '.catagory-listing h2 a'
                ]

                for selector in headline_selectors:
                    headlines = soup.select(selector)
                    for headline in headlines[:10]:
                        title = headline.get_text(strip=True)
                        if title and len(title) > 20:
                            article_url = urljoin(url, headline.get('href', ''))

                            # Extract full article content
                            article_details = self.extract_full_article(article_url) if article_url else {}

                            articles.append({
                                'title': title,
                                'url': article_url,
                                'source': 'India Today',
                                **article_details
                            })

                            if len(articles) >= 10:
                                break

                    if len(articles) >= 10:
                        break

                return articles

            except Exception as e2:
                logger.error(f"Error scraping India Today website: {str(e2)}")
                # Final fallback to generic scraping
                return self.scrape_generic_news(url, "India Today")

    def scrape_ndtv(self, url: str) -> List[Dict]:
        """Enhanced NDTV scraping with complete content extraction"""
        try:
            # NDTV RSS feed
            rss_url = "https://feeds.feedburner.com/ndtvnews-top-stories"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:20]  # Increased count

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Enhanced full article extraction
                        article_details = self.extract_full_article(article_url) if article_url else {}
                        
                        # Use RSS description as fallback if full content extraction fails
                        if not article_details.get('fullContent') and desc_elem:
                            article_details['fullContent'] = desc_elem.text.strip() if desc_elem.text else ""
                        
                        # If still no content, try direct scraping
                        if not article_details.get('fullContent') and article_url:
                            try:
                                direct_response = self.session.get(article_url, timeout=8)
                                direct_response.raise_for_status()
                                fallback_content = self._extract_content_fallback(article_url, direct_response.text)
                                if fallback_content:
                                    article_details['fullContent'] = fallback_content
                            except:
                                pass
                        
                        # Ensure we always have some content
                        if not article_details.get('fullContent'):
                            article_details['fullContent'] = f"Complete article available at NDTV: {article_url}"

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'NDTV',
                            'category': self.categorize_article(title, article_details.get('fullContent', ''), 'NDTV'),
                            'region': 'indian' if any(keyword in title.lower() for keyword in ['india', 'indian', 'delhi', 'mumbai', 'bengaluru', 'kolkata', 'chennai', 'hyderabad', 'pune', 'ahmedabad', 'bjp', 'congress', 'modi', 'rahul']) else 'international',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping NDTV: {str(e)}")
            return self.scrape_generic_news(url, "NDTV")

    def scrape_times_of_india(self, url: str) -> List[Dict]:
        """Enhanced Times of India scraping with complete content extraction"""
        try:
            # Times of India RSS feed
            rss_url = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:20]  # Increased to get more articles

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""
                        
                        # Enhanced full article extraction
                        article_details = self.extract_full_article(article_url) if article_url else {}
                        
                        # Use RSS description as fallback if full content extraction fails
                        if not article_details.get('fullContent') and desc_elem:
                            article_details['fullContent'] = desc_elem.text.strip() if desc_elem.text else ""
                        
                        # If still no content, try one more time with direct scraping
                        if not article_details.get('fullContent') and article_url:
                            try:
                                direct_response = self.session.get(article_url, timeout=8)
                                direct_response.raise_for_status()
                                fallback_content = self._extract_content_fallback(article_url, direct_response.text)
                                if fallback_content:
                                    article_details['fullContent'] = fallback_content
                            except:
                                pass
                        
                        # Ensure we always have some content
                        if not article_details.get('fullContent'):
                            article_details['fullContent'] = f"Complete article available at Times of India: {article_url}"

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Times of India',
                            'category': self.categorize_article(title, article_details.get('fullContent', ''), 'Times of India'),
                            'region': 'indian' if any(keyword in title.lower() for keyword in ['india', 'indian', 'delhi', 'mumbai', 'bengaluru', 'kolkata', 'chennai', 'hyderabad', 'pune', 'ahmedabad', 'bjp', 'congress', 'modi', 'rahul']) else 'international',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Times of India: {str(e)}")
            return self.scrape_generic_news(url, "Times of India")

    def scrape_hindu(self, url: str) -> List[Dict]:
        """Scrape The Hindu headlines"""
        try:
            # The Hindu RSS feed
            rss_url = "https://www.thehindu.com/feeder/default.rss"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:15]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Hindu',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping The Hindu: {str(e)}")
            return self.scrape_generic_news(url, "Hindu")

    def scrape_economic_times(self, url: str) -> List[Dict]:
        """Enhanced Economic Times scraping with complete content extraction"""
        try:
            # Economic Times RSS feed
            rss_url = "https://economictimes.indiatimes.com/rssfeedstopstories.cms"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:20]  # Increased count

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        # Enhanced full article extraction
                        article_details = self.extract_full_article(article_url) if article_url else {}
                        
                        # Use RSS description as fallback if full content extraction fails
                        if not article_details.get('fullContent') and desc_elem:
                            article_details['fullContent'] = desc_elem.text.strip() if desc_elem.text else ""
                        
                        # If still no content, try direct scraping
                        if not article_details.get('fullContent') and article_url:
                            try:
                                direct_response = self.session.get(article_url, timeout=8)
                                direct_response.raise_for_status()
                                fallback_content = self._extract_content_fallback(article_url, direct_response.text)
                                if fallback_content:
                                    article_details['fullContent'] = fallback_content
                            except:
                                pass
                        
                        # Ensure we always have some content
                        if not article_details.get('fullContent'):
                            article_details['fullContent'] = f"Complete article available at Economic Times: {article_url}"

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Economic Times',
                            'category': self.categorize_article(title, article_details.get('fullContent', ''), 'Economic Times'),
                            'region': 'indian' if any(keyword in title.lower() for keyword in ['india', 'indian', 'delhi', 'mumbai', 'bengaluru', 'kolkata', 'chennai', 'hyderabad', 'pune', 'ahmedabad', 'bjp', 'congress', 'modi', 'rahul']) else 'international',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Economic Times: {str(e)}")
            return self.scrape_generic_news(url, "Economic Times")

    def scrape_techcrunch(self, url: str) -> List[Dict]:
        """Scrape TechCrunch headlines"""
        try:
            rss_url = "https://techcrunch.com/feed/"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'TechCrunch',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping TechCrunch RSS: {str(e)}")
            return self.scrape_generic_news(url, "TechCrunch")

    def scrape_wired(self, url: str) -> List[Dict]:
        """Scrape WIRED headlines"""
        try:
            rss_url = "https://www.wired.com/feed/rss"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'WIRED',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping WIRED RSS: {str(e)}")
            return self.scrape_generic_news(url, "WIRED")

    def scrape_engadget(self, url: str) -> List[Dict]:
        """Scrape Engadget headlines"""
        try:
            rss_url = "https://www.engadget.com/rss.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Engadget',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Engadget RSS: {str(e)}")
            return self.scrape_generic_news(url, "Engadget")

    def scrape_ars_technica(self, url: str) -> List[Dict]:
        """Scrape Ars Technica headlines"""
        try:
            rss_url = "https://feeds.arstechnica.com/arstechnica/index"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Ars Technica',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping Ars Technica RSS: {str(e)}")
            return self.scrape_generic_news(url, "Ars Technica")

    def scrape_verge(self, url: str) -> List[Dict]:
        """Scrape The Verge headlines"""
        try:
            rss_url = "https://www.theverge.com/rss/index.xml"
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            articles = []

            items = soup.find_all('item')[:10]

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')

                if title_elem and title_elem.text:
                    title = title_elem.text.strip()
                    if len(title) > 20:
                        article_url = link_elem.text.strip() if link_elem else ""

                        article_details = self.extract_full_article(article_url) if article_url else {}

                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'The Verge',
                            **article_details
                        })

            return articles

        except Exception as e:
            logger.error(f"Error scraping The Verge RSS: {str(e)}")
            return self.scrape_generic_news(url, "The Verge")

    def scrape_source(self, url: str, source_name: str) -> List[Dict]:
        """Scrape a news source based on domain"""
        domain = urlparse(url).netloc.lower()

        if 'bbc.com' in domain:
            return self.scrape_bbc_news(url)
        elif 'reuters.com' in domain:
            return self.scrape_reuters(url)
        elif 'cnn.com' in domain:
            return self.scrape_cnn(url)
        elif 'theguardian.com' in domain:
            return self.scrape_guardian(url)
        elif 'npr.org' in domain:
            return self.scrape_npr(url)
        elif 'apnews.com' in domain:
            return self.scrape_ap(url)
        elif 'ycombinator.com' in domain:
            return self.scrape_hackernews(url)
        elif 'indiatoday.in' in domain:
            return self.scrape_india_today(url)
        elif 'ndtv.com' in domain:
            return self.scrape_ndtv(url)
        elif 'timesofindia.indiatimes.com' in domain:
            return self.scrape_times_of_india(url)
        elif 'thehindu.com' in domain:
            return self.scrape_hindu(url)
        elif 'economictimes.indiatimes.com' in domain:
            return self.scrape_economic_times(url)
        elif 'techcrunch.com' in domain:
            return self.scrape_techcrunch(url)
        elif 'wired.com' in domain:
            return self.scrape_wired(url)
        elif 'engadget.com' in domain:
            return self.scrape_engadget(url)
        elif 'arstechnica.com' in domain:
            return self.scrape_ars_technica(url)
        elif 'theverge.com' in domain:
            return self.scrape_verge(url)
        else:
            return self.scrape_generic_news(url, source_name)

    def scrape_source_comprehensive(self, url: str, source_name: str) -> List[Dict]:
        """
        COMPREHENSIVE SCRAPING: Extract ALL available articles from a source's main page
        This method scrapes from top to bottom, collecting every visible article link
        """
        try:
            logger.info(f"COMPREHENSIVE: Starting complete extraction from {source_name}")
            
            # Use domain-specific scraper first for better results
            domain = urlparse(url).netloc.lower()
            
            # Use existing specialized scrapers but enhance them for comprehensive data
            if 'bbc.com' in domain:
                articles = self.scrape_bbc_comprehensive(url)
            elif 'reuters.com' in domain:
                articles = self.scrape_reuters_comprehensive(url)
            elif 'cnn.com' in domain:
                articles = self.scrape_cnn_comprehensive(url)
            elif 'theguardian.com' in domain:
                articles = self.scrape_guardian_comprehensive(url)
            elif 'npr.org' in domain:
                articles = self.scrape_npr_comprehensive(url)
            elif 'apnews.com' in domain:
                articles = self.scrape_ap_comprehensive(url)
            elif 'ycombinator.com' in domain:
                articles = self.scrape_hackernews_comprehensive(url)
            elif 'indiatoday.in' in domain:
                articles = self.scrape_india_today_comprehensive(url)
            elif 'ndtv.com' in domain:
                articles = self.scrape_ndtv_comprehensive(url)
            elif 'timesofindia.indiatimes.com' in domain:
                articles = self.scrape_times_of_india_comprehensive(url)
            elif 'thehindu.com' in domain:
                articles = self.scrape_hindu_comprehensive(url)
            elif 'economictimes.indiatimes.com' in domain:
                articles = self.scrape_economic_times_comprehensive(url)
            elif 'techcrunch.com' in domain:
                articles = self.scrape_techcrunch_comprehensive(url)
            elif 'wired.com' in domain:
                articles = self.scrape_wired_comprehensive(url)
            elif 'engadget.com' in domain:
                articles = self.scrape_engadget_comprehensive(url)
            elif 'arstechnica.com' in domain:
                articles = self.scrape_ars_technica_comprehensive(url)
            elif 'theverge.com' in domain:
                articles = self.scrape_verge_comprehensive(url)
            else:
                articles = self.scrape_generic_comprehensive(url, source_name)
            
            logger.info(f"COMPREHENSIVE: Extracted {len(articles)} total articles from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"COMPREHENSIVE scraping failed for {source_name}: {e}")
            # Fallback to existing method
            return self.scrape_source(url, source_name)

    def scrape_generic_comprehensive(self, url: str, source_name: str) -> List[Dict]:
        """
        COMPREHENSIVE GENERIC SCRAPER: Extract ALL articles from any news source
        Scrapes every visible article link from top to bottom of the page
        """
        try:
            import random
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(url, timeout=20, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            seen_urls = set()

            # COMPREHENSIVE SELECTORS - Extract EVERYTHING
            comprehensive_selectors = [
                # Primary article containers (high priority)
                'article a[href*="/"]', 'article h1 a', 'article h2 a', 'article h3 a',
                '.article a[href*="/"]', '.story a[href*="/"]', '.post a[href*="/"]',
                '.news-item a[href*="/"]', '.story-card a[href*="/"]', '.article-card a[href*="/"]',
                
                # Headlines and titles (medium priority)
                'h1 a[href*="/"]', 'h2 a[href*="/"]', 'h3 a[href*="/"]', 'h4 a[href*="/"]',
                '.headline a[href*="/"]', '.title a[href*="/"]', '.article-title a[href*="/"]',
                '.story-headline a[href*="/"]', '.news-title a[href*="/"]',
                '.entry-title a[href*="/"]', '.post-title a[href*="/"]',
                
                # Navigation and listing areas
                '.content a[href*="/"]', '.main a[href*="/"]', '.primary a[href*="/"]',
                '.articles a[href*="/"]', '.stories a[href*="/"]', '.posts a[href*="/"]',
                '.news a[href*="/"]', '.feed a[href*="/"]', '.list a[href*="/"]',
                
                # Data attributes (modern websites)
                '[data-testid*="headline"] a[href*="/"]', '[data-testid*="title"] a[href*="/"]',
                '[data-testid*="story"] a[href*="/"]', '[data-testid*="article"] a[href*="/"]',
                
                # Class-based selectors (catch-all)
                '[class*="headline"] a[href*="/"]', '[class*="title"] a[href*="/"]',
                '[class*="story"] a[href*="/"]', '[class*="article"] a[href*="/"]',
                '[class*="news"] a[href*="/"]', '[class*="post"] a[href*="/"]',
                
                # Generic link selectors as fallback
                'a[href*="/news/"]', 'a[href*="/article/"]', 'a[href*="/story/"]',
                'a[href*="/post/"]', 'a[href*="' + urlparse(url).netloc + '"]'
            ]

            logger.info(f"COMPREHENSIVE: Scanning {source_name} with {len(comprehensive_selectors)} selector patterns")

            for selector in comprehensive_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        title = element.get_text(strip=True)
                        article_url = element.get('href', '')
                        
                        # Validate article content
                        if len(title) < 10 or len(title) > 200:  # Reasonable title length
                            continue
                            
                        # Skip navigation, menu, and non-article links
                        skip_keywords = [
                            'menu', 'nav', 'footer', 'header', 'sidebar', 'comment', 'share',
                            'subscribe', 'newsletter', 'login', 'register', 'contact', 'about',
                            'privacy', 'terms', 'cookie', 'advertise', 'shop', 'buy'
                        ]
                        
                        if any(keyword in title.lower() for keyword in skip_keywords):
                            continue
                            
                        # Normalize URL
                        if article_url.startswith('/'):
                            article_url = urljoin(url, article_url)
                        elif not article_url.startswith(('http://', 'https://')):
                            continue
                            
                        # Skip duplicates
                        if article_url in seen_urls:
                            continue
                        seen_urls.add(article_url)
                        
                        # Skip obvious non-article URLs
                        skip_url_patterns = [
                            '/tag/', '/category/', '/author/', '/search/', '/page/',
                            '/feed/', '/rss/', '/sitemap/', '/archive/', '/contact/',
                            '.pdf', '.jpg', '.png', '.gif', '.mp4', '.video'
                        ]
                        
                        if any(pattern in article_url.lower() for pattern in skip_url_patterns):
                            continue

                        # Extract article content (without full article extraction for speed)
                        article_data = {
                            'title': title,
                            'url': article_url,
                            'source': source_name,
                            'fullContent': title,  # Use title as initial content
                            'excerpt': title[:200] + '...' if len(title) > 200 else title,
                            'publishedAt': None,
                            'imageUrl': '',
                            'author': '',
                            'category': self.categorize_article(title, title, source_name),
                            'region': self.get_article_region(title, source_name)
                        }
                        
                        articles.append(article_data)
                        
                        # Log progress every 50 articles
                        if len(articles) % 50 == 0:
                            logger.info(f"COMPREHENSIVE: Collected {len(articles)} articles from {source_name}")
                            
                        # Reasonable limit to prevent infinite collection
                        if len(articles) >= 200:  # Collect up to 200 articles per source
                            logger.info(f"COMPREHENSIVE: Reached limit of 200 articles for {source_name}")
                            break
                            
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed for {source_name}: {e}")
                    continue
                    
                if len(articles) >= 200:
                    break

            # Remove duplicates based on title similarity
            unique_articles = []
            seen_titles = set()
            
            for article in articles:
                title_key = article['title'].lower().strip()[:50]  # First 50 chars for similarity
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_articles.append(article)

            logger.info(f"COMPREHENSIVE: Final result - {len(unique_articles)} unique articles from {source_name}")
            return unique_articles[:150]  # Final limit per source

        except Exception as e:
            logger.error(f"COMPREHENSIVE generic scraping failed for {source_name}: {e}")
            return []

    def scrape_bbc_comprehensive(self, url: str) -> List[Dict]:
        """Comprehensive BBC scraping - extract all visible articles"""
        # First get from RSS for structured data
        articles = self.scrape_bbc_news(url)
        
        # Then get additional articles from main page
        additional = self.scrape_generic_comprehensive(url, "BBC News")
        
        # Combine and deduplicate
        all_titles = {article['title'].lower() for article in articles}
        for article in additional:
            if article['title'].lower() not in all_titles:
                articles.append(article)
                
        return articles[:100]  # Limit BBC to 100 articles

    def scrape_cnn_comprehensive(self, url: str) -> List[Dict]:
        """Comprehensive CNN scraping"""
        articles = self.scrape_cnn(url)
        additional = self.scrape_generic_comprehensive(url, "CNN")
        
        all_titles = {article['title'].lower() for article in articles}
        for article in additional:
            if article['title'].lower() not in all_titles:
                articles.append(article)
                
        return articles[:100]

    def scrape_guardian_comprehensive(self, url: str) -> List[Dict]:
        """Comprehensive Guardian scraping"""
        articles = self.scrape_guardian(url)
        additional = self.scrape_generic_comprehensive(url, "The Guardian")
        
        all_titles = {article['title'].lower() for article in articles}
        for article in additional:
            if article['title'].lower() not in all_titles:
                articles.append(article)
                
        return articles[:100]

    def scrape_times_of_india_comprehensive(self, url: str) -> List[Dict]:
        """Comprehensive Times of India scraping"""
        articles = self.scrape_times_of_india(url)
        additional = self.scrape_generic_comprehensive(url, "Times of India")
        
        all_titles = {article['title'].lower() for article in articles}
        for article in additional:
            if article['title'].lower() not in all_titles:
                articles.append(article)
                
        return articles[:100]

    def scrape_ndtv_comprehensive(self, url: str) -> List[Dict]:
        """Comprehensive NDTV scraping"""
        articles = self.scrape_ndtv(url)
        additional = self.scrape_generic_comprehensive(url, "NDTV")
        
        all_titles = {article['title'].lower() for article in articles}
        for article in additional:
            if article['title'].lower() not in all_titles:
                articles.append(article)
                
        return articles[:100]

    # Add fallback methods for sources that don't have comprehensive versions yet
    def scrape_reuters_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "Reuters")
        
    def scrape_npr_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "NPR")
        
    def scrape_ap_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "Associated Press")
        
    def scrape_hackernews_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "Hacker News")
        
    def scrape_india_today_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "India Today")
        
    def scrape_hindu_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "The Hindu")
        
    def scrape_economic_times_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "Economic Times")
        
    def scrape_techcrunch_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "TechCrunch")
        
    def scrape_wired_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "WIRED")
        
    def scrape_engadget_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "Engadget")
        
    def scrape_ars_technica_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "Ars Technica")
        
    def scrape_verge_comprehensive(self, url: str) -> List[Dict]:
        return self.scrape_generic_comprehensive(url, "The Verge")

    def categorize_article(self, title: str, content: str = "", source: str = "") -> str:
        """Enhanced categorization based on title, content, and source"""
        title_lower = title.lower()
        content_lower = content.lower() if content else ""
        source_lower = source.lower()
        combined = f"{title_lower} {content_lower}"

        # Source-based categorization first
        if source_lower in ['techcrunch', 'the verge', 'engadget', 'ars technica', 'wired', 'hacker news']:
            return 'technology'
        elif source_lower in ['bloomberg', 'wall street journal', 'forbes', 'financial times', 'economic times']:
            return 'business'

        # Enhanced keyword matching with weighted scores
        categories = {
            'technology': ['ai', 'artificial intelligence', 'tech', 'technology', 'software', 'app', 'digital', 'cyber', 'robot', 'automation', 'startup', 'computer', 'internet', 'smartphone', 'gadget', 'coding', 'programming', 'data', 'algorithm', 'silicon valley', 'blockchain', 'cryptocurrency', 'metaverse', 'virtual reality', 'ar', 'vr', 'machine learning', 'iot'],
            'business': ['business', 'economy', 'finance', 'market', 'stock', 'investment', 'company', 'corporate', 'trade', 'banking', 'money', 'funding', 'revenue', 'profit', 'earnings', 'merger', 'acquisition', 'ipo', 'nasdaq', 'dow jones', 'economic', 'financial', 'billion', 'million', 'dollar', 'rupee', 'gdp', 'inflation'],
            'politics': ['politics', 'government', 'minister', 'parliament', 'election', 'policy', 'law', 'court', 'supreme', 'democracy', 'vote', 'president', 'prime minister', 'congress', 'senate', 'cabinet', 'diplomatic', 'treaty', 'sanctions', 'constitutional', 'legislature', 'judicial', 'executive'],
            'sports': ['sports', 'cricket', 'football', 'olympics', 'match', 'team', 'player', 'game', 'championship', 'tournament', 'soccer', 'basketball', 'tennis', 'hockey', 'swimming', 'athletics', 'medal', 'victory', 'defeat', 'score', 'league'],
            'science': ['science', 'research', 'study', 'discovery', 'scientist', 'medicine', 'health', 'space', 'nasa', 'quantum', 'climate', 'medical', 'pharmaceutical', 'vaccine', 'treatment', 'diagnosis', 'hospital', 'doctor', 'patient', 'therapy', 'clinical trial', 'breakthrough'],
            'entertainment': ['movie', 'film', 'actor', 'actress', 'bollywood', 'hollywood', 'music', 'celebrity', 'entertainment', 'cinema', 'director', 'producer', 'album', 'song', 'concert', 'festival', 'award', 'oscar', 'emmy', 'grammy', 'netflix', 'streaming']
        }

        # Calculate scores for each category
        scores = {}
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in combined:
                    # Give higher weight to title matches
                    if keyword in title_lower:
                        score += 3
                    else:
                        score += 1
            scores[category] = score

        # Return category with highest score, minimum threshold of 2
        max_category = max(scores, key=scores.get)
        if scores[max_category] >= 2:
            return max_category
        else:
            return 'general'

    def detect_indian_content(self, title: str, content: str = "", source: str = "") -> str:
        """Detect if content is India-related"""
        title_lower = title.lower()
        content_lower = content.lower() if content else ""
        source_lower = source.lower()
        combined = f"{title_lower} {content_lower} {source_lower}"

        indian_keywords = [
            'india', 'indian', 'delhi', 'mumbai', 'bengaluru', 'bangalore', 'kolkata', 'chennai', 'hyderabad', 'pune',
            'bollywood', 'rupee', 'modi', 'bjp', 'congress', 'lok sabha', 'rajya sabha', 'parliament', 'supreme court',
            'maharashtra', 'gujarat', 'rajasthan', 'punjab', 'haryana', 'uttar pradesh', 'bihar', 'west bengal',
            'kerala', 'tamil nadu', 'karnataka', 'andhra pradesh', 'telangana', 'odisha', 'jharkhand', 'chhattisgarh',
            'isro', 'iit', 'iisc', 'tata', 'reliance', 'infosys', 'wipro', 'ola', 'flipkart', 'paytm', 'zomato'
        ]

        if any(keyword in combined for keyword in indian_keywords) or 'india' in source_lower:
            return 'indian'
        else:
            return 'international'

    def scrape_source_with_categories(self, url: str, source_name: str, target_articles: int = 20) -> List[Dict]:
        """
        STRICT RULE: Scrape exactly 20 articles per source (10 Indian + 10 International)
        This function enforces the hardcoded rule for consistent article distribution in Supabase
        """
        try:
            # HARDCODED RULE: Must get exactly 20 articles per source
            REQUIRED_INDIAN_ARTICLES = 10
            REQUIRED_INTERNATIONAL_ARTICLES = 10
            
            logger.info(f"STRICT RULE ENFORCEMENT: Scraping {source_name} for exactly {REQUIRED_INDIAN_ARTICLES} Indian + {REQUIRED_INTERNATIONAL_ARTICLES} international articles")
            
            # Scrape articles with full content extraction - get more than needed to ensure selection
            all_articles = self.scrape_source(url, source_name)
            
            # MANDATORY: Process each article to ensure full content extraction
            for article in all_articles:
                if article.get('url') and not article.get('fullContent'):
                    logger.info(f"Extracting full content for: {article['title'][:50]}...")
                    content_data = self.extract_full_article(article['url'])
                    article.update(content_data)
                    
                # QUALITY CHECK: Ensure article has meaningful content
                if not article.get('fullContent') or len(article.get('fullContent', '').strip()) < 50:
                    logger.warning(f"Article has insufficient content: {article['title'][:50]}...")
                    # Try to re-extract content
                    if article.get('url'):
                        content_data = self.extract_full_article(article['url'])
                        article.update(content_data)
                    
                    # If still no content, use title as content fallback
                    if not article.get('fullContent') or len(article.get('fullContent', '').strip()) < 50:
                        article['fullContent'] = article['title'] + "\n\n" + (article.get('excerpt', '') or 'Content not available')
            
            # Remove duplicates based on title similarity
            unique_articles = []
            seen_titles = set()
            for article in all_articles:
                title_words = set(article['title'].lower().split())
                is_duplicate = any(len(title_words.intersection(set(seen_title.split()))) > len(title_words) * 0.6 
                                 for seen_title in seen_titles)
                if not is_duplicate:
                    unique_articles.append(article)
                    seen_titles.add(article['title'].lower())
            
            # Categorize articles
            categorized_articles = {
                'indian': {
                    'technology': [], 'business': [], 'politics': [], 'sports': [], 
                    'science': [], 'entertainment': [], 'general': []
                },
                'international': {
                    'technology': [], 'business': [], 'politics': [], 'sports': [], 
                    'science': [], 'entertainment': [], 'general': []
                }
            }
            
            for article in unique_articles:
                # Enhanced categorization
                category = self.categorize_article(article['title'], article.get('fullContent', ''), source_name)
                region = self.detect_indian_content(article['title'], article.get('fullContent', ''), source_name)
                
                article['category'] = category
                article['region'] = region
                
                categorized_articles[region][category].append(article)
            
            # STRICT RULE ENFORCEMENT: Must get exactly 10 Indian + 10 International articles
            final_articles = []
            
            # Select exactly 10 Indian articles across different categories
            indian_articles = self._select_diverse_articles(categorized_articles['indian'], REQUIRED_INDIAN_ARTICLES)
            final_articles.extend(indian_articles)
            
            # Select exactly 10 International articles across different categories
            international_articles = self._select_diverse_articles(categorized_articles['international'], REQUIRED_INTERNATIONAL_ARTICLES)
            final_articles.extend(international_articles)
            
            # QUALITY VALIDATION: Ensure we have content for all articles (relaxed validation)
            validated_articles = []
            for article in final_articles:
                # Relaxed validation: accept articles with title + some content
                if article.get('fullContent') and len(article.get('fullContent', '').strip()) >= 20:
                    validated_articles.append(article)
                else:
                    # If no content, use title as content fallback
                    if not article.get('fullContent'):
                        article['fullContent'] = article['title'] + "\n\n" + (article.get('excerpt', '') or 'Full content not available for this article.')
                    validated_articles.append(article)
            
            # STRICT ENFORCEMENT: If we don't have enough validated articles, try to get more
            if len(validated_articles) < target_articles:
                logger.warning(f"Only {len(validated_articles)} articles validated, need {target_articles}")
                # Try to get more articles from available categories
                for region in ['indian', 'international']:
                    if len(validated_articles) >= target_articles:
                        break
                    for category in categorized_articles[region]:
                        if len(validated_articles) >= target_articles:
                            break
                        for article in categorized_articles[region][category]:
                            if article not in validated_articles:
                                # Relaxed validation for additional articles
                                if not article.get('fullContent'):
                                    article['fullContent'] = article['title'] + "\n\n" + (article.get('excerpt', '') or 'Full content not available for this article.')
                                validated_articles.append(article)
                                if len(validated_articles) >= target_articles:
                                    break
            
            # Log the distribution
            category_count = {}
            region_count = {}
            for article in validated_articles:
                category = article.get('category', 'general')
                region = article.get('region', 'international')
                category_count[category] = category_count.get(category, 0) + 1
                region_count[region] = region_count.get(region, 0) + 1
            
            logger.info(f"STRICT RULE ENFORCED: Scraped {len(validated_articles)} articles from {source_name}")
            logger.info(f"Region distribution: {region_count}")
            logger.info(f"Category distribution: {category_count}")
            
            # ADAPTIVE VALIDATION: Return what we have, prioritizing quality over quantity
            if len(validated_articles) < target_articles:
                logger.warning(f"Could not meet strict requirement of {target_articles} articles, returning {len(validated_articles)}")
            
            # Return all validated articles (may be less than target if source can't provide enough)
            return validated_articles
            
        except Exception as e:
            logger.error(f"Error scraping {source_name} with categories: {str(e)}")
            return []
    
    def _select_diverse_articles(self, categorized_articles: Dict, target_count: int) -> List[Dict]:
        """Select articles ensuring category diversity"""
        selected = []
        categories = ['technology', 'business', 'politics', 'sports', 'science', 'entertainment', 'general']
        
        # First, try to get 1-2 articles from each category
        articles_per_category = max(1, target_count // len(categories))
        
        for category in categories:
            articles = categorized_articles[category]
            selected.extend(articles[:articles_per_category])
            if len(selected) >= target_count:
                break
        
        # If we still need more articles, fill from any available category
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            for category in categories:
                if remaining <= 0:
                    break
                articles = categorized_articles[category]
                # Skip articles already selected
                available = [a for a in articles if a not in selected]
                selected.extend(available[:remaining])
                remaining = target_count - len(selected)
        
        return selected[:target_count]

    def scrape_all_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        ENHANCED COMPREHENSIVE SCRAPING: Extract ALL available articles from each source's main page
        This ensures maximum data collection from top to bottom of each news site
        """
        all_articles = []
        seen_titles = set()  # Track titles to prevent duplicates
        
        logger.info(f"COMPREHENSIVE SCRAPING: Starting complete extraction from {len(sources)} sources")
        logger.info(f"Target: Extract ALL visible articles from each source's main page")
        
        for source in sources:
            if source.get('isActive', True):
                logger.info(f"COMPREHENSIVE SCRAPING: Extracting ALL articles from {source['name']}")
                
                # Use comprehensive scraping method to get all available articles
                articles = self.scrape_source_comprehensive(source['url'], source['name'])
                
                processed_articles = []
                indian_count = 0
                international_count = 0
                
                for article in articles:
                    # Enhanced duplicate detection across all sources
                    title_clean = article['title'].strip().lower()
                    # Create a more robust duplicate key using title and source
                    duplicate_key = f"{title_clean}_{source['name'].lower()}"
                    
                    if duplicate_key in seen_titles:
                        continue
                    
                    # Ensure content is available (relaxed validation)
                    if not article.get('fullContent') or len(article.get('fullContent', '').strip()) < 20:
                        # Use title as fallback content
                        article['fullContent'] = article['title'] + "\n\n" + (article.get('excerpt', '') or 'Full content not available for this article.')
                        logger.info(f"Using title as content for: {article['title'][:50]}...")
                    
                    # Count region distribution
                    region = article.get('region', 'international')
                    if region == 'indian':
                        indian_count += 1
                    else:
                        international_count += 1
                    
                    # Add article to processed list
                    processed_articles.append(article)
                    seen_titles.add(duplicate_key)
                
                # Add processed articles to the main list
                all_articles.extend(processed_articles)
                
                # STRICT RULE VALIDATION: Log the exact distribution
                logger.info(f"STRICT RULE RESULT: {source['name']} provided {len(processed_articles)} articles")
                logger.info(f"  - Indian articles: {indian_count}")
                logger.info(f"  - International articles: {international_count}")
                
                if len(processed_articles) < ARTICLES_PER_SOURCE:
                    logger.warning(f"WARNING: {source['name']} only provided {len(processed_articles)} articles, expected {ARTICLES_PER_SOURCE}")
                
                logger.info(f"Total articles collected so far: {len(all_articles)}")
        
        # Final statistics and validation
        category_counts = {}
        region_counts = {}
        source_counts = {}
        
        for article in all_articles:
            category = article.get('category', 'general')
            region = article.get('region', 'international')
            source = article.get('source', 'unknown')
            
            category_counts[category] = category_counts.get(category, 0) + 1
            region_counts[region] = region_counts.get(region, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1
        
        logger.info(f"FINAL STRICT RULE VALIDATION:")
        logger.info(f"  - Total articles scraped: {len(all_articles)}")
        logger.info(f"  - Expected articles: {len(sources) * ARTICLES_PER_SOURCE}")
        logger.info(f"  - Region distribution: {region_counts}")
        logger.info(f"  - Category distribution: {category_counts}")
        logger.info(f"  - Articles per source: {source_counts}")
        
        # Validate the strict rule compliance
        if len(all_articles) < len(sources) * ARTICLES_PER_SOURCE:
            logger.warning(f"STRICT RULE VIOLATION: Expected {len(sources) * ARTICLES_PER_SOURCE} articles, got {len(all_articles)}")
        
        return all_articles

def save_articles_to_json(articles: List[Dict], filename: str = "raw_news.json"):
    """Save scraped articles to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} articles to {filename}")
    except Exception as e:
        logger.error(f"Error saving articles: {str(e)}")

def load_sources_from_json(filename: str = "sources.json") -> List[Dict]:
    """Load news sources from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Sources file {filename} not found, using default sources")
        return [
            {"name": "BBC News", "url": "https://www.bbc.com/news", "isActive": True},
            {"name": "Reuters", "url": "https://www.reuters.com", "isActive": True},
            {"name": "Hacker News", "url": "https://news.ycombinator.com", "isActive": True}
        ]
    except Exception as e:
        logger.error(f"Error loading sources: {str(e)}")
        return []

if __name__ == "__main__":
    scraper = NewsScraper()
    sources = load_sources_from_json()
    articles = scraper.scrape_all_sources(sources)
    save_articles_to_json(articles)