#!/usr/bin/env python3
"""
SoundCloud Likes Fetcher
A command-line script to query public SoundCloud profile likes.
"""

import sys
import os
import re
import json
import csv
import argparse
from urllib.parse import urljoin
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

def get_client_id():
    """
    Dynamically extract the client_id from SoundCloud's web assets.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get("https://soundcloud.com", headers=headers)
    if r.status_code != 200:
        print(f"Error: Failed to fetch SoundCloud homepage: {r.status_code}", file=sys.stderr)
        return None
    
    soup = BeautifulSoup(r.text, 'html.parser')
    scripts = [s.get('src') for s in soup.find_all('script') if s.get('src')]
    inline_scripts = [s.string for s in soup.find_all('script') if s.string]
    
    client_id_re = re.compile(r'client_id[:=]\s*["\']([a-zA-Z0-9]{32})["\']')
    
    # Try inline scripts first
    for js in inline_scripts:
        m = client_id_re.search(js)
        if m:
            return m.group(1)
            
    # Try external scripts
    for src in reversed(scripts):
        full_src = urljoin("https://soundcloud.com", src)
        if "sndcdn.com" not in full_src and "soundcloud.com" not in full_src:
            continue
        try:
            js_r = requests.get(full_src, headers=headers, timeout=5)
            if js_r.status_code == 200:
                m = client_id_re.search(js_r.text)
                if m:
                    return m.group(1)
        except Exception:
            pass
            
    return None

def resolve_profile(profile, client_id):
    """
    Resolve the SoundCloud username/profile URL to user details (including ID).
    """
    # If the profile is just a username, form the full URL
    if not profile.startswith("http"):
        profile = profile.strip("/")
        profile_url = f"https://soundcloud.com/{profile}"
    else:
        profile_url = profile

    resolve_url = f"https://api-v2.soundcloud.com/resolve?url={profile_url}&client_id={client_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(resolve_url, headers=headers)
    if r.status_code != 200:
        print(f"Error: Failed to resolve SoundCloud profile '{profile_url}': {r.status_code}", file=sys.stderr)
        return None
    return r.json()

def parse_date(date_str):
    """
    Parse ISO date string into datetime object.
    """
    if not date_str:
        return None
    # Normalize Z to +00:00
    normalized = date_str.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(normalized)
    except Exception:
        # Fallback manual parse for standard YYYY-MM-DD
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            return None

def fetch_likes(user_id, client_id, start_date=None, end_date=None):
    """
    Generator that fetches all likes for a user, handling pagination and date boundaries.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # We will use track_likes as our primary endpoint
    next_url = f"https://api-v2.soundcloud.com/users/{user_id}/track_likes?client_id={client_id}&limit=50"
    
    while next_url:
        r = requests.get(next_url, headers=headers)
        if r.status_code != 200:
            print(f"Error: Failed fetching likes page: {r.status_code}", file=sys.stderr)
            break
            
        data = r.json()
        collection = data.get('collection', [])
        if not collection:
            break
            
        for item in collection:
            like_time_str = item.get('created_at')
            like_time = parse_date(like_time_str)
            
            # Since likes are ordered descending by time (newest first):
            # 1. If we have end_date, and like is newer than end_date, we skip it.
            if end_date and like_time and like_time > end_date:
                continue
                
            # 2. If we have start_date, and like is older than start_date, we can stop entirely!
            if start_date and like_time and like_time < start_date:
                return # stop generating results
                
            yield item
            
        # Get next page URL
        next_href = data.get('next_href')
        if next_href:
            # Ensure the client_id is preserved or appended
            if "client_id=" not in next_href:
                next_url = f"{next_href}&client_id={client_id}"
            else:
                next_url = next_href
        else:
            next_url = None

