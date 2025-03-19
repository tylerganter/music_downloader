#!/usr/bin/env python3
"""
SoundCloud MP3 Downloader
A script to download MP3 files from SoundCloud URLs with basic metadata (no artwork).
"""

import argparse
import os
from subprocess import Popen, STDOUT
from tqdm import tqdm
from rich import print as rprint

from music_downloader.metadata import (
    extract_soundcloud_metadata,
    update_metadata,
)


def download_soundcloud(
    url, output_dir=".", audio_format="mp3", audio_quality="320k", with_metadata=True
):
    """Download audio from SoundCloud URL and set metadata."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Downloading from: {url}")

    # Track information (only fetch if metadata is enabled)
    track_info = {}
    if with_metadata:
        track_info = extract_soundcloud_metadata(url)
        rprint(track_info)

    # Set output filename template
    filename_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    # Create a temporary file to capture the output
    temp_output_file = os.path.join(output_dir, "temp_output.txt")

    # Command construction for yt-dlp
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format",
        audio_format,
        "--audio-quality",
        audio_quality,
        "--output",
        filename_template,
        "--progress",  # Show progress
        "--print",
        "after_move:filepath",
        url,
    ]

    # Use Popen to capture the output
    with open(temp_output_file, "w") as f:
        process = Popen(cmd, stdout=f, stderr=STDOUT)
        exit_code = process.wait()

    # Read the captured output to find the output filename
    output_file = None
    if exit_code == 0:
        with open(temp_output_file, "r") as f:
            output_content = f.read()

        # Look for the filepath in the output
        for line in output_content.splitlines():
            if line.endswith(f".{audio_format}"):
                output_file = line
                break

    # Clean up temporary file
    if os.path.exists(temp_output_file):
        os.remove(temp_output_file)

    # If download was successful and we found the output file
    if exit_code == 0 and output_file and os.path.exists(output_file):
        # Update the metadata if enabled
        if with_metadata and track_info:
            print(f"Updating metadata for: {os.path.basename(output_file)}")
            update_metadata(output_file, track_info)

        return True

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Download MP3 files from SoundCloud URLs"
    )
    parser.add_argument("urls", nargs="+", help="SoundCloud URLs to download")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./out",
        help="Output directory for downloaded files",
    )
    parser.add_argument(
        "-f", "--format", default="mp3", help="Audio format (default: mp3)"
    )
    parser.add_argument(
        "-q", "--quality", default="320k", help="Audio quality (default: 320k)"
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Disable metadata extraction and tagging",
    )

    args = parser.parse_args()

    if not args.no_metadata:
        print("Metadata extraction and tagging is enabled")

    success_count = 0
    # Add tqdm progress bar for the URLs
    for url in tqdm(args.urls, desc="Downloading tracks", unit="track"):
        if download_soundcloud(
            url, args.output_dir, args.format, args.quality, not args.no_metadata
        ):
            success_count += 1
        else:
            print(f"\nFailed to download: {url}")

    print(f"\nSuccessfully downloaded {success_count} of {len(args.urls)} tracks.")


if __name__ == "__main__":
    main()
