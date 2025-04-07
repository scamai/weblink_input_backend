import os
import sys
import tempfile
import time
import yt_dlp
import requests
import numpy as np
import cv2
from frame_extractors.common_utils import download_media, extract_frames_from_video, process_as_image

def get_twitter_stream(url, max_retries=3):
    """Get video stream URL for Twitter/X posts"""
    import random
    import json
    import re
    
    # Extract tweet ID from URL
    tweet_id = None
    tweet_id_match = re.search(r'twitter\.com/[^/]+/status/(\d+)', url) or re.search(r'x\.com/[^/]+/status/(\d+)', url)
    if tweet_id_match:
        tweet_id = tweet_id_match.group(1)
        print(f"Extracted tweet ID: {tweet_id}")
    
    for attempt in range(max_retries):
        try:
            # First try: Use yt-dlp with specific options for Twitter
            ydl_opts = {
                'no_playlist': True,
                'extract_flat': False,
                'ignore_no_formats_error': True,
                'dump_single_json': True,
                'force_generic_extractor': False,
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                },
            }
            
            print('Starting yt-dlp for Twitter/X')
            # Create yt-dlp object with options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    print("Could not extract Twitter/X information, trying alternative methods")
                else:
                    # Print debug info (helpful for debugging)
                    print(f"Info keys: {list(info.keys())}")
                    
                    # Store platform in the return value for special handling
                    result = {'platform': 'twitter', 'original_url': url}
                    
                    print("Processing Twitter/X post")
                    
                    # First check for direct media URLs
                    if 'url' in info and info['url']:
                        media_url = info['url']
                        print(f"Found direct media URL: {media_url}")
                        # Determine if it's an image or video based on URL or content type
                        if any(ext in media_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                            result['url'] = media_url
                            result['is_image'] = True
                            return result
                        else:
                            result['url'] = media_url
                            return result
                    
                    # Check for media formats (videos)
                    if 'formats' in info and info['formats']:
                        # Sort formats by quality (if available)
                        formats = sorted(info['formats'], key=lambda x: x.get('height', 0) if x.get('height') else 0, reverse=True)
                        for fmt in formats:
                            if 'url' in fmt and fmt['url']:
                                print(f"Found video format: {fmt.get('format_id', 'unknown')} - {fmt.get('height', 'unknown')}p")
                                result['url'] = fmt['url']
                                return result
                    
                    # Check for thumbnails (images)
                    if 'thumbnails' in info and info['thumbnails']:
                        # Sort thumbnails by preference (larger ones first)
                        thumbnails = sorted(info['thumbnails'], key=lambda x: x.get('width', 0) if x.get('width') else 0, reverse=True)
                        if thumbnails:
                            print(f"Found thumbnail: {thumbnails[0].get('id', 'primary')}")
                            result['url'] = thumbnails[0]['url']
                            result['is_image'] = True
                            return result
                    
                    # Check for a single thumbnail
                    if 'thumbnail' in info and info['thumbnail']:
                        print("Found single thumbnail")
                        result['url'] = info['thumbnail']
                        result['is_image'] = True
                        return result
                    
                    # Check for entries (for tweets with media collections)
                    if 'entries' in info and info['entries']:
                        for entry in info['entries']:
                            # Check for videos in entry
                            if 'formats' in entry and entry['formats']:
                                formats = sorted(entry['formats'], key=lambda x: x.get('height', 0) if x.get('height') else 0, reverse=True)
                                if formats:
                                    print(f"Found video in entry: {formats[0].get('format_id', 'unknown')}")
                                    result['url'] = formats[0]['url']
                                    return result
                            
                            # Check for thumbnails in entry
                            if 'thumbnails' in entry and entry['thumbnails']:
                                thumbnails = sorted(entry['thumbnails'], key=lambda x: x.get('width', 0) if x.get('width') else 0, reverse=True)
                                if thumbnails:
                                    print(f"Found thumbnail in entry: {thumbnails[0].get('id', 'primary')}")
                                    result['url'] = thumbnails[0]['url']
                                    result['is_image'] = True
                                    return result
                            
                            # Check for direct URL in entry
                            if 'url' in entry and entry['url']:
                                print("Found direct URL in entry")
                                result['url'] = entry['url']
                                # Try to determine if it's an image
                                if any(ext in entry['url'].lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                                    result['is_image'] = True
                                return result
            
            # Second try: Use requests to fetch the tweet page and extract media URLs
            if tweet_id:
                try:
                    print(f"Trying direct HTTP request to fetch tweet {tweet_id}")
                    # Construct the Twitter API URL for the tweet
                    tweet_url = f"https://twitter.com/i/api/graphql/1FfuALppD9ew98KZs8D6qw/TweetDetail?variables=%7B%22focalTweetId%22%3A%22{tweet_id}%22%7D"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': 'https://twitter.com/',
                        'x-twitter-active-user': 'yes',
                        'x-twitter-client-language': 'en',
                    }
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Look for image URLs in the HTML
                        html_content = response.text
                        
                        # Look for og:image meta tag
                        og_image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html_content)
                        if og_image_match:
                            image_url = og_image_match.group(1)
                            print(f"Found og:image URL: {image_url}")
                            return {'platform': 'twitter', 'url': image_url, 'is_image': True, 'original_url': url}
                        
                        # Look for twitter:image meta tag
                        twitter_image_match = re.search(r'<meta name="twitter:image" content="([^"]+)"', html_content)
                        if twitter_image_match:
                            image_url = twitter_image_match.group(1)
                            print(f"Found twitter:image URL: {image_url}")
                            return {'platform': 'twitter', 'url': image_url, 'is_image': True, 'original_url': url}
                        
                        # Look for any image URLs in the page
                        image_urls = re.findall(r'https://pbs\.twimg\.com/media/[^\s"]+', html_content)
                        if image_urls:
                            print(f"Found image URL in page: {image_urls[0]}")
                            return {'platform': 'twitter', 'url': image_urls[0], 'is_image': True, 'original_url': url}
                        
                        # Look for video URLs
                        video_urls = re.findall(r'https://video\.twimg\.com/[^\s"]+\.mp4', html_content)
                        if video_urls:
                            print(f"Found video URL in page: {video_urls[0]}")
                            return {'platform': 'twitter', 'url': video_urls[0], 'original_url': url}
                except Exception as req_err:
                    print(f"Error with direct HTTP request: {str(req_err)}")
            
            # Third try: Use a fallback approach with yt-dlp
            try:
                print("Trying alternative yt-dlp configuration...")
                
                alt_opts = {
                    'format': 'best',
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'force_generic_extractor': True,  # Try generic extractor
                }
                
                with yt_dlp.YoutubeDL(alt_opts) as alt_ydl:
                    alt_info = alt_ydl.extract_info(url, download=False, process=True)
                    if alt_info:
                        # Check for direct URL
                        if 'url' in alt_info and alt_info['url']:
                            print("Found URL with alternative options")
                            return {'platform': 'twitter', 'url': alt_info['url'], 'original_url': url}
                        
                        # Check for formats
                        if 'formats' in alt_info and alt_info['formats']:
                            print("Found formats with alternative options")
                            return {'platform': 'twitter', 'url': alt_info['formats'][0]['url'], 'original_url': url}
                        
                        # Check for thumbnail
                        if 'thumbnail' in alt_info and alt_info['thumbnail']:
                            print("Found thumbnail with alternative options")
                            return {'platform': 'twitter', 'url': alt_info['thumbnail'], 'is_image': True, 'original_url': url}
            except Exception as alt_err:
                print(f"Alternative approach failed: {str(alt_err)}")
            
            # Last resort: Create a placeholder image with the tweet ID
            if tweet_id:
                print("Creating placeholder with tweet ID")
                # Return a special flag to indicate we should create a placeholder
                return {
                    'platform': 'twitter',
                    'create_placeholder': True,
                    'tweet_id': tweet_id,
                    'original_url': url
                }
                
            raise Exception("No suitable media found in Twitter/X post")
                
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print("Max retries reached. Please check if the Twitter/X URL is valid and accessible.")
                # Return a placeholder creation instruction as last resort
                if tweet_id:
                    return {
                        'platform': 'twitter',
                        'create_placeholder': True,
                        'tweet_id': tweet_id,
                        'original_url': url
                    }
                return None
                
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print("Max retries reached. Please check if the Twitter/X URL is valid and accessible.")
                return None

