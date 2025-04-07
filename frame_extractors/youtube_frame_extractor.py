import os
import sys
import cv2
import yt_dlp
from frame_extractors.common_utils import download_media, extract_frames_from_video, process_as_image, identify_platform
from frame_extractors.tiktok_frame_extractor import get_tiktok_stream, extract_tiktok_frames
from frame_extractors.bilibili_frame_extractor import get_bilibili_stream, extract_bilibili_frames
from frame_extractors.x_frame_extractor import get_twitter_stream, extract_twitter_frames

def get_video_stream(url, max_retries=3):
    """Get video stream URL for various platforms"""
    import time
    from urllib.parse import urlparse
    import random
    
    # Validate URL format and identify platform
    platform = identify_platform(url)
    if not platform:
        return None
        
    print(f"Detected platform: {platform}")
    
    # Delegate to platform-specific extractors
    if platform == 'tiktok':
        return get_tiktok_stream(url, max_retries)
    elif platform == 'bilibili':
        return get_bilibili_stream(url, max_retries)
    elif platform == 'twitter':
        return get_twitter_stream(url, max_retries)
    
    # Handle YouTube and other platforms
    for attempt in range(max_retries):
        try:
            # Configure yt-dlp options based on platform
            ydl_opts = {
                'format': 'best[ext=mp4]',  # Get best quality MP4
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,  # Need full extraction for some platforms
                # Add browser headers to avoid 403 errors
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                },
            }
            
            # Add platform-specific options
            if platform == 'facebook':
                ydl_opts.update({
                    'no_playlist': True,
                })
            elif platform == 'instagram':
                ydl_opts.update({
                    'extract_flat': True,
                    'no_playlist': True,
                })
            
            print('starting yt-dlp')
            # Create yt-dlp object with options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("Could not extract video information")
                
                # Check if this is an image post rather than a video
                if 'entries' in info and info.get('_type') == 'playlist':
                    # Some platforms return playlists for posts with images
                    for entry in info['entries']:
                        if entry.get('_type') == 'image':
                            print("Detected image post")
                            if 'url' in entry:
                                return entry['url']
                            elif 'thumbnail' in entry:
                                return entry['thumbnail']
                
                # Store platform in the return value for special handling
                result = {'platform': platform}
                
                # General handling for YouTube and other platforms
                if 'url' in info:
                    result['url'] = info['url']
                    return result
                elif 'formats' in info and len(info['formats']) > 0:
                    # Get the best quality format
                    formats = [f for f in info['formats'] if f.get('ext', '') == 'mp4']
                    if formats:
                        result['url'] = formats[0]['url']
                        return result
                    # If no MP4 format, try any format
                    result['url'] = info['formats'][0]['url']
                    return result
                elif 'thumbnail' in info:  # Fallback to thumbnail if no video URL
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
                print("Max retries reached. Please check if the video URL is valid and accessible.")
                return None

def extract_frames(media_info, output_folder, num_frames=5):
    """Extract frames from videos or images"""
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Handle both string URLs and dictionary format
        if isinstance(media_info, dict):
            media_url = media_info['url']
            platform = media_info.get('platform', 'unknown')
            is_image = media_info.get('is_image', False)
            original_url = media_info.get('original_url', None)
        else:
            # For backward compatibility
            media_url = media_info
            platform = 'unknown'
            is_image = False
            original_url = None
        
        # Delegate to platform-specific extractors
        if platform == 'tiktok':
            return extract_tiktok_frames(media_info, output_folder, num_frames)
        elif platform == 'bilibili':
            return extract_bilibili_frames(media_info, output_folder, num_frames)
        elif platform == 'twitter':
            return extract_twitter_frames(media_info, output_folder, num_frames)
        
        # Handle YouTube and other platforms
        # If it's an image URL, download and save it directly
        if is_image:
            return process_as_image(media_url, output_folder, platform=platform)
        
        # For YouTube and other platforms, try direct streaming
        return extract_frames_from_video(media_url, output_folder, num_frames)
        
    except Exception as e:
        print(f"Error extracting frames: {str(e)}")
        if 'cap' in locals():
            cap.release()
        return False

