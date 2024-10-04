from io import StringIO
import time
import os
from telegram import constants
import yt_dlp
from pathlib import Path
from multiprocessing import cpu_count
from telegram.ext import ContextTypes, filters

text_message_filter = filters.TEXT & ~filters.COMMAND

def valid_playlist_name(playlist_name: str):
  # Prevent directory traversal
  return "/" not in playlist_name and playlist_name != ".."

def get_playlists():
  return [entry.name for entry in os.scandir("music/playlists") if entry.is_dir()]

def get_playlist_dict():
  return {str(i): playlist_name for i, playlist_name in enumerate(get_playlists())}

def get_playlist_contents(playlist_name: str, full_filename: bool):
  playlists_root = Path("music/playlists").resolve()
  playlist_path = playlists_root / playlist_name
  assert playlist_path.resolve().parent == playlists_root, "Invalid playlist name"

  return [
    entry.name if full_filename else " ".join(entry.stem.split(" ")[1:])
    for entry in sorted(playlist_path.iterdir(), key=os.path.getmtime)
    if entry.is_file()
  ]

def get_formatted_playlist_list():
  playlists = get_playlists()
  if playlists:
    return "\n".join(f"{i+1}. {playlist}" for i, playlist in enumerate(playlists))
  else:
    return "No playlists."

async def send_possibly_long_text(
    text: str,
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    disable_web_page_preview: bool = True,
):
  if len(text) <= constants.MessageLimit.MAX_TEXT_LENGTH:
    return await context.bot.send_message(
      chat_id=chat_id,
      text=text,
      disable_web_page_preview=disable_web_page_preview,
    )
  
  return await context.bot.send_document(
    chat_id=chat_id,
    document=StringIO(text),
    caption="The output of the operation you attempted is too long to send as raw text. "
            "It is therefore attached as a text file.\n"
            "Note that the attached file may contain instructions to run additional commands.",
  )

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
    "format": "bestaudio",
    "concurrent_fragment_downloads": cpu_count(),
    "paths": { "home": "music/all_songs" },
    "noplaylist": True,
    "outtmpl": "%(uploader)s - %(title)s [%(id)s].%(ext)s",
    "postprocessors": [{
      "add_chapters": True,
      "add_infojson": "if_exists",
      "add_metadata": True,
      "key": "FFmpegMetadata",
    }],
    "fragment_retries": 10,
    "retries": 10,
    "progress_hooks": [symlink_after_download],
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    if ydl.download(url) != 0:
      raise Exception("yt-dlp returned a non-zero exit code")
  
def get_yt_playlist_info(yt_playlist_url):
  with yt_dlp.YoutubeDL({"ignoreerrors": True}) as ydl:
    return ydl.extract_info(yt_playlist_url, download=False)
