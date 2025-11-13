from os import getenv
from dotenv import load_dotenv
from telethon import TelegramClient
import asyncio

load_dotenv()

API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
CHANNEL = getenv("CHANNEL")

# Имя файла сессии Telethon
SESSION_NAME = "telegram_session"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def send_video(video_file, title):

    await client.start()  # при первом запуске запросит код
    with open(video_file, "rb") as f:
        await client.send_file(CHANNEL, f, caption=title)
    print(f"[Telegram] Видео загружено: {video_file}")

def upload_video(video_file, title):
    """
    Синхронная обертка для вызова из обычного кода
    """
    asyncio.run(send_video(video_file, title))
