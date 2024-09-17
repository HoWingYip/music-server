import os
from pathlib import Path
from multiprocessing import cpu_count
from telegram.ext import filters
from yt_dlp import YoutubeDL

text_message_filter = filters.TEXT & ~filters.COMMAND

def validate_playlist_name(playlist_name):
  # Prevent arbitrary directory traversal
  assert "/" not in playlist_name

  # Prevent traversal to parent dir by using ".." as playlist name
  music_root = Path("music").resolve()
  playlist_path = music_root / playlist_name
  assert playlist_path.resolve().parent == music_root

def download_audio(url, playlist_name):
  def symlink_after_download(progress_info):
    if progress_info["status"] != "finished":
      return

    os.makedirs(f"music/playlists/{playlist_name}", exist_ok=True)

    filename = os.path.basename(progress_info["info_dict"]["filename"])
    # FIXME: handle case where playlist already contains song
    # 'File exists' error is thrown when symlinking.
    os.symlink(
      src=f"../../all_songs/{filename}",
      dst=f"music/playlists/{playlist_name}/{filename}",
    )
  
  ydl_opts = {
    "format": "bestaudio",
    "concurrent_fragment_downloads": cpu_count(),
    "paths": { "home": "music/all_songs" },
    "noplaylist": True,
    "outtmpl": "%(uploader)s - %(title)s [%(id)s].%(ext)s",
    "progress_hooks": [symlink_after_download],
  }

  with YoutubeDL(ydl_opts) as ydl:
    if ydl.download(url) != 0:
      raise Exception("yt-dlp returned a non-zero exit code")
  
def get_yt_playlist_info(yt_playlist_url):
  with YoutubeDL() as ydl:
    return ydl.extract_info(yt_playlist_url, download=False)
