# FIXME: added song lists may be too long to send as raw text.
# Use .utility.send_possibly_long_message instead.

import logging
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler

from .playlists import get_playlist_dict, get_playlists
from .utility import text_message_filter, download_audio, valid_playlist_name

AddSongsConversationState = Enum("AddSongsConversationState", [
  "URLS",
  "PLAYLIST",
  "NEW_PLAYLIST",
  "CONFIRM",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True
  
  context.chat_data["add_songs"] = {}

  await update.message.reply_text(
    "Enter a newline-separated list of URLs to download from. "
    "Send /cancel at any time to cancel."
  )
  return AddSongsConversationState.URLS

async def urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["add_songs"]["urls"] = update.message.text.split("\n")

  context.chat_data["add_songs"]["playlist_dict"] = get_playlist_dict()

  await update.message.reply_text(
    text="Which playlist should these songs be added to?",
    reply_markup=InlineKeyboardMarkup(
      [[InlineKeyboardButton("Create new playlist", callback_data="-1")]] + [
        [InlineKeyboardButton(playlist_name, callback_data=str(i))]
        for i, playlist_name in context.chat_data["add_songs"]["playlist_dict"].items()
      ],
    ),
  )

  return AddSongsConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.answer()
  await update.callback_query.edit_message_reply_markup(None)

  playlist_dict = context.chat_data["add_songs"]["playlist_dict"]
  if update.callback_query.data in playlist_dict:
    playlist_name = playlist_dict[update.callback_query.data]
    context.chat_data["add_songs"]["playlist"] = playlist_name
   
    await context.bot.send_message(
      chat_id=update.callback_query.message.chat.id,
      text=f"The songs at the following URLs will be added to playlist '{playlist_name}':\n" + \
          "\n".join(context.chat_data["add_songs"]["urls"]) + \
          "\n\nTo confirm, send /confirm. To cancel, send /cancel.",
      disable_web_page_preview=True,
    )
    return AddSongsConversationState.CONFIRM
  
  await context.bot.send_message(
    chat_id=update.callback_query.message.chat.id,
    text="What should your new playlist be called?",
  )
  return AddSongsConversationState.NEW_PLAYLIST

async def new_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  playlist_name = update.message.text

  if not valid_playlist_name(playlist_name):
    await update.message.reply_text("Invalid playlist name. Please choose another.")
    return AddSongsConversationState.NEW_PLAYLIST

  if playlist_name in get_playlists():
    await update.message.reply_text("Playlist already exists. Please enter another name.")
    return AddSongsConversationState.NEW_PLAYLIST
  
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

  download_status_message = await update.message.reply_text("Preparing to download...")

  playlist_name = context.chat_data["add_songs"]["playlist"]
  song_urls = context.chat_data["add_songs"]["urls"]
  
  num_successes = num_failures = 0
  for i, song_url in enumerate(song_urls):
    await download_status_message.edit_text(
      f"Downloading {song_url} to playlist '{playlist_name}' ({i+1}/{len(song_urls)})",
      disable_web_page_preview=True,
    )

    try:
      download_audio(song_url, playlist_name)
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
      AddSongsConversationState.PLAYLIST: [CallbackQueryHandler(callback=playlist)],
      AddSongsConversationState.NEW_PLAYLIST: [
        MessageHandler(filters=text_message_filter, callback=new_playlist),
      ],
      AddSongsConversationState.CONFIRM: [CommandHandler("confirm", confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))

