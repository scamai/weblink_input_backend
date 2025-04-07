# Main entry point for the weblink input backend
# This file imports from the frame_extractors package

import os
import sys
import shutil

# Import the frame extractor modules from the package
from frame_extractors.youtube_frame_extractor import get_video_stream, extract_frames
from frame_extractors.tiktok_frame_extractor import get_tiktok_stream, extract_tiktok_frames
from frame_extractors.bilibili_frame_extractor import get_bilibili_stream, extract_bilibili_frames
from frame_extractors.x_frame_extractor import get_twitter_stream, extract_twitter_frames
from frame_extractors.common_utils import identify_platform

def process_url(url, output_folder="output_frames"):
    """Process a URL to extract frames"""
    platform = identify_platform(url)
    if not platform:
        print(f"Unsupported platform or invalid URL: {url}")
        return None
        
    print(f"Processing URL from {platform}: {url}")
    
    # Get video stream URL
    print("Getting video stream...")
    stream_info = get_video_stream(url)
    
    if stream_info:
        print("Got video stream successfully!")
        
        # Extract frames
        print("Extracting frames...")
        if extract_frames(stream_info, output_folder):
            print("Frames extracted successfully!")
            return True
    
    print("Failed to process video")
    return False

def test_frame_extraction(platform=None):
    """Test frame extraction for specific platform or all platforms"""
    # Test URLs
    test_urls = {
        'youtube': "https://www.youtube.com/watch?v=lb-B2zi9DtY",
        'tiktok': "https://www.tiktok.com/@willsmith/video/7481699258819693870",
        'facebook': "https://www.facebook.com/reel/560811526820435",
        'bilibili': "https://www.bilibili.com/video/BV1YG4y17713",
        'twitter': "https://x.com/Silomare/status/1908928500645449860"
    }
    
    # Create base test folder
    base_test_folder = os.path.join(os.path.dirname(__file__), 'test_frames')
    os.makedirs(base_test_folder, exist_ok=True)
    
    try:
        # Filter URLs based on platform parameter
        urls_to_test = {k: v for k, v in test_urls.items() if platform is None or k == platform}
        
        if not urls_to_test:
            print(f"No test URLs found for platform: {platform}")
            return
            
        for platform_name, test_url in urls_to_test.items():
            print(f"\nTesting {platform_name.capitalize()} URL: {test_url}")
            
            # Create platform-specific test folder
            platform_test_folder = os.path.join(base_test_folder, f'test_{platform_name}')
            os.makedirs(platform_test_folder, exist_ok=True)
            
            # Clean existing test frames
            for file in os.listdir(platform_test_folder):
                if file.startswith('frame_'):
                    os.remove(os.path.join(platform_test_folder, file))
            
            # Test based on platform
            if platform_name == 'youtube':
                test_youtube_extraction(test_url, platform_test_folder)
            elif platform_name == 'tiktok':
                test_tiktok_extraction(test_url, platform_test_folder)
            elif platform_name == 'bilibili':
                test_bilibili_extraction(test_url, platform_test_folder)
            elif platform_name == 'twitter':
                test_twitter_extraction(test_url, platform_test_folder)
            else:
                # Use the general process_url function for other platforms
                process_url(test_url, platform_test_folder)
            
            # Verify frames were created
            frames = [f for f in os.listdir(platform_test_folder) if f.startswith('frame_')]
            print(f"Generated {len(frames)} frames in {platform_test_folder}")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        print("Test completed - frames preserved in test folder")

def test_youtube_extraction(url, output_folder):
    """Test YouTube frame extraction"""
    print("Testing YouTube frame extraction...")
    stream_info = get_video_stream(url)
    if not stream_info:
        print("Failed to get YouTube video stream.")
        return False
    
    print(f"YouTube stream info: {stream_info}")
    return extract_frames(stream_info, output_folder, num_frames=5)

def test_tiktok_extraction(url, output_folder):
    """Test TikTok frame extraction"""
    print("Testing TikTok frame extraction...")
    stream_info = get_tiktok_stream(url)
    if not stream_info:
        print("Failed to get TikTok video stream.")
        return False
    
    print(f"TikTok stream info: {stream_info}")
    return extract_tiktok_frames(stream_info, output_folder, num_frames=5)

def test_bilibili_extraction(url, output_folder):
    """Test Bilibili frame extraction"""
    print("Testing Bilibili frame extraction...")
    stream_info = get_bilibili_stream(url)
    if not stream_info:
        print("Failed to get Bilibili video stream.")
        return False
    
    print(f"Bilibili stream info: {stream_info}")
    return extract_bilibili_frames(stream_info, output_folder, num_frames=5)

def test_twitter_extraction(url, output_folder):
    """Test Twitter/X frame extraction"""
    print("Testing Twitter/X frame extraction...")
    stream_info = get_twitter_stream(url)
    if not stream_info:
        print("Failed to get Twitter/X video stream.")
        return False
    
    print(f"Twitter/X stream info: {stream_info}")
    return extract_twitter_frames(stream_info, output_folder, num_frames=5)

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Test mode
            platform = None
            if len(sys.argv) > 2:
                platform = sys.argv[2]
            test_frame_extraction(platform)
        else:
            # Normal URL processing mode
            url = sys.argv[1]
            process_url(url)
    else:
        print("Usage:")
        print("  python main.py <url>                  # Process a single URL")
        print("  python main.py --test                 # Test all platforms")
        print("  python main.py --test <platform>      # Test specific platform (youtube, tiktok, bilibili, twitter)")