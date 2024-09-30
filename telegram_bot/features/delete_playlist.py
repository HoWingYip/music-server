from enum import Enum
from pathlib import Path
from shutil import rmtree
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from .utility import send_possibly_long_text
from .playlists import get_playlist_contents, get_playlist_dict

DeletePlaylistConversationState = Enum("DeletePlaylistConversationState", [
  "PLAYLIST",
  "CONFIRM",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True

  playlist_dict = get_playlist_dict()
  if not playlist_dict:
    await update.message.reply_text("No playlists to delete. Playlist deletion cancelled.")
    context.chat_data["in_conversation"] = False
    return ConversationHandler.END

  context.chat_data["delete_playlist"] = {"playlist_dict": playlist_dict}

  await update.message.reply_text(
    text="Which playlist do you want to delete?",
    reply_markup=InlineKeyboardMarkup([
      [InlineKeyboardButton(playlist_name, callback_data=str(i))]
      for i, playlist_name in context.chat_data["delete_playlist"]["playlist_dict"].items()
    ]),
  )

  return DeletePlaylistConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.answer()
  await update.callback_query.edit_message_reply_markup(None)

  try:
    playlist_name = context.chat_data["delete_playlist"]["playlist_dict"][update.callback_query.data]
    context.chat_data["delete_playlist"]["playlist_name"] = playlist_name
  except KeyError:
    await context.bot.send_message(
      chat_id=update.callback_query.message.chat.id,
      text="Invalid playlist. Please try another.",
    )
    return DeletePlaylistConversationState.PLAYLIST
  
  playlist_contents = get_playlist_contents(playlist_name, full_filename=False)
  await send_possibly_long_text(
    text=f"The playlist '{playlist_name}' will be deleted. Its contents are:\n" + \
         "\n".join(f"{i+1}. {song_name}" for i, song_name in enumerate(playlist_contents)) + \
         "\n\nTo confirm, send /confirm. To cancel, send /cancel.",
    chat_id=update.callback_query.message.chat.id,
    context=context,
  )

  return DeletePlaylistConversationState.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["in_conversation"] = False

  playlist_name = context.chat_data["delete_playlist"]["playlist_name"]
  rmtree(Path("music/playlists") / playlist_name)
  
  await update.message.reply_text(f"Playlist '{playlist_name}' deleted.")
  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Playlist deletion cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("delete_playlist", start)],
    states={
      DeletePlaylistConversationState.PLAYLIST: [CallbackQueryHandler(callback=playlist)],
      DeletePlaylistConversationState.CONFIRM: [CommandHandler("confirm", confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))
