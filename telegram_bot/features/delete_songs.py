from enum import Enum
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler

from .playlists import get_playlist_contents, get_playlist_dict
from .utility import text_message_filter

DeleteSongsConversationState = Enum("DeleteSongsConversationState", [
  "PLAYLIST",
  "IDS",
  "CONFIRM",
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True

  playlist_dict = get_playlist_dict()
  if not playlist_dict:
    await update.message.reply_text("No playlists to delete from. Song deletion cancelled.")
    context.chat_data["in_conversation"] = False
    return ConversationHandler.END

  context.chat_data["delete_songs"] = {"playlist_dict": playlist_dict}

  await update.message.reply_text(
    text="Which playlist do you want to delete songs from?",
    reply_markup=InlineKeyboardMarkup([
      [InlineKeyboardButton(playlist_name, callback_data=str(i))]
      for i, playlist_name in context.chat_data["delete_songs"]["playlist_dict"].items()
    ]),
  )

  return DeleteSongsConversationState.PLAYLIST

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.answer()
  await update.callback_query.edit_message_reply_markup(None)

  try:
    playlist_name = context.chat_data["delete_songs"]["playlist_dict"][update.callback_query.data]
    context.chat_data["delete_songs"]["playlist_name"] = playlist_name
  except KeyError:
    await context.bot.send_message(
      chat_id=update.callback_query.message.chat.id,
      text="Invalid playlist. Please try another.",
    )
    return DeleteSongsConversationState.PLAYLIST
  
  playlist_contents = get_playlist_contents(playlist_name, full_filename=True)
  context.chat_data["delete_songs"]["playlist_contents"] = playlist_contents
  
  await context.bot.send_message(
    chat_id=update.callback_query.message.chat.id,
    text="Enter a comma-separated list of song indices you would like to delete "
         f"from playlist '{playlist_name}'. Elements are 1-indexed.\n\n"
         "Playlist contents:\n" + "\n".join(
           f"{i+1}. {song_name}" for i, song_name in enumerate(playlist_contents)
         )
  )

  return DeleteSongsConversationState.IDS

async def ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
  try:
    indices_to_delete = sorted(
      int(idx.strip())-1 for idx in update.message.text.split(",")
    )
    context.chat_data["delete_songs"]["indices_to_delete"] = indices_to_delete
  except:
    await update.message.reply_text(
      "Invalid index list. Song indices are 1-based and should be comma-separated. Please try again."
    )
    return DeleteSongsConversationState.IDS
  
  playlist_contents = context.chat_data["delete_songs"]["playlist_contents"]
  for idx in indices_to_delete:
    if idx >= len(playlist_contents):
      await update.message.reply_text(f"Index {idx+1} out of range. Please try again.")
      return DeleteSongsConversationState.IDS
  
  await update.message.reply_text(
    "The following songs will be deleted from playlist " + \
    f"'{context.chat_data['delete_songs']['playlist_name']}':\n" + \
    "\n".join(f"{idx+1}. {playlist_contents[idx]}" for idx in indices_to_delete) + \
    "\n\nTo confirm, send /confirm. To cancel, send /cancel."
  )
  return DeleteSongsConversationState.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["in_conversation"] = False

  playlist_name = context.chat_data["delete_songs"]["playlist_name"]
  playlist_contents = context.chat_data["delete_songs"]["playlist_contents"]
  indices_to_delete = context.chat_data["delete_songs"]["indices_to_delete"]

  for song_index in indices_to_delete:
    (Path("music/playlists") / playlist_name / playlist_contents[song_index]).unlink()
  
  await update.message.reply_text(f"{len(indices_to_delete)} songs deleted.")
  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Song deletion cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("delete_songs", start)],
    states={
      DeleteSongsConversationState.PLAYLIST: [CallbackQueryHandler(callback=playlist)],
      DeleteSongsConversationState.IDS: [
        MessageHandler(filters=text_message_filter, callback=ids),
      ],
      DeleteSongsConversationState.CONFIRM: [CommandHandler("confirm", confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))
