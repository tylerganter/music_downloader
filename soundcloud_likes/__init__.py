"""SoundCloud Likes API module for fetching user's liked tracks."""

from .fetcher import fetch_likes, SoundCloudLikesError

__all__ = ["fetch_likes", "SoundCloudLikesError"]
