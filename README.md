# Video Frame Extractor

A powerful tool for extracting frames from videos across multiple social media platforms. This project provides a robust solution for capturing frames from video content hosted on various platforms.

## Current Development Status

### Supported Platforms
- ✅ YouTube
- ✅ Facebook
- ✅ Instagram
- ✅ TikTok
- ✅ Twitter/X
- ✅ Bilibili
- ✅ Clapper
- ✅ Pornhub

### Features
- Automatic platform detection from URLs
- High-quality frame extraction
- Configurable number of frames to extract
- Smart frame selection algorithm
- Retry mechanism with exponential backoff
- Platform-specific optimizations
- Modular architecture for easy maintenance and extension

## Project Structure

The project has been refactored into a modular architecture:

```
weblink_input_backend/
├── frame_extractors/         # Package containing platform-specific extractors
│   ├── __init__.py           # Makes the directory a Python package
│   ├── common_utils.py       # Shared utilities across all extractors
│   ├── youtube_frame_extractor.py
│   ├── tiktok_frame_extractor.py
│   ├── bilibili_frame_extractor.py
│   ├── x_frame_extractor.py  # Twitter/X platform support
├── main.py                   # Main entry point with CLI interface
├── requirements.txt          # Project dependencies
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- `yt-dlp`: For video stream extraction across platforms
- `opencv-python`: For frame processing and extraction

## Usage

### Basic Usage
```bash
python main.py <url>
```
Provide a URL from any supported platform, and the system will automatically detect the platform and extract frames.

### Testing Mode

Test all supported platforms:
```bash
python main.py --test
```

Test a specific platform:
```bash
python main.py --test youtube
```
```bash
python main.py --test tiktok
```
```bash
python main.py --test bilibili
```
```bash
python main.py --test twitter
```

## Testing Framework

The project includes a comprehensive testing framework that allows for testing frame extraction from different platforms:

- **Platform Detection**: Automatically identifies the platform from the URL
- **Platform-Specific Tests**: Each platform has dedicated test functions
- **Test URLs**: Pre-configured test URLs for each platform
- **Test Output**: Frames are saved to platform-specific test directories
- **Frame Verification**: Automatically verifies that frames were successfully extracted

### Test Implementation

The testing framework is implemented in `main.py` with the following components:

- `test_frame_extraction()`: Main test function that can test all platforms or a specific one
- Platform-specific test functions:
  - `test_youtube_extraction()`
  - `test_tiktok_extraction()`
  - `test_bilibili_extraction()`
  - `test_twitter_extraction()`

## Technical Details

### Common Utilities

The `common_utils.py` module provides shared functionality:

- `identify_platform()`: Detects the platform from a URL
- `get_common_headers()`: Provides browser-like headers for HTTP requests
- `download_media()`: Downloads media with platform-specific optimizations
- `extract_frames_from_video()`: Extracts frames from video files
- `process_as_image()`: Handles image-only posts

### Platform-Specific Extractors

Each platform has a dedicated extractor module with specialized functions:

- **YouTube**: Handles YouTube videos with optimal quality selection
- **TikTok**: Specialized handling for TikTok's video delivery system
- **Bilibili**: Supports Bilibili's unique video format and authentication requirements
- **Twitter/X**: Handles both video and image posts from Twitter/X

## Output

Extracted frames are saved in the following directories:

- Regular usage: `output_frames/`
- Test mode: `test_frames/test_[platform]/`

Frames are saved as JPEG files named `frame_1.jpg`, `frame_2.jpg`, etc.

## Error Handling

- Retry mechanism with exponential backoff for transient errors
- Platform-specific error handling
- Fallback mechanisms when primary extraction methods fail

## Future Development

- Additional platform support
- Enhanced error reporting
- Performance optimizations
- Integration with AI analysis pipeline