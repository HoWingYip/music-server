import requests
import logging
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

help_str = "/server - View SSH server address and port"

async def get_server_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
  try:
    tunnels = requests.get("http://localhost:4040/api/tunnels").json()["tunnels"]
    tunnel_url = urlparse(tunnels[0]["public_url"]).netloc
  except Exception as ex:
    logging.error(f"Error retrieving SSH server address: {ex}")
    return await update.message.reply_text("Error retrieving SSH server address.")

  await update.message.reply_text(f"SSH server address: {tunnel_url}")

def add_handlers(application: Application):
  application.add_handler(CommandHandler("server", get_server_addr))
