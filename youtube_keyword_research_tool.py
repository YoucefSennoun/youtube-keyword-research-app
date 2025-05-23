"""
YouTube Keyword Research Tool - Proof of Concept
This script demonstrates how we can collect and analyze YouTube keyword data
to help creators find high-volume, low-competition opportunities.
"""

import requests
import json
import re
import pandas as pd
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt # Matplotlib can be an optional dependency
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import html # For unescaping HTML entities if needed from titles

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeKeywordResearchTool:
    DEFAULT_API_KEY = "AIzaSyCvHOl7FIlDBp3wWnm_AccbrqD4JRSdKv4" # Default, can be overridden

    def __init__(self, api_key=None):
        """Initialize the YouTube Keyword Research Tool.
        
        Args:
            api_key (str, optional): YouTube Data API key. If not provided or initialization fails,
                                    the tool will rely on scraping methods.
        """
        self.api_key = api_key if api_key else self.DEFAULT_API_KEY
        self.youtube = None
        
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                logger.info("YouTube API client initialized successfully.")
            except HttpError as e:
                logger.warning(f"Failed to initialize YouTube API client (HttpError: {e.resp.status} {e.reason}). Falling back to scraping methods. Check API key and quotas.")
                self.youtube = None # Ensure it's None
            except Exception as e:
                logger.error(f"An unexpected error occurred initializing YouTube API client: {e}. Falling back to scraping methods.")
                self.youtube = None # Ensure it's None
        else:
            logger.info("No API key provided. Relying on scraping methods.")

    def get_autocomplete_suggestions(self, keyword, max_suggestions=10):
        """Get keyword suggestions from YouTube's autocomplete.
        Args:
            keyword (str): The seed keyword
            max_suggestions (int): Maximum number of suggestions to return
        Returns:
            list: List of keyword suggestions
        """
        try:
            url = f"https://clients1.google.com/complete/search?client=youtube&ds=yt&q={requests.utils.quote(keyword)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Explicitly set verify=True for SSL certificate verification
            response = requests.get(url, headers=headers, timeout=10, verify=True)
            response.raise_for_status()
            content = response.text.strip()
            # Remove JSONP wrapper like )]}' or window.google.ac.h(...)\
            if content.startswith(")]}'"):
                content = content[5:]
            elif content.startswith("window.google.ac.h("):
                content = content[len("window.google.ac.h("):-1]
            
            data = json.loads(content)
            
            suggestions = []
            if len(data) > 1 and isinstance(data[1], list):
                for item in data[1]:
                    if isinstance(item, list) and len(item) > 0 and isinstance(item[0], str):
                        suggestions.append(item[0])
                    if len(suggestions) >= max_suggestions:
                        break
            return suggestions
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error fetching autocomplete suggestions for '{keyword}': {e}. Check system certificates or network.")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error fetching autocomplete suggestions for '{keyword}': {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON for autocomplete suggestions for '{keyword}': {e} - Content: {content[:200]}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_autocomplete_suggestions for '{keyword}': {e}")
            return []
    
    def _parse_view_count(self, view_str):
        view_str = view_str.lower().replace(',', '').replace(' views', '').strip()
        multiplier = 1
        if 'k' in view_str:
            multiplier = 1000
            view_str = view_str.replace('k', '')
        elif 'm' in view_str:
            multiplier = 1000000
            view_str = view_str.replace('m', '')
        elif 'b' in view_str:
            multiplier = 1000000000
            view_str = view_str.replace('b', '')
        try:
            return float(view_str) * multiplier
        except ValueError:
            return 0

    def _estimate_search_volume_api(self, keyword):
        try:
            search_response = self.youtube.search().list(
                q=keyword,
                part='id,snippet',
                maxResults=10, # Analyze top 10 videos for volume estimation
                type='video',
                relevanceLanguage='en', # Optional: specify language
                regionCode='US' # Optional: specify region
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', []) if 'videoId' in item.get('id', {})]
            
            if not video_ids:
                return {'estimated_volume': 0, 'confidence': 'low', 'data_points': {'reason': 'No videos found'}}
            
            video_response = self.youtube.videos().list(
                part='statistics', 
                id=','.join(video_ids)
            ).execute()
            
            view_counts = [int(item['statistics']['viewCount']) for item in video_response.get('items', []) if 'statistics' in item and 'viewCount' in item['statistics']]
            
            if not view_counts:
                return {'estimated_volume': 0, 'confidence': 'low', 'data_points': {'reason': 'No view counts for found videos'}}
            
            avg_views = sum(view_counts) / len(view_counts)
            total_results = search_response.get('pageInfo', {}).get('totalResults', 0)
            
            estimated_volume = 500 # Base
            if total_results > 1000000: estimated_volume = 450000
            elif total_results > 100000: estimated_volume = 100000
            elif total_results > 10000: estimated_volume = 30000
            elif total_results > 1000: estimated_volume = 5000
            
            if avg_views > 1000000: estimated_volume *= 3
            elif avg_views > 100000: estimated_volume *= 2
            elif avg_views < 1000: estimated_volume *= 0.5
            
            volume_category = "very low"
            if estimated_volume > 200000: volume_category = "very high"
            elif estimated_volume > 50000: volume_category = "high"
            elif estimated_volume > 10000: volume_category = "medium"
            elif estimated_volume > 2000: volume_category = "low"

            return {
                'estimated_volume': int(estimated_volume),
                'volume_category': volume_category,
                'confidence': 'medium',
                'data_points': {
                    'total_api_results': total_results,
                    'videos_analyzed': len(view_counts),
                    'avg_views_top_10': int(avg_views),
                }
            }
        except HttpError as e:
            logger.error(f"API error estimating search volume for '{keyword}': {e.resp.status} {e.reason}")
            return {'estimated_volume': 0, 'confidence': 'none', 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected API error estimating search volume for '{keyword}': {e}")
            return {'estimated_volume': 0, 'confidence': 'none', 'error': str(e)}

    def _estimate_search_volume_scrape(self, keyword):
        try:
            formatted_keyword = requests.utils.quote(keyword)
            url = f"https://www.youtube.com/results?search_query={formatted_keyword}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            # Explicitly set verify=True for SSL certificate verification
            response = requests.get(url, headers=headers, timeout=15, verify=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            video_count_on_page = 0
            view_counts = []
            
            # More robust way to find initial data blob if available
            # This often contains structured data for videos on the page.
            # This part is highly dependent on YouTube's current HTML structure.
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'ytInitialData' in script.string:
                    try:
                        # Find the line containing ytInitialData and extract the JSON part
                        match = re.search(r'var ytInitialData = ({.*?});', script.string)
                        if not match:
                             match = re.search(r'window\[\"ytInitialData\"\] = ({.*?});', script.string)
                        if match:
                            initial_data = json.loads(match.group(1))
                            # Navigate through the complex structure to find video renderers
                            # This path can change frequently with YouTube updates.
                            # Example path (needs verification and error handling):
                            contents = initial_data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
                            for content_item in contents:
                                item_section_contents = content_item.get('itemSectionRenderer', {}).get('contents', [])
                                for item in item_section_contents:
                                    if 'videoRenderer' in item:
                                        video_count_on_page += 1
                                        renderer = item['videoRenderer']
                                        if 'viewCountText' in renderer and isinstance(renderer['viewCountText'], dict) and 'simpleText' in renderer['viewCountText']:
                                            view_str = renderer['viewCountText']['simpleText']
                                            views = self._parse_view_count(view_str)
                                            if views > 0: view_counts.append(views)
                                        elif 'viewCountText' in renderer and isinstance(renderer['viewCountText'], dict) and 'runs' in renderer['viewCountText']:
                                            # Handle cases like "1.2K views"
                                            full_view_text = "".join([run.get('text', '') for run in renderer['viewCountText']['runs']])
                                            views = self._parse_view_count(full_view_text)
                                            if views > 0: view_counts.append(views)
                            break # Found ytInitialData, no need to check other scripts for it
                    except json.JSONDecodeError as je:
                        logger.warning(f"JSONDecodeError while parsing ytInitialData for '{keyword}': {je}")
                    except Exception as ex:
                        logger.warning(f"Error parsing ytInitialData structure for '{keyword}': {ex}")

            if video_count_on_page == 0: # Fallback if ytInitialData parsing failed
                 # Fallback to less reliable regex on whole page content (original approach with fixes)
                view_pattern = r'\"viewCountText\":\s*\{\"simpleText\":\"([^\"}]*)\"\}' # Fixed regex
                matches = re.findall(view_pattern, response.text)
                for view_str in matches:
                    views = self._parse_view_count(view_str)
                    if views > 0: view_counts.append(views)
                video_count_on_page = len(view_counts) # Approximation

            avg_views = (sum(view_counts) / len(view_counts)) if view_counts else 0
            
            estimated_volume = 400 # Base for scraping
            if video_count_on_page > 20: estimated_volume = 350000 # Assuming a full page of relevant results indicates high interest
            elif video_count_on_page > 15: estimated_volume = 80000
            elif video_count_on_page > 10: estimated_volume = 25000
            elif video_count_on_page > 5: estimated_volume = 4000

            if avg_views > 1000000: estimated_volume *= 2.5
            elif avg_views > 100000: estimated_volume *= 1.5
            elif avg_views < 1000 and avg_views > 0: estimated_volume *= 0.6
            elif avg_views == 0 and video_count_on_page > 0 : estimated_volume *=0.2 # Penalize if videos found but no views parsed
            
            volume_category = "very low"
            if estimated_volume > 150000: volume_category = "very high"
            elif estimated_volume > 40000: volume_category = "high"
            elif estimated_volume > 8000: volume_category = "medium"
            elif estimated_volume > 1500: volume_category = "low"

            return {
                'estimated_volume': int(estimated_volume),
                'volume_category': volume_category,
                'confidence': 'low', 
                'data_points': {
                    'videos_found_on_page': video_count_on_page,
                    'videos_analyzed_for_views': len(view_counts),
                    'avg_views_on_page': int(avg_views),
                }
            }
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error scraping search volume ('{keyword}'): {e}. Check system certificates or network.")
            return {'estimated_volume': 0, 'confidence': 'none', 'error': str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error scraping search volume ('{keyword}'): {e}")
            return {'estimated_volume': 0, 'confidence': 'none', 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected scraping error for search volume ('{keyword}'): {e}")
            return {'estimated_volume': 0, 'confidence': 'none', 'error': str(e)}

    def estimate_search_volume(self, keyword):
        if self.youtube:
            return self._estimate_search_volume_api(keyword)
        else:
            logger.info(f"Using scraping method for search volume estimation for '{keyword}'.")
            return self._estimate_search_volume_scrape(keyword)

    def _estimate_competition_api(self, keyword):
        try:
            search_response = self.youtube.search().list(
                q=keyword,
                part='id,snippet',
                maxResults=20, # Analyze top 20 videos
                type='video'
            ).execute()
            
            video_items = search_response.get('items', [])
            if not video_items:
                return {'competition_score': 100, 'level': 'unknown', 'data_points': {'reason': 'No videos found for competition analysis'}}

            video_ids = [item['id']['videoId'] for item in video_items if 'videoId' in item.get('id', {})]
            channel_ids = list(set([item['snippet']['channelId'] for item in video_items if 'snippet' in item and 'channelId' in item['snippet']]))

            if not video_ids:
                 return {'competition_score': 100, 'level': 'unknown', 'data_points': {'reason': 'No video IDs extracted'}}

            video_details_response = self.youtube.videos().list(part='statistics,snippet', id=','.join(video_ids)).execute()
            video_details_items = video_details_response.get('items', [])

            subscriber_counts = []
            if channel_ids:
                # Batched channel requests
                for i in range(0, len(channel_ids), 50):
                    batch_ids = channel_ids[i:i+50]
                    try:
                        channel_response = self.youtube.channels().list(part='statistics', id=','.join(batch_ids)).execute()
                        for channel_item in channel_response.get('items', []):
                            if 'statistics' in channel_item and 'subscriberCount' in channel_item['statistics']:
                                subscriber_counts.append(int(channel_item['statistics']['subscriberCount']))
                    except HttpError as he:
                        logger.warning(f"API error fetching channel batch for competition: {he.resp.status} {he.reason}")
                    except Exception as ex:
                         logger.warning(f"Error fetching channel batch details: {ex}")
            
            large_channels = sum(1 for sc in subscriber_counts if sc > 1000000)
            medium_channels = sum(1 for sc in subscriber_counts if 10000 < sc <= 1000000)
            
            channel_score_factor = (large_channels * 3 + medium_channels * 1.5) / len(video_items) if video_items else 0 # Normalize by num videos in SERP
            channel_score = min(50, channel_score_factor * 20) # Max 50 points from channel size

            title_matches = 0
            keyword_lower = keyword.lower()
            for item in video_details_items:
                if 'snippet' in item and 'title' in item['snippet']:
                    if keyword_lower in item['snippet']['title'].lower():
                        title_matches += 1
            
            title_match_ratio = title_matches / len(video_details_items) if video_details_items else 0
            title_score = min(30, title_match_ratio * 50) # Max 30 points from title matches
            
            # Base difficulty and other factors (e.g. video age, engagement - not implemented for API POC)
            base_difficulty = 20
            competition_score = min(100, int(channel_score + title_score + base_difficulty))
            
            level = "very low"
            if competition_score >= 80: level = "very high"
            elif competition_score >= 60: level = "high"
            elif competition_score >= 40: level = "medium"
            elif competition_score >= 20: level = "low"
            
            return {
                'competition_score': competition_score,
                'level': level,
                'data_points': {
                    'top_20_videos_analyzed': len(video_details_items),
                    'channels_analyzed': len(subscriber_counts),
                    'large_channels_in_top_20': large_channels,
                    'medium_channels_in_top_20': medium_channels,
                    'exact_keyword_in_title_ratio': round(title_match_ratio, 2),
                }
            }
        except HttpError as e:
            logger.error(f"API error estimating competition for '{keyword}': {e.resp.status} {e.reason}")
            return {'competition_score': 0, 'level': 'unknown', 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected API error estimating competition for '{keyword}': {e}")
            return {'competition_score': 0, 'level': 'unknown', 'error': str(e)}

    def _estimate_competition_scrape(self, keyword):
        try:
            formatted_keyword = requests.utils.quote(keyword)
            url = f"https://www.youtube.com/results?search_query={formatted_keyword}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            # Explicitly set verify=True for SSL certificate verification
            response = requests.get(url, headers=headers, timeout=15, verify=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            total_video_renderers = 0
            exact_phrase_in_title_count = 0
            verified_badge_count = 0 # Approx
            # recent_videos_count = 0 # Approx, simplified

            unique_titles_on_page = []
            scripts = soup.find_all('script')
            keyword_lower = keyword.lower()

            # Try to parse ytInitialData first for more structured data
            parsed_from_initial_data = False
            for script in scripts:
                if script.string and 'ytInitialData' in script.string:
                    try:
                        match = re.search(r'var ytInitialData = ({.*?});', script.string) or re.search(r'window\[\"ytInitialData\"\] = ({.*?});', script.string)
                        if match:
                            initial_data = json.loads(match.group(1))
                            contents = initial_data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
                            current_titles = []
                            for content_item in contents:
                                item_section_contents = content_item.get('itemSectionRenderer', {}).get('contents', [])
                                for item in item_section_contents:
                                    if 'videoRenderer' in item:
                                        total_video_renderers +=1
                                        renderer = item['videoRenderer']
                                        title_text = None
                                        if 'title' in renderer and 'runs' in renderer['title'] and renderer['title']['runs']:\
                                            title_text = renderer['title']['runs'][0].get('text', '')
                                        elif 'title' in renderer and 'simpleText' in renderer['title']:\
                                            title_text = renderer['title']['simpleText']
                                        
                                        if title_text:
                                            decoded_title = html.unescape(title_text.lower())
                                            if decoded_title not in current_titles:
                                                current_titles.append(decoded_title)
                                                if keyword_lower in decoded_title:
                                                    exact_phrase_in_title_count += 1
                                        
                                        if 'ownerBadges' in renderer:
                                            for badge in renderer['ownerBadges']:
                                                if badge.get('metadataBadgeRenderer',{}).get('tooltip', '') == 'Verified':
                                                    verified_badge_count +=1
                                                    break # count channel once
                            unique_titles_on_page = current_titles
                            parsed_from_initial_data = True
                            break 
                    except Exception as ex:
                        logger.warning(f"Error parsing ytInitialData for competition_scrape '{keyword}': {ex}")
            
            if not parsed_from_initial_data: # Fallback regex if ytInitialData fails
                logger.info(f"Falling back to broader regex for competition scrape for '{keyword}'.")
                total_video_renderers = response.text.count("videoRenderer") # Original count
                
                title_candidates_regex = r'\"title\":\s*\{(?:(?:\"simpleText\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\")|(?:\"runs\"\\s*:\\s*\\[\\s*\\{\"text\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"\\}\\s*\\]))'
                title_matches_re = re.findall(title_candidates_regex, response.text)
                
                temp_unique_titles = []
                for tc in title_matches_re:
                    title_text = tc[0] if tc[0] else tc[1]
                    if title_text:
                        try:
                            decoded_title = title_text.encode('utf-8').decode('unicode-escape').lower()
                            decoded_title = html.unescape(decoded_title)
                        except Exception:
                            decoded_title = title_text.lower()
                        
                        if decoded_title not in temp_unique_titles:
                            temp_unique_titles.append(decoded_title)
                            if keyword_lower in decoded_title:
                                exact_phrase_in_title_count += 1
                unique_titles_on_page = temp_unique_titles
                # verified_badge_count with regex is less reliable, stick to initialData if possible or simplify
                verified_badge_count = response.text.count('\"tooltip\":\"Verified\"') # very rough estimate

            if total_video_renderers == 0 and unique_titles_on_page: # If renderers count failed but titles found
                total_video_renderers = len(unique_titles_on_page)
            
            title_match_ratio = (exact_phrase_in_title_count / len(unique_titles_on_page)) if unique_titles_on_page else 0
            verified_ratio = (verified_badge_count / total_video_renderers) if total_video_renderers > 0 else 0
            # recency_score - original was complex and unreliable, simplifying or omitting for POC stability
            
            title_score = min(50, title_match_ratio * 60)  # Increased weight, max 50
            verified_score = min(30, verified_ratio * 50) # Max 30
            base_difficulty = 20 # Base score
            competition_score = min(100, int(title_score + verified_score + base_difficulty))

            level = "very low"
            if competition_score >= 80: level = "very high"
            elif competition_score >= 60: level = "high"
            elif competition_score >= 40: level = "medium"
            elif competition_score >= 20: level = "low"
            
            return {
                'competition_score': competition_score,
                'level': level,
                'data_points': {
                    'video_renderers_on_page': total_video_renderers,
                    'unique_titles_analyzed': len(unique_titles_on_page),
                    'exact_phrase_title_matches': exact_phrase_in_title_count,
                    'title_match_ratio': round(title_match_ratio, 2),
                    'verified_badge_ratio_approx': round(verified_ratio, 2),
                }
            }
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error scraping competition ('{keyword}'): {e}. Check system certificates or network.")
            return {'competition_score': 0, 'level': 'unknown', 'error': str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error scraping competition ('{keyword}'): {e}")
            return {'competition_score': 0, 'level': 'unknown', 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected scraping error for competition ('{keyword}'): {e}")
            return {'competition_score': 0, 'level': 'unknown', 'error': str(e)}

    def estimate_competition(self, keyword):
        if self.youtube:
            return self._estimate_competition_api(keyword)
        else:
            logger.info(f"Using scraping method for competition estimation for '{keyword}'.")
            return self._estimate_competition_scrape(keyword)
    
    def calculate_opportunity_score(self, search_volume, competition_score):
        """Calculates an opportunity score based on search volume and competition."""
        if search_volume == 0 and competition_score == 0:
            return 0, "unknown"

        # Normalize volume and competition to a 0-100 scale for scoring
        # Assuming max search volume is very high (e.g., 500,000+) and competition is 0-100
        normalized_volume = min(100, search_volume / 5000) # Example normalization, adjust as needed
        normalized_competition = 100 - competition_score # Invert competition: lower is better

        # Weighted average or formula
        # Give more weight to volume but also consider competition heavily
        score = (normalized_volume * 0.6) + (normalized_competition * 0.4)
        score = int(min(100, max(0, score))) # Ensure score is between 0 and 100

        level = "poor"
        if score >= 80: level = "excellent"
        elif score >= 60: level = "good"
        elif score >= 40: level = "average"
        elif score >= 20: level = "low"
        
        return score, level

    def find_opportunities(self, seed_keyword, depth=1, max_keywords=20):
        """
        Finds keyword opportunities based on a seed keyword, considering search volume and competition.
        Args:
            seed_keyword (str): The initial keyword to start the research.
            depth (int): How many levels of suggestions to explore (1: just seed, 2: seed + 1 level, etc.)
            max_keywords (int): Maximum number of unique keywords to analyze.
        Returns:
            pd.DataFrame: A DataFrame with keyword, search volume, competition, and opportunity scores.
        """
        unique_keywords = set()
        keywords_to_process = [seed_keyword]
        processed_keywords = set()
        all_keyword_data = []

        logger.info(f"Starting keyword research for '{seed_keyword}' with depth {depth} and max results {max_keywords}.")

        for current_depth in range(depth):
            next_level_keywords = set()
            
            # Use ThreadPoolExecutor for parallel processing of keywords at each level
            with ThreadPoolExecutor(max_workers=5) as executor: # Limit concurrent requests
                future_to_keyword = {executor.submit(self.get_autocomplete_suggestions, kw): kw for kw in keywords_to_process if kw not in processed_keywords}
                
                for future in as_completed(future_to_keyword):
                    kw = future_to_keyword[future]
                    processed_keywords.add(kw) # Mark as processed before getting results
                    try:
                        suggestions = future.result()
                        for s in suggestions:
                            if s not in unique_keywords and len(unique_keywords) < max_keywords:
                                unique_keywords.add(s)
                                next_level_keywords.add(s)
                    except Exception as exc:
                        logger.error(f"Keyword generation for {kw} generated an exception: {exc}")
            
            keywords_to_process = list(next_level_keywords)
            if not keywords_to_process:
                break # No new keywords to process for the next depth

        # Include the seed keyword itself in the analysis
        if seed_keyword not in unique_keywords:
            unique_keywords.add(seed_keyword)

        logger.info(f"Analyzing {len(unique_keywords)} unique keywords.")
        
        # Analyze each unique keyword for volume and competition
        with ThreadPoolExecutor(max_workers=3) as executor: # Limit concurrent heavy analysis requests
            future_to_analysis = {executor.submit(self._analyze_single_keyword, kw): kw for kw in list(unique_keywords)}

            for future in as_completed(future_to_analysis):
                kw = future_to_analysis[future]
                try:
                    data = future.result()
                    if data:
                        all_keyword_data.append(data)
                except Exception as exc:
                    logger.error(f"Keyword analysis for {kw} generated an exception: {exc}")
                
                # Simple rate limiting for API/scraping calls
                time.sleep(0.5) # Adjust as needed

        if not all_keyword_data:
            logger.warning("No keyword data collected.")
            return pd.DataFrame()

        df = pd.DataFrame(all_keyword_data)
        df = df.sort_values(by='opportunity_score', ascending=False).reset_index(drop=True)
        logger.info("Keyword analysis complete.")
        return df

    def _analyze_single_keyword(self, keyword):
        """Helper to analyze a single keyword's volume, competition, and score."""
        logger.debug(f"Analyzing single keyword: '{keyword}'")
        volume_data = self.estimate_search_volume(keyword)
        competition_data = self.estimate_competition(keyword)

        estimated_volume = volume_data.get('estimated_volume', 0)
        competition_score = competition_data.get('competition_score', 100) # Default to high competition

        opportunity_score, opportunity_level = self.calculate_opportunity_score(estimated_volume, competition_score)

        return {
            'keyword': keyword,
            'search_volume_est': estimated_volume,
            'volume_category': volume_data.get('volume_category', 'unknown'),
            'competition_score': competition_score,
            'competition_level': competition_data.get('level', 'unknown'),
            'opportunity_score': opportunity_score,
            'opportunity_level': opportunity_level,
            'volume_data_points': volume_data.get('data_points', {}),
            'competition_data_points': competition_data.get('data_points', {}),
        }

    def visualize_opportunities(self, df):
        """
        Creates a simple visualization of keyword opportunities.
        Requires matplotlib to be installed.
        Args:
            df (pd.DataFrame): DataFrame containing keyword analysis results.
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            if df.empty:
                logger.info("No data to visualize.")
                return

            # Sort by opportunity score for better visualization
            df_sorted = df.sort_values(by='opportunity_score', ascending=False).head(20) # Top N keywords

            plt.figure(figsize=(12, 8))
            sns.barplot(x='opportunity_score', y='keyword', hue='opportunity_level', data=df_sorted, dodge=False,
                        palette={'excellent': '#28a745', 'good': '#ffc107', 'average': '#17a2b8', 'low': '#007bff', 'poor': '#dc3545', 'unknown': '#6c757d'})
            
            plt.title('Top Keyword Opportunities by Score')
            plt.xlabel('Opportunity Score')
            plt.ylabel('Keyword')
            plt.xlim(0, 100) # Scores are 0-100

            plt.tight_layout()
            plt.show()

            # Optional: Another plot for volume vs competition
            plt.figure(figsize=(10, 6))
            sns.scatterplot(x='search_volume_est', y='competition_score', hue='opportunity_level', size='opportunity_score', sizes=(50, 500), data=df,
                            palette={'excellent': '#28a745', 'good': '#ffc107', 'average': '#17a2b8', 'low': '#007bff', 'poor': '#dc3545', 'unknown': '#6c757d'},
                            legend='full')
            
            plt.title('Keyword Volume vs. Competition with Opportunity Score')
            plt.xlabel('Estimated Monthly Search Volume')
            plt.ylabel('Competition Score (0-100)')
            
            if df['search_volume_est'].max() > 10000: # Use log scale if wide range of volumes
                ax = plt.gca()
                ax.set_xscale('log')
                ax.set_xlabel('Estimated Monthly Search Volume (Log Scale)')
            
            plt.tight_layout()
            plt.show()
            logger.info("Visualization displayed.")
        except ImportError:
            logger.warning("Matplotlib or Seaborn not installed. Skipping visualization.")
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")

# Example usage:
if __name__ == "__main__":
    # Uses default API_KEY from class or falls back to scraping if key is invalid/missing.
    tool = YouTubeKeywordResearchTool() 
    # To force scraping, initialize with: tool = YouTubeKeywordResearchTool(api_key=None)
    
    seed_keyword = "ai content creation tools"
    print(f"Finding keyword opportunities for: '{seed_keyword}'")
    
    results_df = tool.find_opportunities(seed_keyword, depth=1, max_keywords=10)
    
    if not results_df.empty:
        print("\nTop keyword opportunities:")
        print(results_df[['keyword', 'search_volume_est', 'competition_score', 'opportunity_score', 'opportunity_level']].head(10).to_string())
        
        # Visualize results (requires matplotlib)
        tool.visualize_opportunities(results_df)
    else:
        print("No results found...")
