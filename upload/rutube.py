from pathlib import Path
from .base_uploader import BaseUploader
from config.networks import NetworkConfig
from utils.logger import log  


class Uploader(BaseUploader):
    """
    Загрузчик для Rutube Reels.

    Поддерживает интерфейс BaseUploader и UploaderManager.
    Сейчас — заглушка, позже можно подключить Selenium для реальной загрузки.
    """

    def __init__(self, config: NetworkConfig):
        """
        Инициализация загрузчика.

        :param config: NetworkConfig с настройками платформы
        """
        self.config = config
        profile_path = None
        if config.platform_settings:
            profile_path = config.platform_settings.get("profile_path")
        super().__init__(profile_path)
        log(f"[{self.config.title}] Инициализация завершена", level="info")

    def check_login(self) -> bool:
        """
        Проверка авторизации на Rutube.

        :return: True если пользователь авторизован, False иначе
        """
        # TODO: Реальная проверка через Selenium
        log(f"[{self.config.title}] Проверка логина (заглушка) — OK", level="info")
        return True

    def upload(
        self,
        video_file: str | Path,
        title: str,
        description: str,
        tags: list[str] | None = None,
        thumbnail: str | Path | None = None
    ) -> dict:
        """
        Заглушка метода загрузки видео.

        :param video_file: путь к видео
        :param title: заголовок видео
        :param description: описание видео
        :param tags: список тегов
        :param thumbnail: путь к миниатюре
        :return: dict с результатом для UploaderManager
        """
        video_file = Path(video_file)
        if not video_file.exists():
            msg = f"Видео не найдено: {video_file}"
            log(f"[{self.config.title}] {msg}", level="error")
            return {
                "success": False,
                "platform": self.config.title,
                "error": msg
            }

        if thumbnail:
            thumbnail = Path(thumbnail)
            if not thumbnail.exists():
                log(f"[{self.config.title}] Миниатюра не найдена: {thumbnail}", level="warning")

        tags = tags or []

        # Эмуляция загрузки
        log(f"[{self.config.title}] Загружаю видео: {video_file}", level="info")
        log(f"[{self.config.title}] Title: {title}", level="info")
        log(f"[{self.config.title}] Desc: {description[:100]}", level="info")
        log(f"[{self.config.title}] Tags: {tags}", level="info")
        if thumbnail:
            log(f"[{self.config.title}] Thumbnail: {thumbnail}", level="info")

        # Возвращаем успешный результат
        return {
            "success": True,
            "platform": self.config.title,
            "video_path": str(video_file),
            "message": "Загрузка выполнена (заглушка)"
        }