def main():
    parser = argparse.ArgumentParser(description="Query public SoundCloud profile likes.")
    parser.add_argument("profile", help="SoundCloud profile URL or username (e.g. 'lets-get-toastie')")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Maximum number of likes to return (default: 10)")
    parser.add_argument("--offset", type=int, default=0, help="Number of likes to skip from the beginning (default: 0)")
    parser.add_argument("-o", "--output", help="Output file path (prints to stdout if omitted)")
    parser.add_argument("-f", "--format", choices=["json", "csv", "text"], 
                        help="Output format. If omitted, guessed from file extension (defaulting to text/json)")
    parser.add_argument("--start-date", help="Only show likes after this date (ISO format YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Only show likes before this date (ISO format YYYY-MM-DD)")
    parser.add_argument("--raw", action="store_true", help="Output raw API structure instead of cleaned format")
    parser.add_argument("--url-output", help="Optional file path to output a simple list of track URLs, one per line")
    parser.add_argument("--max-duration", type=float, help="Skip tracks longer than this duration in minutes (defaults to 10.0 if --url-output is specified)")
    
    args = parser.parse_args()
    
    max_dur = args.max_duration
    if args.url_output and max_dur is None:
        max_dur = 10.0
    
    # 1. Parse dates if provided
    start_dt = None
    if args.start_date:
        start_dt = parse_date(args.start_date)
        if not start_dt:
            print(f"Error: Invalid start-date format '{args.start_date}'. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
        # Ensure it has timezone info
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
            
    end_dt = None
    if args.end_date:
        end_dt = parse_date(args.end_date)
        if not end_dt:
            print(f"Error: Invalid end-date format '{args.end_date}'. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
        # Ensure it has timezone info
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
            
    # Determine format
    out_format = args.format
    if not out_format:
        if args.output:
            _, ext = os.path.splitext(args.output.lower())
            if ext == ".json":
                out_format = "json"
            elif ext == ".csv":
                out_format = "csv"
            else:
                out_format = "text"
        else:
            out_format = "text"
            
    # 2. Get client_id
    print("Extracting SoundCloud client ID...", file=sys.stderr)
    client_id = get_client_id()
    if not client_id:
        print("Error: Could not extract client_id", file=sys.stderr)
        sys.exit(1)
        
    # 3. Resolve user profile
    print(f"Resolving profile '{args.profile}'...", file=sys.stderr)
    user_info = resolve_profile(args.profile, client_id)
    if not user_info:
        sys.exit(1)
        
    user_id = user_info.get("id")
    username = user_info.get("username")
    print(f"Successfully resolved to '{username}' (User ID: {user_id})", file=sys.stderr)
    
    # 4. Fetch likes
    print("Fetching likes...", file=sys.stderr)
    likes_generator = fetch_likes(user_id, client_id, start_dt, end_dt)
    
    results = []
    skipped = 0
    
    for item in likes_generator:
        # Handle offset skipping
        if skipped < args.offset:
            skipped += 1
            continue
            
        if len(results) >= args.limit:
            break
            
        # Check duration filter
        track = item.get('track', item)
        if max_dur is not None:
            duration_ms = track.get("duration")
            if duration_ms is not None and duration_ms > (max_dur * 60 * 1000):
                continue
                
        if args.raw:
            results.append(item)
        else:
            # Clean structure
            track = item.get('track', item)
            clean_item = {
                "like_date": item.get("created_at"),
                "track_id": track.get("id"),
                "title": track.get("title"),
                "artist": track.get("user", {}).get("username"),
                "artist_url": track.get("user", {}).get("permalink_url"),
                "track_url": track.get("permalink_url"),
                "duration_ms": track.get("duration"),
                "genre": track.get("genre"),
                "likes_count": track.get("likes_count"),
                "playback_count": track.get("playback_count"),
            }
            results.append(clean_item)
            
    print(f"Retrieved {len(results)} likes.", file=sys.stderr)
    
    # 5. Format and Output
    if out_format == "json":
        output_content = json.dumps(results, indent=2)
    elif out_format == "csv":
        import io
        f_out = io.StringIO()
        if results:
            keys = results[0].keys()
            writer = csv.DictWriter(f_out, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        output_content = f_out.getvalue()
    else: # text
        lines = []
        if not args.raw:
            lines.append(f"Likes for {username}:")
            for i, res in enumerate(results, 1):
                like_dt_str = res["like_date"]
                try:
                    dt = datetime.fromisoformat(like_dt_str.replace('Z', '+00:00'))
                    date_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    date_display = like_dt_str
                lines.append(f"{i + args.offset}. [{date_display}] {res['artist']} - {res['title']} ({res['track_url']})")
        else:
            lines.append(json.dumps(results, indent=2))
        output_content = "\n".join(lines) + "\n"
        
    # Write output
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_content)
            print(f"Results successfully written to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error: Failed writing to file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Write to stdout
        sys.stdout.write(output_content)
        
    # Write URL-only output if requested
    if args.url_output:
        try:
            url_lines = []
            for res in results:
                if args.raw:
                    track = res.get('track', res)
                    url_lines.append(track.get('permalink_url', ''))
                else:
                    url_lines.append(res.get('track_url', ''))
            url_lines = [u for u in url_lines if u]
            with open(args.url_output, "w", encoding="utf-8") as f:
                f.write("\n".join(url_lines) + "\n")
            print(f"URLs successfully written to {args.url_output}", file=sys.stderr)
        except Exception as e:
            print(f"Error: Failed writing to URL output file '{args.url_output}': {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
