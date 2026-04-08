from unittest.mock import MagicMock, patch

import pytest

from spotdl.utils.spotify import SpotifyClient, SpotifyError


def test_init(patch_dependencies):
    """
    Test SpotifyClient initialization
    """

    SpotifyClient.init(
        client_id="client_id",
        client_secret="client_secret",
        user_auth=False,
        no_cache=True,
    )

    assert SpotifyClient._instance is not None


def test_multiple_init():
    """
    Test multiple SpotifyClient initialization.
    It was initialized in the previous function so there is no need to initialize it again.
    """

    with pytest.raises(SpotifyError):
        SpotifyClient.init(
            client_id="client_id",
            client_secret="client_secret",
            user_auth=False,
            no_cache=True,
        )
        SpotifyClient.init(
            client_id="client_id",
            client_secret="client_secret",
            user_auth=False,
            no_cache=True,
        )


def test_batch_tracks_chunking():
    """
    Test that batch_tracks deduplicates and chunks IDs correctly.
    """
    client = MagicMock(spec=SpotifyClient)
    client.tracks.return_value = {
        "tracks": [
            {"id": "a", "name": "Song A"},
            {"id": "b", "name": "Song B"},
        ]
    }

    result = SpotifyClient.batch_tracks(client, ["a", "b", "a"])

    assert len(result) == 2
    assert "a" in result
    assert "b" in result
    client.tracks.assert_called_once_with(["a", "b"])


def test_batch_tracks_skips_none():
    """
    Test that batch_tracks skips None items in the response.
    """
    client = MagicMock(spec=SpotifyClient)
    client.tracks.return_value = {
        "tracks": [{"id": "a", "name": "Song A"}, None]
    }

    result = SpotifyClient.batch_tracks(client, ["a", "b"])

    assert len(result) == 1
    assert "a" in result


def test_batch_artists_chunking():
    """
    Test that batch_artists deduplicates and chunks IDs correctly.
    """
    client = MagicMock(spec=SpotifyClient)
    client.artists.return_value = {
        "artists": [
            {"id": "art1", "name": "Artist 1"},
            {"id": "art2", "name": "Artist 2"},
        ]
    }

    result = SpotifyClient.batch_artists(client, ["art1", "art2", "art1"])

    assert len(result) == 2
    client.artists.assert_called_once_with(["art1", "art2"])


def test_batch_albums_chunks_by_20():
    """
    Test that batch_albums uses chunk size of 20 (Spotify's album batch limit).
    """
    client = MagicMock(spec=SpotifyClient)

    album_ids = [f"album{i}" for i in range(25)]
    client.albums.side_effect = [
        {"albums": [{"id": f"album{i}"} for i in range(20)]},
        {"albums": [{"id": f"album{i}"} for i in range(20, 25)]},
    ]

    result = SpotifyClient.batch_albums(client, album_ids)

    assert len(result) == 25
    assert client.albums.call_count == 2
    # First call should have 20 IDs, second should have 5
    first_call_ids = client.albums.call_args_list[0][0][0]
    second_call_ids = client.albums.call_args_list[1][0][0]
    assert len(first_call_ids) == 20
    assert len(second_call_ids) == 5


def test_batch_tracks_empty_input():
    """
    Test that batch methods handle empty input gracefully.
    """
    client = MagicMock(spec=SpotifyClient)

    result = SpotifyClient.batch_tracks(client, [])

    assert result == {}
    client.tracks.assert_not_called()
