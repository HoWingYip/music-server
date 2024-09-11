import re
from enum import Enum
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import filters, Application, BaseHandler, CallbackContext, CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from yt_dlp import YoutubeDL

from .playlists import get_playlists

AddSongsConversationState = Enum("AddSongsConversationState", [
  "URLS",
  "PLAYLIST",
  "CONFIRM",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  
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
    f"Existing playlists:\n{'\n'.join(get_playlists())}"
  )
  return AddSongsConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

  confirmation_message = \
    f"The songs at the following URLs will be added to playlist '{playlist_name}':\n" + \
    "\n".join(context.chat_data["add_songs"]["urls"]) + \
    "\n\nTo confirm, send /confirm. To cancel, send /cancel."

  await context.bot.send_message(chat_id=update.effective_chat.id, text=confirmation_message)
  return AddSongsConversationState.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # await update.message.reply_text("Song addition confirmed.")


  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Song addition cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  text_message_filter = filters.TEXT & ~filters.COMMAND

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

