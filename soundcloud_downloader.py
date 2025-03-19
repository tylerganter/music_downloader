#!/usr/bin/env python3
"""
SoundCloud MP3 Downloader
A script to download MP3 files from SoundCloud URLs with basic metadata (no artwork).
"""

import argparse
import os
import sys
import json
import re
import requests
from subprocess import Popen, PIPE, STDOUT
from tqdm import tqdm
from bs4 import BeautifulSoup
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from rich import print as rprint


def get_track_info(url):
    """
    Scrape track information from SoundCloud URL
    Returns a dictionary with track info (just title, artist, and genre)
    """
    try:
        # Get the page content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the JSON data in the page
        scripts = soup.find_all('script')
        track_info = {}
        
        for script in scripts:
            if script.string and 'window.__sc_hydration =' in script.string:
                try:
                    # Extract the JSON data more carefully
                    data_str = script.string.split('window.__sc_hydration =')[1].split(';')[0].strip()
                    data = json.loads(data_str)
                    
                    for item in data:
                        if item.get('hydratable') == 'sound':
                            sound_data = item.get('data', {})
                            
                            # Extract only essential metadata
                            track_info = {
                                'title': sound_data.get('title', ''),
                                'artist': sound_data.get('user', {}).get('username', ''),
                                'genre': sound_data.get('genre', '')
                            }
                            break
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON data: {e}")
                    continue
        
        # If the JSON approach failed, try conventional HTML parsing
        if not track_info.get('title'):
            # Try to extract title and artist from HTML
            title_tag = soup.find('meta', property='og:title')
            if title_tag:
                title_text = title_tag.get('content', '')
                # Try to separate artist from title if in format "Artist - Title"
                if ' - ' in title_text:
                    artist, title = title_text.split(' - ', 1)
                    track_info['artist'] = artist.strip()
                    track_info['title'] = title.strip()
                else:
                    track_info['title'] = title_text
                
        return track_info
    
    except Exception as e:
        print(f"Error getting track info: {e}")
        raise
        return {}


# Artwork download functionality removed as requested


def update_metadata(file_path, track_info):
    """Update the MP3 file with basic metadata (no artwork)"""
    try:
        # Create ID3 tags if they don't exist
        try:
            audio = EasyID3(file_path)
        except:
            # If the file doesn't have an ID3 tag, add one
            audio = MP3(file_path)
            audio.add_tags()
            audio.save()
            audio = EasyID3(file_path)
        
        # Set the basic metadata
        if track_info.get('title'):
            audio['title'] = track_info['title']
        if track_info.get('artist'):
            audio['artist'] = track_info['artist']
            audio['albumartist'] = track_info['artist']
        if track_info.get('genre') and track_info['genre']:  # Check if genre is not empty
            audio['genre'] = track_info['genre']
            
        # Save the changes
        audio.save()
        return True
    except Exception as e:
        print(f"Error updating metadata: {e}")
        return False


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
        track_info = get_track_info(url)
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
