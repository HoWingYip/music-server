# TODO: register global error handler?

import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import features

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO,
)

os.makedirs("music/all_songs", exist_ok=True)
os.makedirs("music/playlists", exist_ok=True)

application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
for feature in features.__all__:
  feature.add_handlers(application)

async def send_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("\n".join(
    feature.help_str() for feature in features
    if getattr(feature, "help_str")
  ))

application.add_handler(CommandHandler("help", send_help))

application.run_polling()
