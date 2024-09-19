import time
import os
import yt_dlp
from pathlib import Path
from multiprocessing import cpu_count
from telegram.ext import filters

text_message_filter = filters.TEXT & ~filters.COMMAND

def validate_playlist_name(playlist_name):
  # Prevent arbitrary directory traversal
  assert "/" not in playlist_name

  # Prevent traversal to parent dir by using ".." as playlist name
  music_root = Path("music").resolve()
  playlist_path = music_root / playlist_name
  assert playlist_path.resolve().parent == music_root

def download_audio(url, playlist_name):
  playlist_path = f"music/playlists/{playlist_name}"
  os.makedirs(playlist_path, exist_ok=True)

  def symlink_after_download(progress_info):
    if progress_info["status"] != "finished":
      return

    filename = os.path.basename(progress_info["info_dict"]["filename"])
    audio_path_relative_to_symlink = f"../../all_songs/{filename}"
    # Prepend Unix epoch to symlink name for playlist sorting
    # (most music players can't sort by last modification time)
    symlink_path = f"music/playlists/{playlist_name}/{int(time.time())} {filename}"

    # FIXME: handle case where playlist already contains song
    # 'File exists' error is thrown when symlinking.
    os.symlink(src=audio_path_relative_to_symlink, dst=symlink_path)

    # Set modification time so playlist is in correct order when sorted by it
    # Most music players can't sort by last modification time, but whatever
    Path(symlink_path).touch()

  ydl_opts = {
    "format": "m4a",
    "concurrent_fragment_downloads": cpu_count(),
    "paths": { "home": "music/all_songs" },
    "noplaylist": True,
    "outtmpl": "%(uploader)s - %(title)s [%(id)s].%(ext)s",
    'postprocessors': [{
      'add_chapters': True,
      'add_infojson': 'if_exists',
      'add_metadata': True,
      'key': 'FFmpegMetadata',
    }],
    "progress_hooks": [symlink_after_download],
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    if ydl.download(url) != 0:
      raise Exception("yt-dlp returned a non-zero exit code")
  
def get_yt_playlist_info(yt_playlist_url):
  with yt_dlp.YoutubeDL() as ydl:
    return ydl.extract_info(yt_playlist_url, download=False)
