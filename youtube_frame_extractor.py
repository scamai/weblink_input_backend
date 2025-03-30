import os
import sys
import cv2
from pytube import YouTube

def get_video_stream(url, max_retries=3):
    import time
    from urllib.parse import urlparse
    import random
    import yt_dlp
    
    # Validate URL format and identify platform
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            print("Invalid URL format")
            return None
            
        # Identify platform from URL
        domain = parsed.netloc.lower()
        if 'youtube.com' in domain or 'youtu.be' in domain:
            platform = 'youtube'
        elif 'facebook.com' in domain or 'fb.com' in domain:
            platform = 'facebook'
        elif 'instagram.com' in domain:
            platform = 'instagram'
        elif 'tiktok.com' in domain:
            platform = 'tiktok'
        else:
            platform = 'generic'
            
        print(f"Detected platform: {platform}")
    except Exception as e:
        print(f"URL validation error: {str(e)}")
        return None
    
    for attempt in range(max_retries):
        try:
            # Configure yt-dlp options based on platform
            ydl_opts = {
                'format': 'best[ext=mp4]',  # Get best quality MP4
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,  # Need full extraction for some platforms
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
            elif platform == 'tiktok':
                 ydl_opts.update({
                    'no_playlist': True,
                })
            
            # Create yt-dlp object with options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("Could not extract video information")
                
                if platform == 'tiktok':
                    print("tiktok special handling of url info")
                    print(info)
                    video_url = info['formats'][0]['url']
                    print('info formats')
                    print(info['formats'])
                    print('first ')
                    print(f"tiktok video url: {video_url}")
                    return video_url  

                # Get the video URL
                if 'url' in info:
                    return info['url']
                elif 'formats' in info and len(info['formats']) > 0:
                    # Get the best quality format
                    formats = [f for f in info['formats'] if f.get('ext', '') == 'mp4']
                    if formats:
                        return formats[0]['url']
                    
                raise Exception("No suitable video stream found")
                
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
            

def extract_frames(video_url, output_folder, num_frames=5):
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Configure OpenCV to use FFmpeg's demuxer
        cap = cv2.VideoCapture(video_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print("Error: Could not open video stream")
            return False
        
        # Read frames sequentially
        frames_captured = 0
        frame_count = 0
        frames_to_skip = 0  # Will be calculated after first frame
        
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
        
        # Release video capture
        cap.release()
        return frames_captured > 0
        
    except Exception as e:
        print(f"Error extracting frames: {str(e)}")
        if 'cap' in locals():
            cap.release()
        return False

def main():
    # Get video URL from user
    url = input("Enter video URL (supports YouTube, Facebook, Instagram, TikTok): ")
    
    # Create output folder for frames
    frames_folder = os.path.join(os.path.dirname(__file__), 'saved_frames', 'output')
    
    # Get video stream URL
    print("Getting video stream...")
    stream_url = get_video_stream(url)
    
    if stream_url:
        print("Got video stream successfully!")
        
        # Extract frames
        print("Extracting frames...")
        if extract_frames(stream_url, frames_folder):
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
            stream_url = get_video_stream(test_url)
            if not stream_url:
                print("Failed to get video stream. Skipping frame extraction test.")
                continue
            print("Video stream retrieval test passed!")
            print(f"Stream URL: {stream_url}")
            
            # Test frame extraction
            print("Testing frame extraction...")
            # Create platform-specific test folder
            platform_test_folder = os.path.join(base_test_folder, f'test_{platform_name}')
            os.makedirs(platform_test_folder, exist_ok=True)
            
            # Clean existing test frames
            for file in os.listdir(platform_test_folder):
                if file.startswith('frame_'):
                    os.remove(os.path.join(platform_test_folder, file))
            
            success = extract_frames(stream_url, platform_test_folder, num_frames=5)
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
        if len(sys.argv) > 2 and sys.argv[2] in ['youtube', 'facebook', 'tiktok']:
            platform = sys.argv[2]
        test_frame_extraction(platform)
    else:
        main()