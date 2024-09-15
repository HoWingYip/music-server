from telegram.ext import filters

text_message_filter = filters.TEXT & ~filters.COMMAND
