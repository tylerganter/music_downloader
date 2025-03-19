# SoundCloud MP3 Downloader

A Python script that downloads MP3 files from SoundCloud URLs with basic metadata (title, artist, genre).

## Features

- Downloads high-quality MP3 files from SoundCloud
- Extracts and sets basic ID3 metadata (title, artist, genre)
- Shows download progress with tqdm progress bars
- Supports batch downloading of multiple tracks

## Requirements

- Python 3.6+
- FFmpeg (for audio conversion)
- Required Python packages (install using `pip install -r requirements.txt`):
  - yt-dlp
  - tqdm
  - requests
  - beautifulsoup4
  - mutagen

## Installation

1. Clone or download this repository
2. Install FFmpeg if you don't have it already
   - On Ubuntu/Debian: `sudo apt install ffmpeg`
   - On macOS: `brew install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
3. Install the required Python packages:
   ```
   pip install -r requirements.txt
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

### Specify Output Directory

```bash
python soundcloud_downloader.py -o ~/Music/downloads https://soundcloud.com/artist/track
```

### Change Audio Quality

```bash
python soundcloud_downloader.py -q 192k https://soundcloud.com/artist/track
```

### Disable Metadata

```bash
python soundcloud_downloader.py --no-metadata https://soundcloud.com/artist/track
```

## Available Options

- `-o, --output-dir`: Specify the output directory (default: current directory)
- `-f, --format`: Audio format (default: mp3)
- `-q, --quality`: Audio quality (default: 320k)
- `--no-metadata`: Disable metadata extraction and tagging

## How It Works

1. The script uses yt-dlp to download the audio from SoundCloud
2. It scrapes the SoundCloud page to extract basic metadata like title, artist, and genre
3. After downloading, it sets basic ID3 tags (no artwork)
4. The final file is named after the track title and includes the metadata
