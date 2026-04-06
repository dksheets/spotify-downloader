#!/usr/bin/env bash
#
# spotDL installer for macOS
# Installs spotDL from dksheets' fork with batched API requests.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/dksheets/spotify-downloader/master/scripts/install-mac.sh | bash
#
# What this script does:
#   1. Installs Homebrew (if missing)
#   2. Installs Python 3.13 and ffmpeg via Homebrew
#   3. Installs pipx (if missing)
#   4. Installs spotDL from the fork into an isolated environment
#   5. Sets up Spotify API credentials and output directory
#   6. Verifies the installation

set -euo pipefail

REPO_URL="git+https://github.com/dksheets/spotify-downloader.git@master"
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

info()  { printf "${BOLD}==> %s${RESET}\n" "$1"; }
ok()    { printf "${GREEN}==> %s${RESET}\n" "$1"; }
warn()  { printf "${YELLOW}==> %s${RESET}\n" "$1"; }
error() { printf "${RED}==> %s${RESET}\n" "$1"; }

# --- Pre-flight checks -------------------------------------------------------

if [[ "$(uname)" != "Darwin" ]]; then
    error "This script is intended for macOS only."
    exit 1
fi

# --- Homebrew -----------------------------------------------------------------

if ! command -v brew &>/dev/null; then
    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add brew to PATH for Apple Silicon Macs
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    ok "Homebrew already installed"
fi

# --- Python & ffmpeg ----------------------------------------------------------

if ! brew list python@3.13 &>/dev/null; then
    info "Installing Python 3.13..."
    brew install python@3.13
else
    ok "Python 3.13 already installed"
fi

if ! command -v ffmpeg &>/dev/null; then
    info "Installing ffmpeg..."
    brew install ffmpeg
else
    ok "ffmpeg already installed"
fi

# --- pipx ---------------------------------------------------------------------

if ! command -v pipx &>/dev/null; then
    info "Installing pipx..."
    brew install pipx
    pipx ensurepath
else
    ok "pipx already installed"
fi

# --- spotDL -------------------------------------------------------------------

info "Installing spotDL from fork..."

# Uninstall existing spotdl if present (pipx will error on reinstall otherwise)
if pipx list 2>/dev/null | grep -q spotdl; then
    warn "Removing existing spotDL installation..."
    pipx uninstall spotdl
fi

pipx install "$REPO_URL" --python "$(brew --prefix python@3.13)/bin/python3.13"

# --- Verify -------------------------------------------------------------------

if ! command -v spotdl &>/dev/null; then
    error "Installation failed. spotdl command not found."
    echo "Try restarting your terminal, or run: pipx ensurepath"
    exit 1
fi

ok "spotDL installed successfully!"
echo ""
spotdl --version

# --- Spotify API credentials --------------------------------------------------

SPOTDL_DIR="$HOME/.spotdl"
CONFIG_FILE="$SPOTDL_DIR/config.json"

echo ""
info "Setting up Spotify API credentials"
echo ""
echo "  spotDL needs your own Spotify API credentials for reliable"
echo "  rate limits. The shared defaults are heavily throttled."
echo ""
echo "  To create your credentials:"
echo "    1. Go to https://developer.spotify.com/dashboard"
echo "    2. Log in with your Spotify account"
echo "    3. Click 'Create App'"
echo "    4. Fill in:"
echo "       - App name: anything (e.g. 'spotdl')"
echo "       - App description: anything"
echo "       - Redirect URI: http://127.0.0.1:9900/"
echo "       - Check 'Web API'"
echo "    5. Click 'Save', then 'Settings' to find your Client ID and Secret"
echo ""

read -rp "Spotify Client ID: " SPOTIFY_CLIENT_ID
read -rp "Spotify Client Secret: " SPOTIFY_CLIENT_SECRET

if [[ -z "$SPOTIFY_CLIENT_ID" || -z "$SPOTIFY_CLIENT_SECRET" ]]; then
    warn "Skipped — using shared defaults (expect rate limiting)."
    warn "You can set credentials later in $CONFIG_FILE"
else
    # Generate default config if it doesn't exist
    if [[ ! -f "$CONFIG_FILE" ]]; then
        mkdir -p "$SPOTDL_DIR"
        spotdl --generate-config 2>/dev/null || true
    fi

    if [[ -f "$CONFIG_FILE" ]]; then
        # Use python to safely update JSON (available since we just installed it)
        python3 -c "
import json, sys
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
config['client_id'] = '$SPOTIFY_CLIENT_ID'
config['client_secret'] = '$SPOTIFY_CLIENT_SECRET'
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=4)
"
        ok "Credentials saved to $CONFIG_FILE"
    else
        # Config doesn't exist and generate failed — write minimal config
        mkdir -p "$SPOTDL_DIR"
        cat > "$CONFIG_FILE" <<CONF
{
    "client_id": "$SPOTIFY_CLIENT_ID",
    "client_secret": "$SPOTIFY_CLIENT_SECRET"
}
CONF
        ok "Credentials saved to $CONFIG_FILE"
    fi
fi

# --- Output directory ---------------------------------------------------------

DEFAULT_OUTPUT="$HOME/Music/spotdl"

echo ""
read -rp "Where should downloaded music be saved? [$DEFAULT_OUTPUT]: " OUTPUT_DIR
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"

# Expand ~ if user typed it
OUTPUT_DIR="${OUTPUT_DIR/#\~/$HOME}"

mkdir -p "$OUTPUT_DIR"

if [[ -f "$CONFIG_FILE" ]]; then
    python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
config['output'] = '$OUTPUT_DIR/{artists} - {title}.{output-ext}'
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=4)
"
    ok "Music will be saved to $OUTPUT_DIR"
fi

# --- Done ---------------------------------------------------------------------

echo ""
info "Quick start:"
echo ""
echo "  To get a Spotify link: open Spotify, right-click any"
echo "  song, album, or playlist > Share > Copy Link"
echo ""
echo "  Download a song:"
echo "    spotdl \"https://open.spotify.com/track/...\""
echo ""
echo "  Download an entire playlist:"
echo "    spotdl \"https://open.spotify.com/playlist/...\""
echo ""
info "Configuration:"
echo "  Config file: $CONFIG_FILE"
echo "  Default format: mp3 @ 128k"
echo "  Default provider: youtube-music"
echo ""
echo "  To customize, run: spotdl --generate-config"
echo "  Then edit $CONFIG_FILE"
echo ""
info "To uninstall:"
echo "  pipx uninstall spotdl"
