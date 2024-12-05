
import datetime
import logging
import os, time, asyncio, json
from bot.localisation import Localisation
from bot import (
    DOWNLOAD_LOCATION, 
    AUTH_USERS,
    SESSION_NAME,
    data,
    app  
)
from bot.helper_funcs.ffmpeg import (
    convert_video,
    media_info,
    take_screen_shot
)
from bot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    TimeFormatter,
    humanbytes
)

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

os.system("wget https://te.legra.ph/file/86e958f9fc0d7cbdf1a28.jpg -O thumb.jpg")

CURRENT_PROCESSES = {}
CHAT_FLOOD = {}
broadcast_ids = {}
bot = app

async def incoming_start_message_f(bot, update):
    await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.START_TEXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Channel', url='https://t.me/Anime_Sensei_Network')
                ]
            ]
        ),
        reply_to_message_id=update.id,
    )
    
async def incoming_compress_message_f(update, custom_filename=None):
    """Handle file compression requests."""
    d_start = time.time()
    status_file = os.path.join(DOWNLOAD_LOCATION, "status.json")

    def get_full_filename(filepath):
        return os.path.splitext(os.path.basename(filepath))[0]

    sent_message = await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.DOWNLOAD_START,
        reply_to_message_id=update.id
    )

    try:
        # Save status to JSON
        with open(status_file, "w") as f:
            status_msg = {"running": True, "message": sent_message.id}
            json.dump(status_msg, f, indent=2)

        # Download the media
        video = await bot.download_media(
            message=update,
            progress=progress_for_pyrogram,
            progress_args=(
                bot,
                Localisation.DOWNLOAD_START,
                sent_message,
                d_start
            )
        )
        if not video:
            await sent_message.edit_text(text="⚠️ Download stopped ⚠️")
            LOGGER.info("Download stopped")
            return

        # Apply custom filename if provided
        if custom_filename:
            new_path = os.path.join(os.path.dirname(video), custom_filename)
        else:
            # Use full original filename with extension
            full_filename = get_full_filename(video) + os.path.splitext(video)[1]
            new_path = os.path.join(os.path.dirname(video), full_filename)

        try:
            os.rename(video, new_path)
            video = new_path
            LOGGER.info(f"Renamed file to: {new_path}")
        except Exception as e:
            LOGGER.exception(f"Error renaming file: {e}")
            await sent_message.edit_text(text="⚠️ Failed to apply custom filename ⚠️")
            return

        await sent_message.edit_text(text=Localisation.SAVED_RECVD_DOC_FILE)
        
        duration, bitrate = await media_info(video)
        if not duration or not bitrate:
            await sent_message.edit_text(text="⚠️ Failed to retrieve video metadata ⚠️")
            return

        # Take a thumbnail screenshot
        thumb_image_path = await take_screen_shot(
            video,
            os.path.dirname(os.path.abspath(video)),
            (duration / 2)
        )

        await sent_message.edit_text(text=Localisation.COMPRESS_START)

        # Compress the video
        c_start = time.time()
        compressed_file = await convert_video(
            video, DOWNLOAD_LOCATION, duration, bot, sent_message, None
        )

        if compressed_file == "stopped" or not compressed_file:
            await sent_message.edit_text(text="⚠️ Compression failed ⚠️")
            return

        # Upload the compressed file
        await sent_message.edit_text(text=Localisation.UPLOAD_START)
        await bot.send_document(
            chat_id=update.chat.id,
            document=compressed_file,
            caption=custom_filename or os.path.basename(compressed_file),
            force_document=True,
            thumb="thumb.jpg",
            reply_to_message_id=update.id,
            progress=progress_for_pyrogram,
            progress_args=(
                bot,
                Localisation.UPLOAD_START,
                sent_message,
                time.time()
            )
        )
        await sent_message.delete()
    except Exception as e:
        LOGGER.exception(f"Error in compression: {e}")
        await sent_message.edit_text(text="⚠️ An error occurred ⚠️")
    finally:
        if os.path.exists(status_file):
            os.remove(status_file)


async def incoming_cancel_message_f(bot, update):
    if update.from_user.id not in AUTH_USERS:      
        try:
            await update.message.delete()
        except:
            pass
        return

    status = os.path.join(DOWNLOAD_LOCATION, "status.json")
    if os.path.exists(status):
        reply_markup = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Yes 🚫", callback_data="fuckingdo"),
                InlineKeyboardButton("No 🤗", callback_data="fuckoff")
            ]]
        )
        await update.reply_text("Are you sure? 🚫 This will stop the compression!", reply_markup=reply_markup, quote=True)
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text="No active compression exists",
            reply_to_message_id=update.id
        )
