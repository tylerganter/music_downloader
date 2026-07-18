#!/bin/bash

# PROFILE=lets-get-toastie
PROFILE=lets-get-toastie
# PROFILE=some_other_user

# Output directory and timestamped filenames
OUTDIR="./out/my_likes"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
OUTFILE_JSON="$OUTDIR/likes_$TIMESTAMP.json"
OUTFILE_TRACKS="$OUTDIR/tracks_$TIMESTAMP.txt"
OUTFILE_SHORT_TRACKS_W_LEN="$OUTDIR/short_tracks_w_len_$TIMESTAMP.txt"
OUTFILE_MIXES="$OUTDIR/mixes_$TIMESTAMP.txt"

# Default date range: last week to today (up to the current second)
# We leave END_DATE commented out by default so that today's new likes are not filtered out.
START_DATE=$(date -v-30d "+%Y-%m-%d")
# END_DATE=$(date "+%Y-%m-%d")

# Maximum number of likes to fetch
LIMIT=1000

# Set RAW=true to save the raw SoundCloud API response instead of cleaned JSON
# RAW=true

# Optional duration filter in minutes (tracks longer than this are skipped)
# Note: Since the script splits tracks and mixes, you'd typically leave this commented out.
# MAX_DURATION=10.0

# Ensure output directory exists
mkdir -p "$OUTDIR"

# Build arguments dynamically
ARGS=()

if [ -n "$START_DATE" ]; then
    ARGS+=(--start-date "$START_DATE")
fi

if [ -n "$END_DATE" ]; then
    ARGS+=(--end-date "$END_DATE")
fi

if [ -n "$MAX_DURATION" ]; then
    ARGS+=(--max-duration "$MAX_DURATION")
fi

if [ "$RAW" = true ]; then
    ARGS+=(--raw)
fi

# 1. Run the python script to download the JSON output
python3 get_likes.py \
    -n $LIMIT \
    --output "$OUTFILE_JSON" \
    "${ARGS[@]}" \
    "$PROFILE"

# 2. Parse the JSON and split URLs into tracks (<=18 min), short tracks with length (<4:30), and mixes (>18 min)
python3 -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except Exception as e:
    print(f'Error reading JSON file: {e}', file=sys.stderr)
    sys.exit(1)

def format_duration(ms):
    if not ms:
        return '0:00'
    total_seconds = int(ms) // 1000
    seconds = total_seconds % 60
    total_minutes = total_seconds // 60
    minutes = total_minutes % 60
    hours = total_minutes // 60
    if hours > 0:
        return f'{hours}:{minutes:02d}:{seconds:02d}'
    else:
        return f'{minutes}:{seconds:02d}'

tracks = []
short_tracks_w_len = []
mixes = []

for item in data:
    # Support both raw and clean formats
    track = item.get('track', item)
    url = track.get('permalink_url') or item.get('track_url')
    duration = track.get('duration') or item.get('duration_ms')
    
    if not url:
        continue
        
    # 18 minutes = 18 * 60 * 1000 = 1080000 milliseconds
    if duration and duration > 1080000:
        mixes.append(url)
    else:
        tracks.append(url)
        # Under 4:30 = (4 * 60 + 30) * 1000 = 270000 milliseconds
        if duration and duration < 270000:
            duration_str = format_duration(duration)
            short_tracks_w_len.append(f'{url} - {duration_str}')

with open(sys.argv[2], 'w', encoding='utf-8') as f:
    f.write('\n'.join(tracks) + ('\n' if tracks else ''))

with open(sys.argv[3], 'w', encoding='utf-8') as f:
    f.write('\n'.join(short_tracks_w_len) + ('\n' if short_tracks_w_len else ''))

with open(sys.argv[4], 'w', encoding='utf-8') as f:
    f.write('\n'.join(mixes) + ('\n' if mixes else ''))

print(f'Split complete:')
print(f'  - {len(tracks)} tracks (<=18m) written to {sys.argv[2]}')
print(f'  - {len(short_tracks_w_len)} short tracks (<4:30) with length written to {sys.argv[3]}')
print(f'  - {len(mixes)} mixes (>18m) written to {sys.argv[4]}')
" "$OUTFILE_JSON" "$OUTFILE_TRACKS" "$OUTFILE_SHORT_TRACKS_W_LEN" "$OUTFILE_MIXES"
