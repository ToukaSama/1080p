# utils.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

import os
from bot import data
from bot.plugins.incoming_message_fn import incoming_compress_message_f
from pyrogram.types import Message


def checkKey(dict, key):
  if key in dict.keys():
    return True
  else:
    return False

async def on_task_complete():
    del data[0]
    if len(data) > 0:
        # Pass None as default for custom_filename if not specified
        await add_task(data[0])

async def add_task(message, custom_filename=None):
    try:
        os.system('rm -rf /app/downloads/*')
        # Attach custom filename to message if provided
        if custom_filename:
            message.custom_filename = custom_filename
        
        await incoming_compress_message_f(message, custom_filename)
    except Exception as e:
        LOGGER.info(f"Error in add_task: {e}")
    await on_task_complete()
