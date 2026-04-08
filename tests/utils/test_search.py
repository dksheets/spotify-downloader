from unittest.mock import MagicMock, patch

import pytest

from spotdl.types.saved import SavedError
from spotdl.types.song import Song
from spotdl.utils.search import (
    get_search_results,
    get_simple_songs,
    parse_query,
    reinit_songs,
)

SONG = ["https://open.spotify.com/track/2Ikdgh3J5vCRmnCL3Xcrtv"]
PLAYLIST = ["https://open.spotify.com/playlist/78Lg6HmUqlTnmipvNxc536"]
ALBUM = ["https://open.spotify.com/album/4MQnUDGXmHOvnsWCpzeqWT"]
YT = [
    "https://www.youtube.com/watch?v=BZKwsPIhVO8|https://open.spotify.com/track/4B2kkxg3wKSTZw5JPaUtzQ"
]
ARTIST = ["https://open.spotify.com/artist/1FPC2zwfMHhrP3frOfaai6"]
ALBUM_SEARCH = ["album: yeezus"]

QUERY = SONG + PLAYLIST + ALBUM + YT + ARTIST

SAVED = ["saved"]


@pytest.mark.vcr()
def test_parse_song():
    songs = parse_query(SONG)

    song = songs[0]
    assert len(songs) == 1
    assert song.download_url == None


@pytest.mark.vcr()
def test_parse_album():
    songs = parse_query(ALBUM)

    assert len(songs) > 1
    assert songs[0].url == "https://open.spotify.com/track/2Ikdgh3J5vCRmnCL3Xcrtv"


@pytest.mark.vcr()
def test_parse_yt_link():
    songs = parse_query(YT)

    assert len(songs) == 1
    assert songs[0].url == "https://open.spotify.com/track/4B2kkxg3wKSTZw5JPaUtzQ"
    assert songs[0].download_url == "https://www.youtube.com/watch?v=BZKwsPIhVO8"


@pytest.mark.vcr()
def test_parse_artist():
    songs = parse_query(ARTIST)

    assert len(songs) > 1


@pytest.mark.vcr()
def test_parse_album_search():
    songs = parse_query(ALBUM_SEARCH)

    assert len(songs) > 0


@pytest.mark.vcr()
def test_parse_saved():
    with pytest.raises(SavedError):
        parse_query(SAVED)


def test_parse_query():
    songs = parse_query(QUERY)

    assert len(songs) > 1


@pytest.mark.vcr()
def test_get_search_results():
    results = get_search_results("test")
    assert len(results) > 1


def test_create_empty_song():
    song = Song.from_missing_data(name="test")
    assert song.name == "test"
    assert song.url == None
    assert song.download_url == None
    assert song.duration == None
    assert song.artists == None


@patch("spotdl.utils.search.Song")
def test_reinit_songs_batch(mock_song_cls):
    """
    Test that reinit_songs uses batch fetching for songs with URLs.
    """
    song1 = Song.from_missing_data(
        name=None,
        url="https://open.spotify.com/track/abc123",
        song_id="abc123",
    )
    song2 = Song.from_missing_data(
        name=None,
        url="https://open.spotify.com/track/def456",
        song_id="def456",
    )

    fetched_song1 = Song.from_missing_data(
        name="Song 1",
        artist="Artist 1",
        artists=["Artist 1"],
        url="https://open.spotify.com/track/abc123",
        song_id="abc123",
        genres=["pop"],
        disc_count=1,
        album_id="alb1",
        album_name="Album 1",
        album_artist="Artist 1",
        disc_number=1,
        duration=180,
        year=2024,
        date="2024-01-01",
        track_number=1,
        tracks_count=10,
        isrc="US1234",
        explicit=False,
        publisher="Label",
        cover_url="https://example.com/img.jpg",
        copyright_text="(c) 2024",
    )
    fetched_song2 = Song.from_missing_data(
        name="Song 2",
        artist="Artist 2",
        artists=["Artist 2"],
        url="https://open.spotify.com/track/def456",
        song_id="def456",
        genres=["rock"],
        disc_count=1,
        album_id="alb2",
        album_name="Album 2",
        album_artist="Artist 2",
        disc_number=1,
        duration=200,
        year=2023,
        date="2023-06-15",
        track_number=2,
        tracks_count=12,
        isrc="US5678",
        explicit=True,
        publisher="Label 2",
        cover_url="https://example.com/img2.jpg",
        copyright_text="(c) 2023",
    )

    mock_song_cls.from_urls.return_value = [fetched_song1, fetched_song2]
    mock_song_cls.__dataclass_fields__ = Song.__dataclass_fields__

    results = reinit_songs([song1, song2])

    assert len(results) == 2
    mock_song_cls.from_urls.assert_called_once()


@patch("spotdl.utils.search.reinit_song")
@patch("spotdl.utils.search.Song")
def test_reinit_songs_falls_back_for_non_url_songs(mock_song_cls, mock_reinit):
    """
    Test that reinit_songs falls back to individual reinit for songs without URLs.
    """
    song = Song.from_missing_data(
        name="Some Song",
        artist="Some Artist",
    )

    fallback_result = Song.from_missing_data(
        name="Some Song",
        artist="Some Artist",
        url="https://open.spotify.com/track/found123",
        genres=["pop"],
        disc_count=1,
        album_id="alb1",
        album_name="Album",
        album_artist="Some Artist",
        disc_number=1,
        duration=180,
        year=2024,
        date="2024-01-01",
        track_number=1,
        tracks_count=10,
        isrc="US0000",
        song_id="found123",
        explicit=False,
        publisher="Label",
        cover_url="https://example.com/img.jpg",
        copyright_text="(c) 2024",
    )

    mock_reinit.return_value = fallback_result
    mock_song_cls.from_urls.return_value = []
    mock_song_cls.__dataclass_fields__ = Song.__dataclass_fields__

    results = reinit_songs([song])

    assert len(results) == 1
    mock_reinit.assert_called_once_with(song)


@pytest.mark.vcr()
def test_get_simple_songs():
    songs = get_simple_songs(QUERY)
    assert len(songs) > 1
