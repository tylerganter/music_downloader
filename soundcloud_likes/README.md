# SoundCloud Likes Fetcher

Fetch your SoundCloud liked tracks via the API and save them as JSON.

## Quick Start

```bash
# 1. Get your OAuth token (see instructions below)
# 2. Test it works
python test_likes.py --oauth-token "YOUR_TOKEN" --verify-only

# 3. Fetch your 20 most recent likes
python test_likes.py --oauth-token "YOUR_TOKEN" --output likes.json
```

## Authentication Setup

### Option 1: OAuth Token from Browser (Recommended)

This is the most reliable method for fetching your own likes.

**Steps to get your OAuth token:**

1. Open **Chrome/Firefox** and go to [soundcloud.com](https://soundcloud.com)
2. **Log in** to your SoundCloud account
3. Open **Developer Tools** (F12 or Cmd+Option+I on Mac)
4. Go to the **Network** tab
5. In the filter box, type `api-v2` or `api.soundcloud`
6. **Click on any track** or navigate around SoundCloud
7. Look for any API request (like `track_likes`, `me`, etc.)
8. Click on the request and look at the **Request Headers**
9. Find the `Authorization` header - it will look like:
   ```
   Authorization: OAuth 1-123456-987654321-AbCdEfGhIjKlMnOp
   ```
10. Copy the token part (everything after "OAuth ")

**Alternative method using Application tab:**

1. Open Developer Tools → **Application** tab (Chrome) or **Storage** tab (Firefox)
2. Expand **Cookies** → `https://soundcloud.com`
3. Look for `oauth_token` cookie
4. Copy the value

### Option 2: Extract client_id (Public Likes Only)

If you only need to fetch someone's **public** likes, you can use a client_id.

**Steps to extract client_id:**

1. Go to [soundcloud.com](https://soundcloud.com)
2. Open **Developer Tools** → **Network** tab
3. Refresh the page
4. Filter for `client_id`
5. Look for any request with `client_id=` in the URL
6. Copy the client_id value (looks like: `AbCdEfGhIjKlMnOpQrStUvWxYz123456`)

**Note:** This method cannot fetch your own private likes or access `/me` endpoints.

## Usage

### Verify Your Token Works

```bash
python test_likes.py --oauth-token "YOUR_TOKEN" --verify-only
```

Expected output:
```
Verifying OAuth token...

✓ Token is valid!

User Info:
  ID: 123456789
  Username: yourname
  Permalink: yourname
  Total Likes: 1234
  Tracks: 10
  Followers: 500
```

### Fetch Your Likes

```bash
# Fetch 20 most recent likes (default)
python test_likes.py --oauth-token "YOUR_TOKEN"

# Fetch 10 likes and save to file
python test_likes.py --oauth-token "YOUR_TOKEN" --limit 10 --output my_likes.json

# Fetch maximum (200 likes)
python test_likes.py --oauth-token "YOUR_TOKEN" --limit 200 --output likes.json
```

### Using Environment Variables

```bash
export SOUNDCLOUD_OAUTH_TOKEN="YOUR_TOKEN"
python test_likes.py --limit 20
```

### Fetch Another User's Public Likes

```bash
python test_likes.py --client-id "CLIENT_ID" --user "artistname" --limit 20
```

## Output Format

```json
{
  "fetched_at": "2026-01-22T15:30:00.000000Z",
  "count": 20,
  "limit_requested": 20,
  "has_more": true,
  "next_href": "https://api-v2.soundcloud.com/...",
  "likes": [
    {
      "urn": "soundcloud:tracks:123456789",
      "id": 123456789,
      "title": "Track Title",
      "artist": "Artist Name",
      "artist_id": 987654,
      "permalink_url": "https://soundcloud.com/artist/track",
      "duration_ms": 180000,
      "genre": "Electronic",
      "artwork_url": "https://...",
      "created_at": "2026/01/15 12:00:00 +0000",
      "liked_at": "2026/01/20 10:30:00 +0000",
      "playback_count": 10000,
      "likes_count": 500,
      "streamable": true,
      "downloadable": false
    }
  ]
}
```

## Programmatic Usage

```python
from soundcloud_likes import fetch_likes, SoundCloudLikesError

try:
    result = fetch_likes(
        oauth_token="YOUR_TOKEN",
        limit=20,
        output_file="likes.json"  # optional
    )

    for like in result["likes"]:
        print(f"{like['artist']} - {like['title']}")

except SoundCloudLikesError as e:
    print(f"Error: {e}")
```

## Troubleshooting

### "Authentication failed (401)"

- **Token expired**: OAuth tokens expire after ~6 hours. Get a fresh token from your browser.
- **Token invalid**: Make sure you copied the full token without extra spaces.

### "Access forbidden (403)"

- The user's likes are set to private
- Your token doesn't have permission for this resource

### "Rate limit exceeded (429)"

- SoundCloud limits API requests
- Wait a few minutes before trying again
- Token rate limit: 50 per 12 hours, 30 per hour per IP

### "Failed to resolve username"

- Check the username/permalink is correct
- Try using the numeric user ID instead

## Known Limitations

1. **API registration is closed**: SoundCloud is not accepting new API applications. The workaround is using OAuth tokens from browser sessions.

2. **Token expiration**: OAuth tokens expire after ~6 hours. You'll need to refresh periodically.

3. **Rate limits**: Be mindful of rate limits when making many requests.

4. **ID deprecation**: SoundCloud is deprecating numeric `id` fields by June 30, 2025. Use `urn` for long-term stability.

## Potential Issues and Mitigations

| Issue | Cause | Mitigation |
|-------|-------|------------|
| Token expires frequently | 6-hour TTL | Script to extract token from browser, or implement refresh token flow if you have full OAuth credentials |
| API changes break fetcher | Unofficial API | The v2 API is relatively stable; the module uses standard endpoints |
| Private likes inaccessible | Privacy settings | Must use OAuth token from the account owner |
| client_id stops working | SoundCloud rotation | Extract a fresh client_id from the web app |

## Files

- `fetcher.py` - Core module for fetching likes
- `test_likes.py` - CLI tool for testing and fetching
- `README.md` - This documentation

## Future Integration

This module is designed to integrate with the main `soundcloud_downloader.py`:

```python
# Future usage example
from soundcloud_likes import fetch_likes

# Fetch recent likes
likes = fetch_likes(oauth_token=token, limit=10)

# Download each liked track
for like in likes["likes"]:
    download_track(like["permalink_url"])
```