def main():
    # Get video URL from user
    url = input("Enter video URL (supports YouTube, Facebook, Instagram, TikTok, Twitter/X, Bilibili): ")
    
    # Create output folder for frames
    frames_folder = os.path.join(os.path.dirname(__file__), 'saved_frames', 'output')
    
    # Get video stream URL
    print("Getting video stream...")
    stream_info = get_video_stream(url)
    
    if stream_info:
        print("Got video stream successfully!")
        
        # Extract frames
        print("Extracting frames...")
        if extract_frames(stream_info, frames_folder):
            print("Frames extracted successfully!")
    else:
        print("Failed to process video")

def test_frame_extraction(platform=None):
    import shutil
    # Test URLs
    test_urls = {
        'youtube': "https://www.youtube.com/watch?v=lb-B2zi9DtY",
        'tiktok': "https://www.tiktok.com/@willsmith/video/7481699258819693870",
        'facebook': "https://www.facebook.com/reel/560811526820435",
        'general_website': "https://www.pornhub.com/view_video.php?viewkey=670e028ceb11d",
        'clapper': "https://clapperapp.com/video/GE8opqZnYBgzYne9",
        'bilibili': "https://www.bilibili.com/video/BV1YG4y17713",
        'twitter': "https://twitter.com/elonmusk/status/1677828521746722817" # Updated to a tweet with video content
    }
    base_test_folder = os.path.join(os.path.dirname(__file__), 'saved_frames')
    os.makedirs(base_test_folder, exist_ok=True)
    
    try:
        # Filter URLs based on platform parameter
        urls_to_test = {k: v for k, v in test_urls.items() if platform is None or k == platform}
        
        if not urls_to_test:
            print(f"No test URLs found for platform: {platform}")
            return
            
        for platform_name, test_url in urls_to_test.items():
            print(f"\nTesting {platform_name.capitalize()} URL: {test_url}")
            # Test video stream retrieval
            print("Testing video stream retrieval...")
            stream_info = get_video_stream(test_url)
            if not stream_info:
                # Special handling for Twitter - it's common for tweets to not have videos
                if platform_name == 'twitter':
                    print("Note: This tweet doesn't contain extractable media. This is common for text-only tweets.")
                    print("For Twitter testing, consider using a tweet URL that contains images or videos.")
                    print("Skipping frame extraction test for this tweet.")
                else:
                    print("Failed to get video stream. Skipping frame extraction test.")
                continue
            print("Video stream retrieval test passed!")
            if isinstance(stream_info, dict):
                print(f"Stream URL: {stream_info['url']}")
            else:
                print(f"Stream URL: {stream_info}")
            
            # Test frame extraction
            print("Testing frame extraction...")
            # Create platform-specific test folder
            platform_test_folder = os.path.join(base_test_folder, f'test_{platform_name}')
            os.makedirs(platform_test_folder, exist_ok=True)
            
            # Clean existing test frames
            for file in os.listdir(platform_test_folder):
                if file.startswith('frame_'):
                    os.remove(os.path.join(platform_test_folder, file))
            
            success = extract_frames(stream_info, platform_test_folder, num_frames=5)
            if not success:
                print("Failed to extract frames. Test failed.")
                continue
            
            # Verify frames were created
            frames = [f for f in os.listdir(platform_test_folder) if f.startswith('frame_')]
            if len(frames) != 5:
                print(f"Expected 5 frames, but got {len(frames)}. Test failed.")
                continue
            print("Frame extraction test passed!")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        print("Test completed - frames preserved in test folder")


if __name__ == "__main__":
    if "--test" in sys.argv:
        import sys
        # Get platform from command line arguments
        platform = None
        if len(sys.argv) > 2:
            platform = sys.argv[2]
        test_frame_extraction(platform)
    else:
        main()