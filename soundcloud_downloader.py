#!/usr/bin/env python3
"""
SoundCloud MP3 Downloader
A script to download MP3 files from SoundCloud URLs.
Requirements: youtube-dl (or yt-dlp), ffmpeg, tqdm
"""

import argparse
import os
import sys
from subprocess import call, STDOUT
from tqdm import tqdm


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        # First try youtube-dl
        import youtube_dl

        downloader = "youtube-dl"
    except ImportError:
        try:
            # If youtube-dl is not available, try yt-dlp (fork with more active development)
            import yt_dlp

            downloader = "yt-dlp"
        except ImportError:
            print("Error: Neither youtube-dl nor yt-dlp is installed.")
            print("Please install one of them using pip:")
            print("pip install youtube-dl")
            print("or")
            print("pip install yt-dlp")
            return False

    # Check for ffmpeg
    try:
        devnull = open(os.devnull, "w")
        call(["ffmpeg", "-version"], stdout=devnull, stderr=STDOUT)
    except:
        print("Error: ffmpeg is not installed or not in your PATH.")
        print("Please install ffmpeg from https://ffmpeg.org/download.html")
        return False

    return downloader


def download_soundcloud(
    url,
    output_dir=".",
    audio_format="mp3",
    audio_quality="320k",
    downloader="youtube-dl",
):
    """Download audio from SoundCloud URL."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Command construction based on the downloader
    if downloader == "youtube-dl":
        cmd = [
            "youtube-dl",
            "--extract-audio",
            "--audio-format",
            audio_format,
            "--audio-quality",
            audio_quality,
            "--output",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
            "--newline",  # Important for progress tracking
            url,
        ]
    else:  # yt-dlp
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format",
            audio_format,
            "--audio-quality",
            audio_quality,
            "--output",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
            "--progress",  # Show progress in yt-dlp
            url,
        ]

    print(f"Downloading from: {url}")
    return call(cmd) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Download MP3 files from SoundCloud URLs"
    )
    parser.add_argument("urls", nargs="+", help="SoundCloud URLs to download")
    parser.add_argument(
        "-o", "--output-dir", default=".", help="Output directory for downloaded files"
    )
    parser.add_argument(
        "-f", "--format", default="mp3", help="Audio format (default: mp3)"
    )
    parser.add_argument(
        "-q", "--quality", default="320k", help="Audio quality (default: 320k)"
    )

    args = parser.parse_args()

    downloader = check_dependencies()
    if not downloader:
        sys.exit(1)

    success_count = 0
    # Add tqdm progress bar for the URLs
    for url in tqdm(args.urls, desc="Downloading tracks", unit="track"):
        if download_soundcloud(
            url, args.output_dir, args.format, args.quality, downloader
        ):
            success_count += 1
        else:
            print(f"\nFailed to download: {url}")

    print(f"\nSuccessfully downloaded {success_count} of {len(args.urls)} tracks.")


if __name__ == "__main__":
    main()
