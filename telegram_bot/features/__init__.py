from . import (
  auth, add_playlist, add_songs, delete_playlist, delete_songs, list_playlists, list_songs, rename_playlist, get_server_url
)

# This list defines the order of commands in the /help message.
all_features_except_help = [
  auth, add_playlist, add_songs, delete_playlist, delete_songs, list_playlists, list_songs, rename_playlist, get_server_url
]

from . import help

__all__ = all_features_except_help + [help]
