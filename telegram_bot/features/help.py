from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from . import all_features_except_help

async def send_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  help_strings = [
    feature.help_str for feature in all_features_except_help
    if hasattr(feature, "help_str")
  ]
  help_strings.append("/help - Show manual")

  await update.message.reply_text("\n".join(help_strings))

def add_handlers(application: Application):
  application.add_handler(CommandHandler("help", send_help))
