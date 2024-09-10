import logging
import os
import subprocess
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, BaseHandler, CallbackContext, CommandHandler, ContextTypes
from yt_dlp import YoutubeDL

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO
)

# TODO: test with someone else's user account

class AuthHandler(BaseHandler):
  def __init__(self):
    super().__init__(self.callback)
  
  async def callback(self, update: Update, context: CallbackContext):
    logging.info(f"Attempted unauthorized access.\nUpdate: {update}\nContext:{context}")
    
  def check_update(self, update: Update):
    allowed_user_ids = [int(id) for id in os.environ["ALLOWED_USER_IDS"].split(",")]
    return update.effective_user.id not in allowed_user_ids

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
  audio_url = context.args[0]

  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=update,
  )

async def show_library_tree(update: Update, context: ContextTypes.DEFAULT_TYPE):
  tree_output = subprocess.run(
    "tree * -d --noreport",
    shell=True, cwd="music", capture_output=True, encoding="utf-8",
  )

  if tree_output.returncode == 0:
    return await context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=f"`{tree_output.stdout}`",
      parse_mode=ParseMode.MARKDOWN_V2,
    )

  logging.error(f"Error while displaying library tree: {tree_output.stderr}")
  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="Error occurred while displaying library tree.",
  )

if __name__ == '__main__':
  application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
  
  application.add_handler(AuthHandler())
  application.add_handler(CommandHandler("download", download_audio))
  application.add_handler(CommandHandler("tree", show_library_tree))
  
  application.run_polling()
