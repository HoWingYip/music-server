import logging
import subprocess
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

def get_playlists():
  return [entry.name for entry in os.scandir("music") if entry.is_dir()]

async def send_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
  return await update.message.reply_text(
    text=f"Existing playlists:\n{'\n'.join(get_playlists())}",
  )

def add_handlers(application: Application):
  application.add_handler(CommandHandler("playlists", send_playlists))
