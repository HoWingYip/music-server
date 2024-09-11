import logging
import os
import requests
import asyncio
from urllib.parse import urlparse
from telegram.ext import ApplicationBuilder

import features

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO,
)

application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
for feature in features.__all__:
  feature.add_handlers(application)

async def send_start_notification():
  try:
    tunnels = requests.get("http://localhost:4040/api/tunnels").json()["tunnels"]
    tunnel_url = urlparse(tunnels[0]["public_url"]).netloc
  except Exception as ex:
    logging.error("Error retrieving SSH tunnel status")
    raise ex
  
  for user_id_str in os.environ["ALLOWED_USER_IDS"].split(","):
    await application.bot.send_message(
      chat_id=int(user_id_str),
      text=f"Bot instance started. Associated SSH server is at {tunnel_url}."
    )

asyncio.run(send_start_notification())

application.run_polling()
