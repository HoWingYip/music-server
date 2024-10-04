from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from .utility import send_possibly_long_text, get_playlist_contents, get_playlist_dict

help_str = "/list_songs - List songs in local playlist"

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
  sorted_song_list = get_playlist_contents(playlist_name, full_filename=False)

  await send_possibly_long_text(
    text=f"Songs in playlist '{playlist_name}' (most recently added last):\n" + \
         "\n".join(f"{i+1}. {filename}" for i, filename in enumerate(sorted_song_list)),
    chat_id=update.callback_query.message.chat.id,
    context=context,
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
