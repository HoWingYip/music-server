import os
from enum import Enum
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from .playlists import get_playlist_dict

ListSongsConversationState = Enum("ListSongsConversationState", [
  "PLAYLIST",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True

  context.chat_data["list_songs"] = {"playlist_dict": get_playlist_dict()}

  await update.message.reply_text(
    text="Which playlist do you want to list the songs of? Send /cancel to cancel.",
    reply_markup=InlineKeyboardMarkup([
      [InlineKeyboardButton(playlist_name, callback_data=str(i))]
      for i, playlist_name in context.chat_data["list_songs"]["playlist_dict"].items()
    ])
  )
  return ListSongsConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["in_conversation"] = False
  
  await update.callback_query.answer()
  await update.callback_query.edit_message_reply_markup(None)

  playlist_name = context.chat_data["list_songs"]["playlist_dict"][update.callback_query.data]
  sorted_song_list = [path.stem for path in sorted(
    Path(f"music/playlists/{playlist_name}").iterdir(),
    key=os.path.getmtime,
  )]

  await context.bot.send_message(
    chat_id=update.callback_query.message.chat.id,
    text=f"Songs in playlist '{playlist_name}' (most recently added last):\n" + \
         "\n".join(f"{i+1}. {filename}" for i, filename in enumerate(sorted_song_list)),
  )

  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Song listing cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("list_songs", start)],
    states={
      ListSongsConversationState.PLAYLIST: [CallbackQueryHandler(callback=playlist)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))
