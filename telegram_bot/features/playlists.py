from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .utility import get_formatted_playlist_list

async def send_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
  return await update.message.reply_text(
    text=f"Existing playlists:\n{get_formatted_playlist_list()}",
  )

def add_handlers(application: Application):
  application.add_handler(CommandHandler("playlists", send_playlists))
