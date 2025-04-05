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
    
    for attempt in range(max_retries):
        try:
            # Configure yt-dlp options for Twitter/X
            ydl_opts = {
                'no_playlist': True,
                'extract_flat': 'in_playlist',
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
                    raise Exception("Could not extract Twitter/X information")
                
                # Store platform in the return value for special handling
                result = {'platform': 'twitter', 'original_url': url}
                
                print("Processing Twitter/X post")
                
                # Check if it's an image post
                if 'thumbnail' in info:
                    print("Detected Twitter/X image")
                    result['url'] = info['thumbnail']
                    result['is_image'] = True
                    return result
                    
                # Check for media in entries (for tweets with images/videos)
                if 'entries' in info and info.get('_type') == 'playlist':
                    for entry in info['entries']:
                        # Check for images
                        if entry.get('_type') == 'image' or 'thumbnail' in entry:
                            print("Detected Twitter/X image in entries")
                            result['url'] = entry.get('url') or entry.get('thumbnail')
                            result['is_image'] = True
                            return result
                        # Check for videos
                        if 'formats' in entry and len(entry['formats']) > 0:
                            video_url = entry['formats'][0]['url']
                            print(f"Twitter/X video URL from entries: {video_url}")
                            result['url'] = video_url
                            return result
                
                # Try to extract any image from the tweet
                try:
                    if isinstance(info, dict):
                        for key in ['thumbnails', 'thumbnail_url', 'thumbnail', 'webpage_url_thumbnail']:
                            if key in info and info[key]:
                                print(f"Found Twitter/X image in {key}")
                                if isinstance(info[key], list) and len(info[key]) > 0:
                                    result['url'] = info[key][0]['url'] if isinstance(info[key][0], dict) else info[key][0]
                                else:
                                    result['url'] = info[key]
                                result['is_image'] = True
                                return result
                except Exception as e:
                    print(f"Error extracting Twitter/X images: {str(e)}")
                
                # Otherwise treat as video
                if 'formats' in info and len(info['formats']) > 0:
                    video_url = info['formats'][0]['url']
                    print(f"Twitter/X video URL: {video_url}")
                    result['url'] = video_url
                    return result
                
                # Additional fallback for Twitter/X
                # Try to find any URL that might be a video or image
                if 'url' in info:
                    result['url'] = info['url']
                    return result
                
                # Last resort: check if the original URL is directly accessible
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'image' in content_type:
                            result['url'] = url
                            result['is_image'] = True
                            return result
                        elif 'video' in content_type:
                            result['url'] = url
                            return result
                except Exception as e:
                    print(f"Error checking original URL: {str(e)}")
                    
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
                return None

def extract_twitter_frames(media_info, output_folder, num_frames=5):
    """Extract frames from Twitter/X posts"""
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Handle both string URLs and dictionary format
        if isinstance(media_info, dict):
            media_url = media_info['url']
            is_image = media_info.get('is_image', False)
            original_url = media_info.get('original_url', None)
        else:
            # For backward compatibility
            media_url = media_info
            is_image = False
            original_url = None
        
        # If it's an image URL, download and save it directly
        if is_image:
            return process_as_image(media_url, output_folder, platform='twitter')
        
        # Special handling for Twitter/X videos
        print("Using special handling for Twitter/X media")
        
        # Create a temporary file to store the video
        temp_video_path = os.path.join(tempfile.gettempdir(), f"temp_video_{int(time.time())}.mp4")
        
        # Try to download the media with proper headers
        if not download_media(media_url, temp_video_path, platform='twitter'):
            print("Failed to download Twitter/X media")
            return False
            
        print(f"Media downloaded to temporary file: {temp_video_path}")
        
        # Try to process as video first
        try:
            # Process the local video file
            cap = cv2.VideoCapture(temp_video_path)
            if cap.isOpened():
                print("Successfully opened as video")
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
                
                # Clean up temp file
                try:
                    os.remove(temp_video_path)
                    print("Temporary file deleted")
                except Exception as e:
                    print(f"Failed to delete temporary file: {str(e)}")
                    
                return False
        except Exception as img_err:
            print(f"Error processing as image: {str(img_err)}")
            
            # Clean up temp file
            try:
                os.remove(temp_video_path)
                print("Temporary file deleted")
            except Exception as e:
                print(f"Failed to delete temporary file: {str(e)}")
                
            return False
            
    except Exception as e:
        print(f"Error extracting Twitter/X frames: {str(e)}")
        return False