def extract_twitter_frames(media_info, output_folder, num_frames=5):
    """Extract frames from Twitter/X posts"""
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Handle both string URLs and dictionary format
        if isinstance(media_info, dict):
            # Check if we need to create a placeholder (no media found)
            if media_info.get('create_placeholder', False):
                print("Creating placeholder for tweet with no extractable media")
                tweet_id = media_info.get('tweet_id', 'unknown')
                original_url = media_info.get('original_url', 'unknown')
                
                # Create a blank image with tweet information
                placeholder = np.zeros((720, 1280, 3), dtype=np.uint8)
                # Add text explaining the tweet
                cv2.putText(placeholder, f"Twitter/X Tweet ID: {tweet_id}", (320, 300), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(placeholder, f"URL: {original_url}", (320, 360), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                cv2.putText(placeholder, "Media could not be extracted", (320, 420), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 255), 2)
                
                # Save the placeholder
                placeholder_path = os.path.join(output_folder, 'frame_1.jpg')
                cv2.imwrite(placeholder_path, placeholder)
                print(f'Saved placeholder to {placeholder_path}')
                return True
            
            media_url = media_info.get('url')
            is_image = media_info.get('is_image', False)
            original_url = media_info.get('original_url', None)
        else:
            # For backward compatibility
            media_url = media_info
            is_image = False
            original_url = None
        
        print(f"Processing Twitter/X media URL: {media_url}")
        print(f"Is image: {is_image}")
        
        # If it's an image URL, download and save it directly
        if is_image:
            print("Processing as image")
            return process_as_image(media_url, output_folder, platform='twitter')
        
        # Special handling for Twitter/X videos
        print("Using special handling for Twitter/X media")
        
        # Create a temporary file to store the video
        temp_video_path = os.path.join(tempfile.gettempdir(), f"temp_video_{int(time.time())}.mp4")
        
        # Try to download the media with proper headers
        print(f"Downloading media to {temp_video_path}")
        download_success = download_media(media_url, temp_video_path, platform='twitter')
        
        if not download_success:
            print("Failed to download Twitter/X media with standard method")
            
            # Try direct download with yt-dlp as fallback
            try:
                print("Trying direct download with yt-dlp")
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': temp_video_path,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                # Use original URL if available
                download_url = original_url if original_url else media_url
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([download_url])
                    download_success = True
                    print("Successfully downloaded with yt-dlp")
            except Exception as ydl_err:
                print(f"yt-dlp download failed: {str(ydl_err)}")
                download_success = False
        
        if not download_success:
            print("All download methods failed")
            return False
            
        print(f"Media downloaded to temporary file: {temp_video_path}")
        
        # Check if the file exists and has content
        if not os.path.exists(temp_video_path) or os.path.getsize(temp_video_path) == 0:
            print("Downloaded file is empty or does not exist")
            return False
        
        # Try to process as video first
        try:
            # Process the local video file
            cap = cv2.VideoCapture(temp_video_path)
            if cap.isOpened():
                print("Successfully opened as video")
                # Get video properties
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = frame_count / fps if fps > 0 else 0
                print(f"Video properties: {frame_count} frames, {fps} FPS, {duration:.2f} seconds")
                
                cap.release()
                return extract_frames_from_video(temp_video_path, output_folder, num_frames, try_delete_temp=True)
            else:
                print("Could not open as video, trying as image")
                cap.release()
        except Exception as e:
            print(f"Error processing as video: {str(e)}")
            print("Trying as image instead")
        
        # If video processing fails, try as image
        try:
            # Try to read as image
            image = cv2.imread(temp_video_path)
            if image is not None:
                # Save the image
                image_path = os.path.join(output_folder, 'frame_1.jpg')
                cv2.imwrite(image_path, image)
                print(f'Saved image to {image_path}')
                
                # Clean up temp file
                try:
                    os.remove(temp_video_path)
                    print("Temporary file deleted")
                except Exception as e:
                    print(f"Failed to delete temporary file: {str(e)}")
                    
                return True
            else:
                print("Failed to process media as either video or image")
                
                # As a last resort, try to create a simple frame with text
                try:
                    print("Creating placeholder frame with text")
                    # Create a blank image
                    placeholder = np.zeros((720, 1280, 3), dtype=np.uint8)
                    # Add text explaining the issue
                    cv2.putText(placeholder, "Twitter media could not be processed", (320, 360), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    # Save the placeholder
                    placeholder_path = os.path.join(output_folder, 'frame_1.jpg')
                    cv2.imwrite(placeholder_path, placeholder)
                    print(f'Saved placeholder to {placeholder_path}')
                    return True
                except Exception as placeholder_err:
                    print(f"Failed to create placeholder: {str(placeholder_err)}")
                    return False
        except Exception as img_err:
            print(f"Error processing as image: {str(img_err)}")
            return False
    except Exception as e:
        print(f"Error extracting Twitter/X frames: {str(e)}")
        return False