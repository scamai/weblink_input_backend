# Video Frame Extractor

A powerful tool for extracting frames from videos across multiple social media platforms. This project provides a robust solution for capturing frames from video content hosted on various platforms.

## Current Development Status

### Supported Platforms
- ✅ YouTube
- ✅ Facebook
- ✅ Instagram
- ✅ Pornhub
- 🚧 TikTok (In Progress)
- 🚧 X/Twitter (In Progress)

### Features
- Automatic platform detection from URLs
- High-quality frame extraction
- Configurable number of frames to extract
- Smart frame selection algorithm
- Retry mechanism with exponential backoff
- Platform-specific optimizations

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python youtube_frame_extractor.py
```
Follow the prompts to enter a video URL.

### Testing Mode
```bash
python youtube_frame_extractor.py --test
```
Test specific platform:
```bash
python youtube_frame_extractor.py --test youtube
```

## Project Roadmap

### Current Focus
- Completing TikTok platform support
- Backend integration preparation

### Upcoming Features
- Integration with main backend system
- Enhanced error handling
- Performance optimizations

## Technical Details

- Uses `yt-dlp` for video stream extraction
- OpenCV for frame processing
- Platform-specific handling for optimal video quality
- Modular design for easy platform additions

## Output

Extracted frames are saved in the `saved_frames` directory:
- Regular usage: `saved_frames/output/`
- Test mode: `saved_frames/test_[platform]/`

Frames are saved as JPEG files named `frame_1.jpg`, `frame_2.jpg`, etc.