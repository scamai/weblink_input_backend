import os
import sys
import tempfile
import time
import yt_dlp
from frame_extractors.common_utils import download_media, extract_frames_from_video, process_as_image

def get_bilibili_stream(url, max_retries=3):
    """Get video stream URL for Bilibili videos"""
    import random
    
    for attempt in range(max_retries):
        try:
            # Configure yt-dlp options for Bilibili
            ydl_opts = {
                'extract_flat': False,  # Need full extraction for Bilibili
                'no_playlist': True,
                'format': None,  # Remove format restriction completely
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                },
            }
            
            print('Starting yt-dlp for Bilibili')
            # Create yt-dlp object with options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("Could not extract video information")
                
                # Store platform in the return value for special handling
                result = {'platform': 'bilibili'}
                
                print("Processing Bilibili video")
                # For Bilibili, we need to be more careful with format selection
                if 'formats' in info and len(info['formats']) > 0:
                    # Try to find a format that works - prioritize mp4 but accept others
                    formats = info['formats']
                    print(f"Found {len(formats)} available formats for Bilibili video")
                    
                    # First try to find an mp4 format
                    mp4_formats = [f for f in formats if f.get('ext') == 'mp4']
                    if mp4_formats:
                        video_url = mp4_formats[0]['url']
                        print(f"Selected mp4 format for Bilibili: {mp4_formats[0].get('format_id', 'unknown')}")
                    else:
                        # If no mp4, try any video format
                        video_formats = [f for f in formats if f.get('vcodec', 'none') != 'none']
                        if video_formats:
                            video_url = video_formats[0]['url']
                            print(f"Selected alternative video format for Bilibili: {video_formats[0].get('format_id', 'unknown')} (ext: {video_formats[0].get('ext', 'unknown')})")
                        else:
                            # Last resort: just use the first format
                            video_url = formats[0]['url']
                            print(f"Selected fallback format for Bilibili: {formats[0].get('format_id', 'unknown')}")
                    
                    print(f"Bilibili video URL: {video_url}")
                    result['url'] = video_url
                    return result
                
                # Check if this is an image post rather than a video
                if 'entries' in info and info.get('_type') == 'playlist':
                    for entry in info['entries']:
                        if entry.get('_type') == 'image':
                            print("Detected Bilibili image post")
                            if 'url' in entry:
                                result['url'] = entry['url']
                                result['is_image'] = True
                                return result
                            elif 'thumbnail' in entry:
                                result['url'] = entry['thumbnail']
                                result['is_image'] = True
                                return result
                
                # Fallback to thumbnail if no video URL
                if 'thumbnail' in info:
                    print("No video found, using thumbnail image")
                    result['url'] = info['thumbnail']
                    result['is_image'] = True
                    return result
                    
                raise Exception("No suitable media stream found")
                
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
                continue
            else:
                print("Max retries reached. Please check if the Bilibili URL is valid and accessible.")
                return None

def extract_bilibili_frames(media_info, output_folder, num_frames=5):
    """Extract frames from Bilibili videos"""
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
            return process_as_image(media_url, output_folder, platform='bilibili')
        
        # Special handling for Bilibili videos - download directly with yt-dlp
        print("Using special handling for Bilibili video")
        
        # Create a temporary file to store the video
        temp_video_path = os.path.join(tempfile.gettempdir(), f"temp_video_{int(time.time())}.mp4")
        
        # For Bilibili, always use the original URL with yt-dlp if available
        download_url = original_url if original_url else media_url
        
        try:
            print(f"Downloading Bilibili video from URL: {download_url}")
            ydl_opts = {
                'format': 'best',  # Get best quality
                'outtmpl': temp_video_path,  # Output to our temp file
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.bilibili.com/',  # Important for Bilibili
                },
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([download_url])
                print(f"Successfully downloaded Bilibili video to: {temp_video_path}")
            
            # Process the local video file
            return extract_frames_from_video(temp_video_path, output_folder, num_frames, try_delete_temp=True)
            
        except Exception as e:
            print(f"Error downloading Bilibili video: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error extracting Bilibili frames: {str(e)}")
        return False