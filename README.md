# SoundCloud MP3 Downloader

A Python script that downloads MP3 files from SoundCloud URLs with basic metadata (title, artist).

## Features

- Downloads high-quality MP3 files from SoundCloud
- Extracts and sets basic ID3 metadata (title, artist)
- Supports parallel batch downloading of multiple tracks

## Installation

1. Clone or download this repository
2. Install FFmpeg if you don't have it already
   - On Ubuntu/Debian: `sudo apt install ffmpeg`
   - On macOS: `brew install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
3. Install the required Python packages:
   ```
   pip install .
   ```

## Usage

### Basic Usage

```bash
python soundcloud_downloader.py https://soundcloud.com/artist/track
```

### Download Multiple Tracks

```bash
python soundcloud_downloader.py https://soundcloud.com/artist/track1 https://soundcloud.com/artist/track2
```

## How It Works

1. The script uses yt-dlp to download the audio from SoundCloud
2. It scrapes the SoundCloud page to extract basic metadata like title, artist, and genre
3. After downloading, it sets basic ID3 tags (no artwork)
4. The final file is named after the track title and includes the metadata
