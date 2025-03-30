import os
import sys
import cv2
from pytube import YouTube

def get_video_stream(url, max_retries=3):
    import time
    from urllib.parse import urlparse
    import random
    import yt_dlp
    
    # Validate URL format
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            print("Invalid URL format")
            return None
    except Exception as e:
        print(f"URL validation error: {str(e)}")
        return None
    
    for attempt in range(max_retries):
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[ext=mp4]',  # Get best quality MP4
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            # Create yt-dlp object with options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("Could not extract video information")
                
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
        
        # Open the video stream
        cap = cv2.VideoCapture(video_url)
        
        # Get video properties
        # For streams, we can't get total frames, so we'll use duration and fps
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else 60)
        total_frames = fps * duration
        frame_interval = total_frames // num_frames
        frames_captured = 0
        frames_read = 0
        
        # Extract frames
        while frames_captured < num_frames:
            # Read frame
            ret, frame = cap.read()
            frames_read += 1
            
            # Check if we should capture this frame
            if frames_read % frame_interval == 0:
                if ret:
                    # Save frame
                    frame_path = os.path.join(output_folder, f'frame_{frames_captured+1}.jpg')
                    cv2.imwrite(frame_path, frame)
                    print(f'Saved frame {frames_captured+1} to {frame_path}')
                    frames_captured += 1
                else:
                    break
        
        # Release video capture
        cap.release()
        return frames_captured > 0
    except Exception as e:
        print(f"Error extracting frames: {str(e)}")
        return False

def main():
    # Get YouTube URL from user
    url = input("Enter YouTube URL: ")
    
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

def test_youtube_frame_extraction():
    import shutil
    # Test URL
    test_url = "https://www.youtube.com/watch?v=lb-B2zi9DtY"
    test_frames_folder = os.path.join(os.path.dirname(__file__), 'saved_frames', 'test')
    os.makedirs(test_frames_folder, exist_ok=True)
    
    try:
        # Test video stream retrieval
        print("Testing video stream retrieval...")
        stream_url = get_video_stream(test_url)
        if not stream_url:
            print("Failed to get video stream. Skipping frame extraction test.")
            return
        print("Video stream retrieval test passed!")
        
        # Test frame extraction
        print("Testing frame extraction...")
        success = extract_frames(stream_url, test_frames_folder, num_frames=5)
        if not success:
            print("Failed to extract frames. Test failed.")
            return
        
        # Verify frames were created
        frames = [f for f in os.listdir(test_frames_folder) if f.startswith('frame_')]
        if len(frames) != 5:
            print(f"Expected 5 frames, but got {len(frames)}. Test failed.")
            return
        print("Frame extraction test passed!")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        print("Test completed - frames preserved in test folder")


if __name__ == "__main__":
    if "--test" in sys.argv:
        import sys
        test_youtube_frame_extraction()
    else:
        main()