import os
import sys
import cv2
import requests
import shutil
import tempfile
import time
import random
from urllib.parse import urlparse

def identify_platform(url):
    """Identify the platform from the URL"""
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            print("Invalid URL format")
            return None
            
        # Identify platform from URL
        domain = parsed.netloc.lower()
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'facebook.com' in domain or 'fb.com' in domain:
            return 'facebook'
        elif 'instagram.com' in domain:
            return 'instagram'
        elif 'tiktok.com' in domain:
            return 'tiktok'
        elif 'clapperapp' in domain:
            return 'clapper'
        elif 'bilibili.com' in domain or 'b23.tv' in domain:
            return 'bilibili'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        else:
            return 'generic'
    except Exception as e:
        print(f"URL validation error: {str(e)}")
        return None

def get_common_headers():
    """Get common headers for HTTP requests"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def download_media(url, output_path, platform=None):
    """Download media from URL with proper headers for different platforms"""
    import yt_dlp
    
    # For TikTok or Bilibili, use yt-dlp to download directly
    if platform in ['tiktok', 'bilibili'] or 'tiktok.com' in url or 'bilibili.com' in url or 'b23.tv' in url:
        try:
            print(f"Using yt-dlp to download {platform if platform else 'video'} directly")
            
            # Configure headers based on platform
            headers = get_common_headers()
            
            # Add platform-specific referer
            if platform == 'tiktok' or 'tiktok.com' in url:
                headers['Referer'] = 'https://www.tiktok.com/'
            elif platform == 'bilibili' or 'bilibili.com' in url or 'b23.tv' in url:
                headers['Referer'] = 'https://www.bilibili.com/'
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'http_headers': headers,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get the actual URL
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Could not extract video information")
                
                # Then download the video
                ydl.download([url])
                return True
        except Exception as e:
            print(f"yt-dlp download error: {str(e)}")
            # Fall back to regular download method
    
    # For other platforms or as fallback, use requests
    # Common headers that mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    
    # Add Referer for specific platforms
    if platform == 'tiktok' or 'tiktok.com' in url:
        headers['Referer'] = 'https://www.tiktok.com/'
    elif platform == 'bilibili' or 'bilibili.com' in url or 'b23.tv' in url:
        headers['Referer'] = 'https://www.bilibili.com/'
    elif platform == 'twitter' or 'twitter.com' in url or 'x.com' in url:
        headers['Referer'] = 'https://twitter.com/'
    
    try:
        # Stream the response to handle large files efficiently
        with requests.get(url, headers=headers, stream=True, timeout=30) as response:
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Save the downloaded content to the specified path
            with open(output_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
                
            return True
    except Exception as e:
        print(f"Download error: {str(e)}")
        return False

def extract_frames_from_video(video_path, output_folder, num_frames=5, try_delete_temp=False):
    """Extract frames from a video file"""
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video file")
            return False
        
        # Read frames sequentially
        frames_captured = 0
        frame_count = 0
        frames_to_skip = 0  # Will be calculated after first frame
        
        try:
            while frames_captured < num_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1
                
                # Calculate frames to skip after first frame
                if frame_count == 1:
                    # Try to get total frames, fallback to estimation
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    if total_frames <= 0:
                        # Estimate based on FPS and duration
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        if fps <= 0:
                            fps = 30  # Default assumption
                        duration = 60  # Assume 60 seconds if can't determine
                        total_frames = int(fps * duration)
                    
                    # Calculate how many frames to skip between captures
                    if total_frames > num_frames:
                        frames_to_skip = (total_frames // (num_frames + 1)) - 1
                    else:
                        frames_to_skip = 0
                    
                    # Save first frame
                    frame_path = os.path.join(output_folder, f'frame_{frames_captured+1}.jpg')
                    cv2.imwrite(frame_path, frame)
                    print(f'Saved frame {frames_captured+1} to {frame_path}')
                    frames_captured += 1
                    continue
                
                # Skip frames based on calculation
                if frames_to_skip > 0:
                    if (frame_count - 1) % (frames_to_skip + 1) != 0:
                        continue
                
                # Save frame
                frame_path = os.path.join(output_folder, f'frame_{frames_captured+1}.jpg')
                cv2.imwrite(frame_path, frame)
                print(f'Saved frame {frames_captured+1} to {frame_path}')
                frames_captured += 1
        finally:
            # Release video capture
            cap.release()
            
            # Clean up temp file if it exists
            if try_delete_temp:
                try:
                    os.remove(video_path)
                    print("Temporary file deleted")
                except Exception as e:
                    print(f"Failed to delete temporary file: {str(e)}")
        
        return frames_captured > 0
        
    except Exception as e:
        print(f"Error extracting frames: {str(e)}")
        if 'cap' in locals():
            cap.release()
        return False

def process_as_image(media_url, output_folder, platform=None):
    """Process a URL as an image and save it"""
    try:
        print("Detected image URL, downloading directly")
        # Download the image
        image_path = os.path.join(output_folder, 'frame_1.jpg')
        
        # Use our custom download function with proper headers
        if download_media(media_url, image_path, platform=platform):
            print(f'Saved image to {image_path}')
            return True
        else:
            print("Failed to download image")
            return False
    except Exception as img_err:
        print(f"Error downloading image: {str(img_err)}")
        return False