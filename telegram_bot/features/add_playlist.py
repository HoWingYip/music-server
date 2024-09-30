import logging
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler

from .playlists import get_playlist_dict, get_playlists
from .utility import get_yt_playlist_info, text_message_filter, download_audio, valid_playlist_name, send_possibly_long_text

AddPlaylistConversationState = Enum("AddPlaylistConversationState", [
  "URL",
  "PLAYLIST",
  "NEW_PLAYLIST",
  "CONFIRM",
])

async def send_confirmation_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
  return await send_possibly_long_text(
    text=f"The following songs will be added to playlist " + \
         f"'{context.chat_data['add_playlist']['playlist']}':\n" + \
         context.chat_data["add_playlist"]["song_list"] + \
         "\n\nTo confirm, send /confirm. To cancel, send /cancel.",
    chat_id=chat_id,
    context=context,
  )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.chat_data.get("in_conversation"):
    return ConversationHandler.END
  context.chat_data["in_conversation"] = True
  
  context.chat_data["add_playlist"] = {}

  await update.message.reply_text(
    "Enter the URL of the playlist to download. "
    "Send /cancel at any time to cancel."
  )
  return AddPlaylistConversationState.URL

async def url(update: Update, context: ContextTypes.DEFAULT_TYPE):
  yt_playlist_url = update.message.text
  context.chat_data["add_playlist"]["playlist_url"] = yt_playlist_url

  fetching_info_message = await update.message.reply_text(
    "Fetching YouTube playlist info. This may take several minutes, "
    "or up to an hour for playlists with several hundred songs."
  )

  try:
    # TODO: run get_yt_playlist info asynchronously so user can /cancel while waiting
    # And find some way to log fetching progress (e.g. "video m of n")
    yt_playlist_info = get_yt_playlist_info(yt_playlist_url)
    context.chat_data["add_playlist"]["urls"] = [
      video["webpage_url"] if video else None
      for video in yt_playlist_info["entries"]
    ]
    context.chat_data["add_playlist"]["song_list"] = "\n".join(
      f"{i+1}. {video['title']}\nURL: {video['webpage_url']}"
      if video else f"{i+1}. [Not available.]"
      for i, video in enumerate(yt_playlist_info["entries"])
    )
    await fetching_info_message.edit_text("Successfully fetched YouTube playlist info.")
  except Exception as ex:
    logging.error(f"Error while fetching info for YouTube playlist {yt_playlist_url}: {ex}")
    await context.bot.send_message(
      chat_id=update.message.chat_id,
      text="Error occurred while fetching YouTube playlist info. Send another playlist URL to try again.",
    )
    return AddPlaylistConversationState.URL

  context.chat_data["add_playlist"]["playlist_dict"] = get_playlist_dict()

  await update.message.reply_text(
    text="Which playlist should these songs be added to?",
    reply_markup=InlineKeyboardMarkup(
      [[InlineKeyboardButton("Create new playlist", callback_data="-1")]] + [
        [InlineKeyboardButton(playlist_name, callback_data=str(i))]
        for i, playlist_name in context.chat_data["add_playlist"]["playlist_dict"].items()
      ],
    ),
  )

  return AddPlaylistConversationState.PLAYLIST  

async def playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.answer()
  await update.callback_query.edit_message_reply_markup(None)

  playlist_dict = context.chat_data["add_playlist"]["playlist_dict"]
  if update.callback_query.data in playlist_dict:
    playlist_name = playlist_dict[update.callback_query.data]
    context.chat_data["add_playlist"]["playlist"] = playlist_name

    await send_confirmation_message(update.callback_query.message.chat.id, context)
    return AddPlaylistConversationState.CONFIRM
  
  await context.bot.send_message(
    chat_id=update.callback_query.message.chat.id,
    text="What should your new playlist be called?",
  )
  return AddPlaylistConversationState.NEW_PLAYLIST

async def new_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
  playlist_name = update.message.text

  if not valid_playlist_name(playlist_name):
    await update.message.reply_text("Invalid playlist name. Please choose another.")
    return AddPlaylistConversationState.NEW_PLAYLIST

  if playlist_name in get_playlists():
    await update.message.reply_text("Playlist already exists. Please enter another name.")
    return AddPlaylistConversationState.NEW_PLAYLIST
  
  context.chat_data["add_playlist"]["playlist"] = playlist_name

  await send_confirmation_message(update.message.chat_id, context)
  return AddPlaylistConversationState.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.chat_data["in_conversation"] = False

  download_status_message = await update.message.reply_text("Preparing to download...")

  playlist_name = context.chat_data["add_playlist"]["playlist"]
  song_urls = context.chat_data["add_playlist"]["urls"]
  
  num_successes = num_failures = 0
  for i, song_url in enumerate(song_urls):
    await download_status_message.edit_text(
      f"Downloading {song_url} to playlist '{playlist_name}' ({i+1}/{len(song_urls)})",
      disable_web_page_preview=True,
    )

    try:
      download_audio(song_url, playlist_name)
      num_successes += 1
    except Exception as ex:
      logging.error(f"Error while downloading URL {song_url}: {ex}")
      await update.message.reply_text(
        f"Error occurred while downloading URL {song_url}.",
        disable_web_page_preview=True,
      )
      num_failures += 1

  await download_status_message.edit_text(
    f"Song addition summary: {num_successes} added; {num_failures} failed."
  )

  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Playlist addition cancelled.")
  context.chat_data["in_conversation"] = False
  return ConversationHandler.END

def add_handlers(application: Application):
  application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("add_playlist", start)],
    states={
      AddPlaylistConversationState.URL: [
        MessageHandler(filters=text_message_filter, callback=url),
      ],
      AddPlaylistConversationState.PLAYLIST: [CallbackQueryHandler(callback=playlist)],
      AddPlaylistConversationState.NEW_PLAYLIST: [
        MessageHandler(filters=text_message_filter, callback=new_playlist),
      ],
      AddPlaylistConversationState.CONFIRM: [CommandHandler("confirm", confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
  ))
