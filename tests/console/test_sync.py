import json
from unittest.mock import MagicMock, patch

from spotdl.console.sync import sync
from spotdl.types.song import Song


def _make_song(**kwargs):
    """Helper to create a Song with sensible defaults."""
    defaults = {
        "name": "Test Song",
        "artists": ["Test Artist"],
        "artist": "Test Artist",
        "genres": ["pop"],
        "disc_number": 1,
        "disc_count": 1,
        "album_name": "Test Album",
        "album_artist": "Test Artist",
        "duration": 180,
        "year": 2024,
        "date": "2024-01-01",
        "track_number": 1,
        "tracks_count": 10,
        "song_id": "abc123",
        "explicit": False,
        "publisher": "Test Label",
        "url": "https://open.spotify.com/track/abc123",
        "isrc": "USTEST0000001",
        "cover_url": "https://example.com/img.jpg",
        "copyright_text": "(c) 2024",
    }
    defaults.update(kwargs)
    return Song.from_missing_data(**defaults)


@patch("spotdl.console.sync.get_simple_songs")
@patch("spotdl.console.sync.reinit_songs")
def test_sync_reuses_cached_songs(mock_reinit, mock_get_simple, tmp_path):
    """
    Sync should reuse song metadata from the save file for songs
    already in the playlist, and only call reinit_songs for new ones.
    """
    # Existing song in save file (complete metadata)
    old_song = _make_song(
        name="Old Song",
        url="https://open.spotify.com/track/old1",
        song_id="old1",
        genres=["rock"],
        disc_count=1,
    )

    # New song (not in save file)
    new_song_partial = _make_song(
        name="New Song",
        url="https://open.spotify.com/track/new1",
        song_id="new1",
        genres=None,
        disc_count=None,
    )

    # What get_simple_songs returns (lightweight playlist fetch)
    mock_get_simple.return_value = [
        _make_song(
            name="Old Song",
            url="https://open.spotify.com/track/old1",
            song_id="old1",
            genres=None,  # Playlist API doesn't return genres
            disc_count=None,
            list_position=1,
            list_length=2,
        ),
        new_song_partial,
    ]

    # What reinit_songs returns for new songs
    new_song_complete = _make_song(
        name="New Song",
        url="https://open.spotify.com/track/new1",
        song_id="new1",
        genres=["electronic"],
        disc_count=1,
    )
    mock_reinit.return_value = [new_song_complete]

    # Write the sync file
    sync_file = tmp_path / "test.spotdl"
    sync_file.write_text(
        json.dumps(
            {
                "type": "sync",
                "query": ["https://open.spotify.com/playlist/test123"],
                "songs": [old_song.json],
            }
        )
    )

    # Mock the downloader
    downloader = MagicMock()
    downloader.settings = {
        "threads": 1,
        "ytm_data": False,
        "playlist_numbering": False,
        "album_type": None,
        "playlist_retain_track_cover": False,
        "save_file": None,
        "m3u": None,
        "output": "{artists} - {title}.{output-ext}",
        "format": "mp3",
        "restrict": None,
        "sync_without_deleting": True,
        "sync_remove_lrc": False,
        "fetch_albums": False,
    }

    sync(query=[str(sync_file)], downloader=downloader)

    # reinit_songs should only be called with the new song, not the old one
    mock_reinit.assert_called_once()
    reinit_args = mock_reinit.call_args[0][0]
    assert len(reinit_args) == 1
    assert reinit_args[0].url == "https://open.spotify.com/track/new1"


@patch("spotdl.console.sync.get_simple_songs")
@patch("spotdl.console.sync.reinit_songs")
def test_sync_no_new_songs_skips_reinit(mock_reinit, mock_get_simple, tmp_path):
    """
    When all songs are already cached, reinit_songs should not be called.
    """
    old_song = _make_song(
        url="https://open.spotify.com/track/old1",
        song_id="old1",
    )

    mock_get_simple.return_value = [
        _make_song(
            url="https://open.spotify.com/track/old1",
            song_id="old1",
            genres=None,
            disc_count=None,
        ),
    ]

    sync_file = tmp_path / "test.spotdl"
    sync_file.write_text(
        json.dumps(
            {
                "type": "sync",
                "query": ["https://open.spotify.com/playlist/test123"],
                "songs": [old_song.json],
            }
        )
    )

    downloader = MagicMock()
    downloader.settings = {
        "threads": 1,
        "ytm_data": False,
        "playlist_numbering": False,
        "album_type": None,
        "playlist_retain_track_cover": False,
        "save_file": None,
        "m3u": None,
        "output": "{artists} - {title}.{output-ext}",
        "format": "mp3",
        "restrict": None,
        "sync_without_deleting": True,
        "sync_remove_lrc": False,
        "fetch_albums": False,
    }

    sync(query=[str(sync_file)], downloader=downloader)

    # reinit_songs should NOT have been called
    mock_reinit.assert_not_called()
