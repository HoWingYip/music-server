# TODO: register global error handler?

import logging
import os
from telegram.ext import ApplicationBuilder

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

application.run_polling()
