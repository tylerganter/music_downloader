"""
SoundCloud metadata extractor

This module provides utilities for extracting metadata from SoundCloud URLs,
including title, artist, and other track information.
"""

import re
import requests
from bs4 import BeautifulSoup


def extract_soundcloud_metadata(url):
    """
    Extract title and artist information from a SoundCloud URL.
    Automatically formats the title by replacing "with" with "w/" and "feat" with "ft".
    Handles "ARTIST - TITLE" pattern in title field.

    Args:
        url (str): The SoundCloud URL to scrape.

    Returns:
        dict: {'title': title, 'artist': artist} - The extracted title and artist name.
    """
    try:
        # Send a GET request to the URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Method 1: Try to extract from meta tags (most reliable)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content")
        else:
            # Fallback to title tag
            title_tag = soup.find("title")
            if title_tag:
                # Extract title from title tag pattern: "Track Name by Artist Name | Listen online for free on SoundCloud"
                title_text = title_tag.text
                title_match = re.search(r"(.+) by (.+) \| Listen", title_text)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    title = "Title not found"
            else:
                title = "Title not found"

        # Extract artist name
        # Method 1: Try from the meta tags
        artist = None
        soundcloud_user = soup.find("meta", property="soundcloud:user")
        if soundcloud_user and soundcloud_user.get("content"):
            # Extract username from the URL
            artist_url = soundcloud_user.get("content")
            artist_match = re.search(r"soundcloud\.com/([^/]+)", artist_url)
            if artist_match:
                # Get the actual username from the page
                artist_element = soup.find("a", {"href": f"/{artist_match.group(1)}"})
                if artist_element:
                    artist = artist_element.text.strip()

        # Method 2: Try alternative extraction from schema.org markup
        if not artist:
            schema_artist = soup.find("div", {"itemprop": "byArtist"})
            if schema_artist:
                artist_meta = schema_artist.find("meta", {"itemprop": "name"})
                if artist_meta:
                    artist = artist_meta.get("content")

        # Method 3: Extract from title tag if still not found
        if not artist:
            title_tag = soup.find("title")
            if title_tag:
                title_match = re.search(r"by (.+) \| Listen", title_tag.text)
                if title_match:
                    artist = title_match.group(1).strip()
                else:
                    artist = "Artist not found"
            else:
                artist = "Artist not found"

        # Check for "ARTIST - TITLE" pattern in the title (with space-hyphen-space)
        artist_title_pattern = r"^(.*?)\s+-\s+(.+)$"
        artist_title_match = re.match(artist_title_pattern, title)
        if artist_title_match:
            extracted_artist = artist_title_match.group(1).strip()
            extracted_title = artist_title_match.group(2).strip()

            # Only use this pattern if we have both components
            if extracted_artist and extracted_title:
                # Update the title to just the title part
                title = extracted_title
                # Override the artist with the artist part from the title
                artist = extracted_artist

        # Format the title: replace "with" with "w/" and "feat" with "ft"
        title = re.sub(r"\bwith\b", "w/", title, flags=re.IGNORECASE)
        title = re.sub(r"\bfeat\.?\b", "ft", title, flags=re.IGNORECASE)
        title = re.sub(r"\bfeaturing\b", "ft", title, flags=re.IGNORECASE)

        return {"title": title, "artist": artist}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"title": "Error extracting title", "artist": "Error extracting artist"}


if __name__ == "__main__":
    import argparse
    from rich import print as rprint

    parser = argparse.ArgumentParser(
        description="Extract title and artist from a SoundCloud URL"
    )
    parser.add_argument("url", help="SoundCloud URL to extract info from")
    args = parser.parse_args()

    title_artist = extract_soundcloud_metadata(args.url)
    rprint(title_artist)
