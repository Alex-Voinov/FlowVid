from pathlib import Path
import asyncio
from os import getenv
from telethon import TelegramClient, errors

from config.networks import NetworkConfig
from utils.logger import log  


class Uploader:
    """
    Загрузчик видео на Telegram через Telethon.

    Секреты берутся из .env:
        - TG_API_ID
        - TG_API_HASH
        - TG_CHANNEL

    Конфигурация для UI и логов — из NetworkConfig.
    """

    def __init__(self, config: NetworkConfig):
        self.config = config
        self.title = config.title

        # Секреты из env
        self.api_id = getenv("TG_API_ID")
        self.api_hash = getenv("TG_API_HASH")
        self.channel = getenv("TG_CHANNEL")

        if not all([self.api_id, self.api_hash, self.channel]):
            raise RuntimeError(f"[{self.title}] Telegram secrets missing in environment")

        self.api_id = int(self.api_id)

        # Путь к файлу сессии Telethon
        self.session_path = Path("telegram_session")

        # Кешируем клиента, чтобы не создавать заново каждый раз
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        self._connected = False

    async def _connect(self):
        """Подключаемся к Telegram, если ещё не подключены."""
        if not self._connected:
            await self.client.start()
            self._connected = True
            log(f"[{self.title}] Клиент Telegram подключен", level="info")

    async def _send_video(self, video_file: Path, title: str):
        """Асинхронная отправка видео через Telethon с прогрессом."""
        await self._connect()

        def progress_callback(sent_bytes, total_bytes):
            percent = sent_bytes / total_bytes * 100
            log(f"[{self.title}] Загрузка: {percent:.2f}%", level="info")

        try:
            await self.client.send_file(
                self.channel,
                video_file,
                caption=title,
                progress_callback=progress_callback
            )
            log(f"[{self.title}] Видео загружено: {video_file}", level="info")
        except errors.TelegramError as e:
            log(f"[{self.title}] Ошибка при отправке видео: {e}", level="error")
            raise

    def upload(
        self,
        video_file: str | Path,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        thumbnail: str | Path | None = None
    ) -> dict:
        """
        Синхронная обертка для вызова из UploaderManager.

        :param video_file: путь к видео
        :param title: заголовок видео
        :param description: игнорируется
        :param tags: игнорируются
        :param thumbnail: игнорируется
        """
        video_file = Path(video_file)
        if not video_file.exists():
            log(f"[{self.title}] Видео не найдено: {video_file}", level="error")
            return {"success": False, "error": f"Видео не найдено: {video_file}"}

        try:
            asyncio.run(self._send_video(video_file, title))
        except Exception as e:
            return {"success": False, "error": str(e), "platform": self.title}

        return {"success": True, "platform": self.title, "video_path": str(video_file)}
