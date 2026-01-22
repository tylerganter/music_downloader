#!/usr/bin/env python3
"""
Test script for SoundCloud Likes API.

This script helps you verify your authentication setup and fetch your likes.

Usage:
    # Test with OAuth token (recommended)
    python test_likes.py --oauth-token "YOUR_TOKEN_HERE"

    # Or set environment variable
    export SOUNDCLOUD_OAUTH_TOKEN="YOUR_TOKEN_HERE"
    python test_likes.py

    # Fetch specific user's public likes (with client_id)
    python test_likes.py --client-id "YOUR_CLIENT_ID" --user "username"

    # Save output to file
    python test_likes.py --oauth-token "TOKEN" --output likes.json --limit 20
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soundcloud_likes.fetcher import (
    fetch_likes,
    get_my_user_info,
    SoundCloudLikesError,
)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch your SoundCloud likes and save as JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch your 20 most recent likes
  python test_likes.py --oauth-token "1-123456-123456789-XXXXXXXXXXXXX"

  # Fetch 10 likes and save to file
  python test_likes.py --oauth-token "TOKEN" --limit 10 --output my_likes.json

  # Verify your token works
  python test_likes.py --oauth-token "TOKEN" --verify-only

  # Fetch another user's public likes
  python test_likes.py --client-id "CLIENT_ID" --user "artistname" --limit 10

Environment Variables:
  SOUNDCLOUD_OAUTH_TOKEN - Your OAuth token (alternative to --oauth-token)
  SOUNDCLOUD_CLIENT_ID   - Client ID (alternative to --client-id)
        """,
    )

    parser.add_argument(
        "--oauth-token",
        help="OAuth token from browser session (or set SOUNDCLOUD_OAUTH_TOKEN env var)",
    )
    parser.add_argument(
        "--client-id",
        help="SoundCloud client_id (or set SOUNDCLOUD_CLIENT_ID env var)",
    )
    parser.add_argument(
        "--user",
        help="Username or user ID to fetch likes for (required if using client-id only)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of likes to fetch (default: 20, max: 200)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path for JSON (default: print to stdout)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify authentication, don't fetch likes",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty print JSON output (default: True)",
    )

    args = parser.parse_args()

    # Get credentials from args or environment
    oauth_token = args.oauth_token or os.environ.get("SOUNDCLOUD_OAUTH_TOKEN")
    client_id = args.client_id or os.environ.get("SOUNDCLOUD_CLIENT_ID")

    if not oauth_token and not client_id:
        print("ERROR: No authentication provided.", file=sys.stderr)
        print("\nYou need to provide either:", file=sys.stderr)
        print("  --oauth-token YOUR_TOKEN", file=sys.stderr)
        print("  or", file=sys.stderr)
        print("  --client-id YOUR_CLIENT_ID --user USERNAME", file=sys.stderr)
        print("\nSee README.md for instructions on obtaining these credentials.", file=sys.stderr)
        sys.exit(1)

    # Verify-only mode
    if args.verify_only:
        if not oauth_token:
            print("ERROR: --verify-only requires --oauth-token", file=sys.stderr)
            sys.exit(1)

        print("Verifying OAuth token...")
        try:
            user_info = get_my_user_info(oauth_token)
            print("\n✓ Token is valid!")
            print(f"\nUser Info:")
            print(f"  ID: {user_info['id']}")
            print(f"  Username: {user_info['username']}")
            print(f"  Permalink: {user_info['permalink']}")
            print(f"  Total Likes: {user_info['likes_count']}")
            print(f"  Tracks: {user_info['track_count']}")
            print(f"  Followers: {user_info['followers_count']}")
            sys.exit(0)
        except SoundCloudLikesError as e:
            print(f"\n✗ Token verification failed: {e}", file=sys.stderr)
            sys.exit(1)

    # Fetch likes
    print(f"Fetching up to {args.limit} likes...", file=sys.stderr)

    try:
        result = fetch_likes(
            oauth_token=oauth_token,
            client_id=client_id,
            user_id=args.user,
            limit=args.limit,
            output_file=args.output,
        )

        # Print summary to stderr
        print(f"\n✓ Successfully fetched {result['count']} likes", file=sys.stderr)
        print(f"  Fetched at: {result['fetched_at']}", file=sys.stderr)
        if result['has_more']:
            print(f"  Note: More likes available (pagination supported)", file=sys.stderr)

        # Print JSON to stdout (unless output file was specified)
        if not args.output:
            if args.pretty:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"\n  Saved to: {args.output}", file=sys.stderr)

        # Print quick summary of likes
        if result['likes']:
            print(f"\nMost recent likes:", file=sys.stderr)
            for i, like in enumerate(result['likes'][:5], 1):
                title = like.get('title', 'Unknown')
                artist = like.get('artist', 'Unknown')
                print(f"  {i}. {artist} - {title}", file=sys.stderr)
            if len(result['likes']) > 5:
                print(f"  ... and {len(result['likes']) - 5} more", file=sys.stderr)

    except SoundCloudLikesError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
