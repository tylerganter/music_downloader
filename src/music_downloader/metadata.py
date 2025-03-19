"""SoundCloud metadata extractor"""

import argparse
import re

import requests
from bs4 import BeautifulSoup
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from rich import print as rprint


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

        # max one space
        title = re.sub(r' {2,}', ' ', title)

        return {"title": title, "artist": artist}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"title": "Error extracting title", "artist": "Error extracting artist"}


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
        if track_info.get("title"):
            audio["title"] = track_info["title"]
        if track_info.get("artist"):
            audio["artist"] = track_info["artist"]
            audio["albumartist"] = track_info["artist"]
        if (
            track_info.get("genre") and track_info["genre"]
        ):  # Check if genre is not empty
            audio["genre"] = track_info["genre"]

        # Save the changes
        audio.save()
        return True
    except Exception as e:
        print(f"Error updating metadata: {e}")
        return False


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
