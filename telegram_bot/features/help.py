from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from . import all_features_except_help

help_strings = [
  feature.help_str for feature in all_features_except_help
  if hasattr(feature, "help_str")
]
help_strings.append("/help - Show this message")
help_message = "\n".join(help_strings)

async def send_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(help_message)

def add_handlers(application: Application):
  application.add_handler(CommandHandler("help", send_help))
