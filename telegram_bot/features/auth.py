import logging
import os
from telegram import Update
from telegram.ext import Application, BaseHandler, CallbackContext

class AuthHandler(BaseHandler):
  # TODO: test with someone else's user account
  def __init__(self):
    super().__init__(self.callback)
  
  async def callback(self, update: Update, context: CallbackContext):
    logging.info(f"Attempted unauthorized access.\nupdate = {update}\ncontext = {context}")
    
  def check_update(self, update: Update):
    allowed_user_ids = [int(id) for id in os.environ["ALLOWED_USER_IDS"].split(",")]
    return update.effective_user.id not in allowed_user_ids

def add_handlers(application: Application):
  application.add_handler(AuthHandler())
