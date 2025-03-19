#!/usr/bin/env python3
"""
SoundCloud MP3 Downloader
A script to download MP3 files from SoundCloud URLs with basic metadata (no artwork).
Supports parallel downloads using asyncio.
"""

import argparse
import asyncio
import os
import sys
from subprocess import run
from tqdm.asyncio import tqdm as async_tqdm
from rich import print as rprint

from music_downloader.metadata import (
    extract_soundcloud_metadata,
    update_metadata,
)


async def download_soundcloud(
    url, output_dir=".", audio_format="mp3", audio_quality="320k", with_metadata=True,
    semaphore=None
):
    """Download audio from SoundCloud URL and set metadata asynchronously."""
    # Use the semaphore to limit concurrent downloads if provided
    async with semaphore or asyncio.Semaphore(1):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Downloading from: {url}")

        # Track information (only fetch if metadata is enabled)
        track_info = {}
        if with_metadata:
            try:
                track_info = extract_soundcloud_metadata(url)
                rprint(track_info)
            except Exception as e:
                print(f"Error extracting metadata for {url}: {e}")

        # Set output filename template
        filename_template = os.path.join(output_dir, "%(title)s.%(ext)s")

        # Create a temporary file to capture the output
        temp_output_file = os.path.join(output_dir, f"temp_output_{hash(url)}.txt")

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

        # Run the command and capture output
        try:
            # Run the command in a separate process and wait for it to complete
            process = await asyncio.to_thread(
                run, cmd, capture_output=True, text=True, check=False
            )
            exit_code = process.returncode
            output_content = process.stdout
            
            # Write the output to a temporary file for debugging if needed
            with open(temp_output_file, "w") as f:
                f.write(output_content)
                
            # Look for the filepath in the output
            output_file = None
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
                    await asyncio.to_thread(update_metadata, output_file, track_info)
                return True, url
            
            print(f"Failed to download: {url}")
            if process.stderr:
                print(f"Error: {process.stderr}")
            return False, url
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            if os.path.exists(temp_output_file):
                os.remove(temp_output_file)
            return False, url


async def main_async():
    parser = argparse.ArgumentParser(
        description="Download MP3 files from SoundCloud URLs in parallel"
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
    parser.add_argument(
        "-p", "--parallel",
        type=int,
        default=4,
        help="Maximum number of parallel downloads (default: 4)"
    )

    args = parser.parse_args()

    if not args.no_metadata:
        print("Metadata extraction and tagging is enabled")
    
    print(f"Maximum parallel downloads: {args.parallel}")

    # Create a semaphore to limit concurrent downloads
    semaphore = asyncio.Semaphore(args.parallel)
    
    # Prepare the tasks
    tasks = [
        download_soundcloud(
            url, 
            args.output_dir, 
            args.format, 
            args.quality, 
            not args.no_metadata,
            semaphore
        )
        for url in args.urls
    ]
    
    # Use tqdm to show progress
    print(f"Starting download of {len(tasks)} tracks...")
    results = await async_tqdm.gather(*tasks, desc="Downloading tracks")
    
    # Count successes and failures
    success_count = sum(1 for success, _ in results if success)
    
    # Print a summary
    print(f"\nSuccessfully downloaded {success_count} of {len(args.urls)} tracks.")
    
    # List any failed URLs
    failed_urls = [url for success, url in results if not success]
    if failed_urls:
        print("\nFailed to download the following URLs:")
        for url in failed_urls:
            print(f" - {url}")


def main():
    """Entry point for the script."""
    if sys.platform == "win32":
        # Set the event loop policy for Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the async main function
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
