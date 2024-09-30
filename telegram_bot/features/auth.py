import logging
import os
from telegram import Update
from telegram.ext import Application, ApplicationHandlerStop, BaseHandler, CallbackContext

class AuthHandler(BaseHandler):
  def __init__(self):
    super().__init__(self.callback)
    self.allowed_user_ids = set(int(id) for id in os.environ["ALLOWED_USER_IDS"].split(","))
  
  async def callback(self, update: Update, context: CallbackContext):
    logging.info(f"Attempted unauthorized access. Attempt info: {update}")
    raise ApplicationHandlerStop # Stop other handlers from running
    
  def check_update(self, update: Update):
    return update.effective_user.id not in self.allowed_user_ids

def add_handlers(application: Application):
  application.add_handler(AuthHandler(), group=-1) # max priority
