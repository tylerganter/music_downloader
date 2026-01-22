"""
SoundCloud Likes Fetcher

Fetches a user's liked tracks from SoundCloud API.
Requires either an OAuth token or client_id for authentication.
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional


class SoundCloudLikesError(Exception):
    """Custom exception for SoundCloud likes fetching errors."""
    pass


# API endpoints
API_V2_BASE = "https://api-v2.soundcloud.com"
API_V1_BASE = "https://api.soundcloud.com"


def fetch_likes(
    oauth_token: Optional[str] = None,
    client_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 20,
    output_file: Optional[str] = None,
) -> dict:
    """
    Fetch liked tracks from SoundCloud.

    Args:
        oauth_token: OAuth access token from a logged-in session.
                    Required for fetching your own likes via /me endpoint.
        client_id: Client ID (can fetch public likes only).
                  If you have oauth_token, client_id is optional.
        user_id: User ID or permalink (username) to fetch likes for.
                If not provided and oauth_token is set, fetches your likes.
        limit: Maximum number of likes to fetch (default: 20, max: 200)
        output_file: Optional path to save JSON output

    Returns:
        dict with 'likes' array and 'fetched_at' timestamp

    Raises:
        SoundCloudLikesError: If authentication fails or API returns an error
    """
    if not oauth_token and not client_id:
        raise SoundCloudLikesError(
            "Either oauth_token or client_id is required. "
            "See README.md for instructions on obtaining these."
        )

    limit = min(limit, 200)  # API max is 200

    headers = {}
    params = {
        "limit": limit,
        "linked_partitioning": 1,
    }

    # Determine which endpoint and auth method to use
    if oauth_token:
        headers["Authorization"] = f"OAuth {oauth_token}"
        if user_id:
            endpoint = f"{API_V2_BASE}/users/{user_id}/track_likes"
        else:
            # Fetch authenticated user's likes
            endpoint = f"{API_V2_BASE}/me/track_likes"
    else:
        # Client ID only - can only fetch public user likes
        if not user_id:
            raise SoundCloudLikesError(
                "user_id is required when using client_id authentication. "
                "To fetch your own likes, use oauth_token instead."
            )
        params["client_id"] = client_id
        endpoint = f"{API_V2_BASE}/users/{user_id}/track_likes"

    # If user_id looks like a username (not numeric), resolve it first
    if user_id and not user_id.isdigit():
        user_id = resolve_user_id(user_id, oauth_token=oauth_token, client_id=client_id)
        if oauth_token:
            endpoint = f"{API_V2_BASE}/users/{user_id}/track_likes"
        else:
            endpoint = f"{API_V2_BASE}/users/{user_id}/track_likes"

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise SoundCloudLikesError(
                "Authentication failed (401). Your token may be expired or invalid. "
                "Please obtain a fresh OAuth token from your browser."
            )
        elif response.status_code == 403:
            raise SoundCloudLikesError(
                "Access forbidden (403). The user's likes may be private, "
                "or your credentials don't have permission to access this resource."
            )
        elif response.status_code == 404:
            raise SoundCloudLikesError(
                f"User or resource not found (404). Check the user_id: {user_id}"
            )
        elif response.status_code == 429:
            raise SoundCloudLikesError(
                "Rate limit exceeded (429). Please wait before making more requests."
            )
        else:
            raise SoundCloudLikesError(f"API request failed: {e}")
    except requests.exceptions.RequestException as e:
        raise SoundCloudLikesError(f"Network error: {e}")

    try:
        data = response.json()
    except json.JSONDecodeError:
        raise SoundCloudLikesError("Failed to parse API response as JSON")

    # Process and format the likes
    likes = []
    collection = data.get("collection", [])

    for item in collection:
        # The API returns either track objects directly or wrapped in a 'track' key
        track = item.get("track", item)

        like_info = {
            "urn": track.get("urn"),
            "id": track.get("id"),  # Deprecated but still useful
            "title": track.get("title"),
            "artist": track.get("user", {}).get("username"),
            "artist_id": track.get("user", {}).get("id"),
            "permalink_url": track.get("permalink_url"),
            "duration_ms": track.get("duration"),
            "genre": track.get("genre"),
            "artwork_url": track.get("artwork_url"),
            "created_at": track.get("created_at"),  # When track was created
            "liked_at": item.get("created_at"),  # When you liked it (if available)
            "playback_count": track.get("playback_count"),
            "likes_count": track.get("likes_count") or track.get("favoritings_count"),
            "streamable": track.get("streamable"),
            "downloadable": track.get("downloadable"),
        }
        likes.append(like_info)

    result = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "count": len(likes),
        "limit_requested": limit,
        "has_more": data.get("next_href") is not None,
        "next_href": data.get("next_href"),
        "likes": likes,
    }

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(likes)} likes to {output_file}")

    return result


def resolve_user_id(
    username: str,
    oauth_token: Optional[str] = None,
    client_id: Optional[str] = None,
) -> str:
    """
    Resolve a username/permalink to a numeric user ID.

    Args:
        username: SoundCloud username or permalink
        oauth_token: OAuth token for authentication
        client_id: Client ID for authentication

    Returns:
        Numeric user ID as string
    """
    endpoint = f"{API_V2_BASE}/resolve"
    url_to_resolve = f"https://soundcloud.com/{username}"

    headers = {}
    params = {"url": url_to_resolve}

    if oauth_token:
        headers["Authorization"] = f"OAuth {oauth_token}"
    elif client_id:
        params["client_id"] = client_id

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return str(data.get("id"))
    except Exception as e:
        raise SoundCloudLikesError(f"Failed to resolve username '{username}': {e}")


def get_my_user_info(oauth_token: str) -> dict:
    """
    Get the authenticated user's profile information.
    Useful for verifying your token works and getting your user ID.

    Args:
        oauth_token: OAuth access token

    Returns:
        User profile dict with id, username, permalink, etc.
    """
    endpoint = f"{API_V2_BASE}/me"
    headers = {"Authorization": f"OAuth {oauth_token}"}

    try:
        response = requests.get(endpoint, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {
            "id": data.get("id"),
            "urn": data.get("urn"),
            "username": data.get("username"),
            "permalink": data.get("permalink"),
            "full_name": data.get("full_name"),
            "likes_count": data.get("likes_count"),
            "track_count": data.get("track_count"),
            "followers_count": data.get("followers_count"),
        }
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise SoundCloudLikesError("Invalid or expired OAuth token")
        raise SoundCloudLikesError(f"Failed to get user info: {e}")
    except Exception as e:
        raise SoundCloudLikesError(f"Failed to get user info: {e}")
