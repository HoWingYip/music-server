import logging
import os
from enum import Enum
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler

from .utility import text_message_filter, get_playlists, get_playlist_dict, valid_playlist_name

help_str = "/rename_playlist - Rename local playlist"

RenamePlaylistConversationState = Enum("RenamePlaylistConversationState", [
  "PLAYLIST",
  "NEW_NAME",
  "CONFIRM",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True

  playlist_dict = get_playlist_dict()
  if not playlist_dict:
    await update.message.reply_text("No playlists to rename. Playlist renaming cancelled.")
    context.chat_data["in_conversation"] = False
    return ConversationHandler.END

  context.chat_data["rename_playlist"] = {"playlist_dict": playlist_dict}

  await update.message.reply_text(
    text="Which playlist do you want to rename?",
    reply_markup=InlineKeyboardMarkup([
      [InlineKeyboardButton(playlist_name, callback_data=str(i))]
      for i, playlist_name in context.chat_data["rename_playlist"]["playlist_dict"].items()
    ]),
  )

  return RenamePlaylistConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.answer()
  await update.callback_query.edit_message_reply_markup(None)

  try:
    playlist_name = context.chat_data["rename_playlist"]["playlist_dict"][update.callback_query.data]
    context.chat_data["rename_playlist"]["playlist_name"] = playlist_name
  except KeyError:
    await context.bot.send_message(
      chat_id=update.callback_query.message.chat.id,
      text="Invalid playlist. Please try another.",
    )
    return RenamePlaylistConversationState.PLAYLIST
  
  await context.bot.send_message(
    chat_id=update.callback_query.message.chat.id,
    text=f"What do you want to rename the playlist '{playlist_name}' to?",
  )
  return RenamePlaylistConversationState.NEW_NAME

async def new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not valid_playlist_name(update.message.text):
    await update.message.reply_text("Invalid playlist name. Please choose another.")
    return RenamePlaylistConversationState.NEW_NAME
  
  if update.message.text in get_playlists():
    await update.message.reply_text("Playlist already exists. Please enter another name.")
    return RenamePlaylistConversationState.NEW_NAME

  context.chat_data["rename_playlist"]["new_name"] = update.message.text

  old_name = context.chat_data["rename_playlist"]["playlist_name"]
  await update.message.reply_text(
    f"The playlist '{old_name}' will be renamed to '{update.message.text}'.\n"
    "To confirm, send /confirm. To cancel, send /cancel."
  )

  return RenamePlaylistConversationState.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["in_conversation"] = False

  try:
    playlists_path = Path("music/playlists").resolve()
    os.rename(
      playlists_path / context.chat_data["rename_playlist"]["playlist_name"],
      playlists_path / context.chat_data["rename_playlist"]["new_name"],
    )
    await update.message.reply_text("Playlist successfully renamed.")
  except Exception as ex:
    logging.error(f"Error occurred while renaming playlist: {ex}")
    await update.message.reply_text("An error occurred.")

  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Playlist renaming cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("rename_playlist", start)],
    states={
      RenamePlaylistConversationState.PLAYLIST: [CallbackQueryHandler(callback=playlist)],
      RenamePlaylistConversationState.NEW_NAME: [
        MessageHandler(filters=text_message_filter, callback=new_name),
      ],
      RenamePlaylistConversationState.CONFIRM: [CommandHandler("confirm", confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))
