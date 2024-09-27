import os
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# FIXME: these functions should go in utility.py

def get_playlists():
  return [entry.name for entry in os.scandir("music/playlists") if entry.is_dir()]

def get_playlist_dict():
  return {str(i): playlist_name for i, playlist_name in enumerate(get_playlists())}

def get_playlist_contents(playlist_name: str, full_filename):
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

async def send_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
  return await update.message.reply_text(
    text=f"Existing playlists:\n{get_formatted_playlist_list()}",
  )

def add_handlers(application: Application):
  application.add_handler(CommandHandler("playlists", send_playlists))
