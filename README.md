# spotDL (dksheets fork)

Fork of [spotDL](https://github.com/spotDL/spotify-downloader) with optimizations for Spotify's February 2026 API changes, smarter sync that avoids rate limiting, and a one-liner macOS installer.

## What's different in this fork

- **Smart sync** — reuses cached song metadata from previous runs. Only new playlist additions hit the Spotify API.
- **Batch API fallback** — tries batch endpoints first, falls back to individual calls when Spotify blocks them (common with dev mode apps).
- **Rate limit friendly** — removes unnecessary API calls for non-essential metadata (genres, disc_count, publisher). A typical sync of a 300-song playlist with 5 new songs makes ~3 API calls instead of 400+.
- **February 2026 API fixes** — handles missing `genres`, `popularity`, `publisher`, and `label` fields that Spotify removed from responses.
- **None-safe metadata embedding** — won't crash when optional fields are missing from playlist-sourced songs.

## Quick install (macOS)

```bash
curl -sSL https://raw.githubusercontent.com/dksheets/spotify-downloader/master/scripts/install-mac.sh | bash
```

The installer handles Homebrew, Python, ffmpeg, pipx, and walks you through Spotify API credential setup.

## Spotify API setup

You need your own Spotify API credentials. The shared defaults are heavily rate-limited.

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click **Create App**
4. Fill in:
   - App name: anything (e.g. `spotdl`)
   - App description: anything
   - Redirect URI: `http://127.0.0.1:9900/`
   - Check **Web API**
5. Click **Save**, then **Settings** to find your Client ID and Client Secret

Add them to `~/.spotdl/config.json`:

```json
{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
}
```

Or generate a full config with `spotdl --generate-config` and edit the file.

## Usage

### Download a song or playlist

To get a Spotify link: open Spotify, right-click any song, album, or playlist > **Share** > **Copy Link**.

```bash
spotdl "https://open.spotify.com/track/..."
spotdl "https://open.spotify.com/playlist/..."
```

### Sync a playlist (recommended for ongoing use)

First run — creates a sync file:

```bash
spotdl sync "https://open.spotify.com/playlist/YOUR_PLAYLIST_ID" \
    --save-file ~/spotdl-playlists/myplaylist.spotdl \
    --output "~/Music/spotdl/{artists} - {title}.{output-ext}"
```

Subsequent runs — pass the sync file directly (this uses the smart diff):

```bash
spotdl sync ~/spotdl-playlists/myplaylist.spotdl \
    --output "~/Music/spotdl/{artists} - {title}.{output-ext}"
```

**Important:** Always pass the `.spotdl` file on subsequent syncs, not the playlist URL. Passing the URL re-fetches everything and burns through your API quota.

### YouTube Premium quality

By default, downloads are 128kbps. With a YouTube Premium account, you get 256kbps. To enable:

1. Export cookies from youtube.com using a browser extension like [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Set the cookie path in `~/.spotdl/config.json`:

```json
{
    "cookie_file": "/path/to/cookies.txt"
}
```

Cookies expire roughly every 30 days — re-export when download quality drops.

## Config tips

Config lives at `~/.spotdl/config.json`. Key settings:

```json
{
    "save_file": null,
    "scan_for_songs": false,
    "fetch_albums": false,
    "use_cache_file": true,
    "overwrite": "skip"
}
```

| Setting | Recommendation | Why |
|---------|---------------|-----|
| `save_file` | `null` | Prevents download commands from silently overwriting your sync file. Let your script manage it explicitly. |
| `scan_for_songs` | `false` | Scans every file on disk against Spotify on each run. Massive API waste. |
| `fetch_albums` | `false` | Fetches full album for every song. Triggers extra API calls. |
| `use_cache_file` | `true` | Caches Spotify API responses to disk so repeated runs don't re-fetch. |
| `overwrite` | `"skip"` | Skips songs that already exist on disk. |

## Setting up a sync script

Example shell script for automated syncing (e.g. via Raycast, cron, etc.):

```bash
#!/bin/bash
PLAYLIST="https://open.spotify.com/playlist/YOUR_PLAYLIST_ID"
SAVE_FILE="/path/to/myplaylist.spotdl"
OUTPUT_DIR="/path/to/music"

# First run creates the sync file; subsequent runs use the smart diff
if [ -f "$SAVE_FILE" ]; then
    spotdl sync "$SAVE_FILE" \
        --output "$OUTPUT_DIR/{artists} - {title}.{output-ext}"
else
    spotdl sync "$PLAYLIST" \
        --save-file "$SAVE_FILE" \
        --output "$OUTPUT_DIR/{artists} - {title}.{output-ext}"
fi
```

## Troubleshooting

### `403 Forbidden` on batch track endpoints

Spotify's February 2026 API changes restrict batch endpoints (`/v1/tracks/?ids=...`) for dev mode apps. This fork automatically falls back to individual calls with a 0.5s delay between requests to avoid triggering rate limits.

### `SpotifyOauthError: invalid_client`

Your cached OAuth token was created with different credentials. Clear it:

```bash
rm -f ~/.spotdl/.spotipy
```

Then re-run — it'll open your browser to re-authenticate.

### `ValueError: Sync file is not a valid sync file`

Your `.spotdl` file got overwritten with a plain song list (usually by a `spotdl download` command while `save_file` was set in your config). Fix by ensuring `save_file` is `null` in your config. To recover the sync file:

```python
import json
with open("myplaylist.spotdl") as f:
    data = json.load(f)
# If it's a plain list, convert to sync format
if isinstance(data, list):
    sync = {"type": "sync", "query": ["YOUR_PLAYLIST_URL"], "songs": data}
    with open("myplaylist.spotdl", "w") as f:
        json.dump(sync, f, indent=4)
```

### `MetadataError: Failed to embed metadata`

Usually caused by None fields in song metadata when downloading from playlist data without full API enrichment. This fork handles None fields gracefully. If you see this on an older install, reinstall from this fork.

### Rate limited (`429` or `403` with retry timer)

- Don't retry while limited — each attempt can reset the 24-hour window
- Check remaining time: the error message includes `Retry will occur after: N s`
- On subsequent syncs, the smart diff ensures only new songs hit the API

## Uninstall

```bash
pipx uninstall spotdl
```

## License

This project is licensed under the [MIT](/LICENSE) License. Based on [spotDL](https://github.com/spotDL/spotify-downloader) by the spotDL contributors.
