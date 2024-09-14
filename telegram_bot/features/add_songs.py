import os
import logging
from enum import Enum
from multiprocessing import cpu_count
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from yt_dlp import YoutubeDL

from .playlists import get_playlists, get_formatted_playlist_list
from .utility import text_message_filter

AddSongsConversationState = Enum("AddSongsConversationState", [
  "URLS",
  "PLAYLIST",
  "CONFIRM",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True
  
  context.chat_data["add_songs"] = {}

  await update.message.reply_text(
    "Enter a newline-separated list of URLs to download from. "
    "Send /cancel at any time to cancel." # TODO: add cancel button to inline keyboard
  )
  return AddSongsConversationState.URLS

async def urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["add_songs"]["urls"] = update.message.text.split("\n")

  await update.message.reply_text(
    f"Enter the name of the playlist to add this song to. "
    f"Playlist names may not contain slashes or null bytes.\n\n"
    f"Existing playlists:\n{get_formatted_playlist_list()}"
  )
  return AddSongsConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # FIXME: user to specify playlist by clicking on inline keyboard button
  # Also provide a button to create a new playlist.
  # Avoids ambiguity.
  playlist_name = update.message.text

  if "/" in playlist_name or "\0" in playlist_name:
    await update.message.reply_text(
      "Invalid playlist name. Playlist names may not contain slashes or null bytes."
    )
    return AddSongsConversationState.PLAYLIST
  
  if playlist_name not in get_playlists():
    await update.message.reply_text(
      f"No existing playlist named '{playlist_name}'. Will create new playlist after confirmation."
    )
  
  context.chat_data["add_songs"]["playlist"] = playlist_name

  await update.message.reply_text(
    text=f"The songs at the following URLs will be added to playlist '{playlist_name}':\n" + \
         "\n".join(context.chat_data["add_songs"]["urls"]) + \
         "\n\nTo confirm, send /confirm. To cancel, send /cancel.",
    disable_web_page_preview=True,
  )
  return AddSongsConversationState.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # TODO: handle case where song is already present in playlist
  context.chat_data["in_conversation"] = False

  playlist_name = context.chat_data["add_songs"]["playlist"]
  song_urls = context.chat_data["add_songs"]["urls"]

  download_status_message = await update.message.reply_text("Preparing to download...")

  def symlink_after_download(progress_info):
    if progress_info["status"] != "finished":
      return

    os.makedirs(f"music/playlists/{playlist_name}", exist_ok=True)

    filename = os.path.basename(progress_info["info_dict"]["filename"])
    os.symlink(
      src=f"../../all_songs/{filename}",
      dst=f"music/playlists/{playlist_name}/{filename}",
    )

  ydl_opts = {
    "format": "bestaudio",
    "concurrent_fragment_downloads": cpu_count(),
    # "paths": { "home": f"music/{playlist_name}" },
    "paths": { "home": "music/all_songs" },
    "noplaylist": True,
    "outtmpl": "%(uploader)s - %(title)s [%(id)s].%(ext)s",
    "progress_hooks": [symlink_after_download],
  }
  with YoutubeDL(ydl_opts) as ydl:
    num_successes = num_failures = 0

    for i, song_url in enumerate(song_urls):
      await download_status_message.edit_text(
        f"Downloading {song_url} to playlist '{playlist_name}' ({i+1}/{len(song_urls)})",
        disable_web_page_preview=True,
      )

      try:
        if ydl.download(song_url) != 0:
          raise Exception("yt-dlp returned a non-zero exit code")
        num_successes += 1
      except Exception as ex:
        logging.error(f"Error while downloading URL {song_url}: {ex}")
        await update.message.reply_text(
          f"Error occurred while downloading URL {song_url}.",
          disable_web_page_preview=True,
        )
        num_failures += 1

  await download_status_message.edit_text(
    f"Song addition summary: {num_successes} added; {num_failures} failed."
  )

  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Song addition cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("add_songs", start)],
    states={
      AddSongsConversationState.URLS: [
        MessageHandler(filters=text_message_filter, callback=urls),
      ],
      AddSongsConversationState.PLAYLIST: [
        MessageHandler(filters=text_message_filter, callback=playlist),
      ],
      AddSongsConversationState.CONFIRM: [CommandHandler("confirm", confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))

