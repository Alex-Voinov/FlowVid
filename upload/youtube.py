import pickle
from pathlib import Path
import logging

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config.networks import NetworkConfig

logger = logging.getLogger("flowvid")


class Uploader:
    """
    Загрузчик видео на YouTube через YouTube Data API v3.

    Настройки берутся из NetworkConfig.platform_settings:
        - scopes: список OAuth-скоупов
        - token_path: путь к файлу токена
        - privacy_status: 'public' | 'unlisted' | 'private'
        - made_for_kids: True | False
        - category_id: ID категории видео (строка)
    """

    def __init__(self, config: NetworkConfig):
        self.config = config
        self.settings = config.platform_settings or {}

        self.scopes = self.settings.get(
            "scopes", ["https://www.googleapis.com/auth/youtube.upload"]
        )
        self.token_path: Path = Path(self.settings.get("token_path", "token_youtube.pickle"))
        self.privacy_status: str = self.settings.get("privacy_status", "unlisted")
        self.made_for_kids: bool = self.settings.get("made_for_kids", True)
        self.category_id: str = self.settings.get("category_id", "22")

        # Путь к client_secret.json в проекте (корень проекта)
        self.client_secret_path = Path(__file__).parent.parent / "client_secret.json"
        if not self.client_secret_path.exists():
            raise FileNotFoundError(f"Client secret not found: {self.client_secret_path}")

        # Инициализация YouTube API один раз
        self.service = self._get_authenticated_service()
        logger.info("[YouTube] Сервис инициализирован")

    def _get_authenticated_service(self):
        """Возвращает авторизованный объект YouTube API."""
        creds = None

        # Загружаем токен, если есть
        if self.token_path.exists():
            with open(self.token_path, "rb") as f:
                creds = pickle.load(f)

        # Проверяем валидность токена
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    logger.info("[YouTube] Токен обновлён через refresh_token")
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.client_secret_path), self.scopes
                    )
                    creds = flow.run_local_server(
                        host="localhost",
                        port=8080,
                        authorization_prompt_message="Откройте ссылку для авторизации Google:"
                    )
                    logger.info("[YouTube] Новый токен получен через OAuth")
                # Сохраняем токен
                with open(self.token_path, "wb") as f:
                    pickle.dump(creds, f)
            except Exception as e:
                logger.error(f"[YouTube] Ошибка OAuth: {e}")
                raise RuntimeError(f"YouTube OAuth failed: {e}") from e

        return build("youtube", "v3", credentials=creds)

    def upload(
        self,
        video_file: str | Path,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        thumbnail: str | Path | None = None
    ) -> dict:
        """Загружает видео на YouTube с миниатюрой и тегами."""
        video_file = Path(video_file)
        if not video_file.exists():
            logger.error(f"[YouTube] Видео не найдено: {video_file}")
            return {"success": False, "error": f"Видео не найдено: {video_file}"}

        tags = tags or []
        description_full = f"{description}\n\n{' '.join(f'#{t}' for t in tags)}"

        # Подготавливаем тело запроса
        body = {
            "snippet": {
                "title": title,
                "description": description_full,
                "tags": tags,
                "categoryId": self.category_id,
            },
            "status": {
                "privacyStatus": self.privacy_status,
                "selfDeclaredMadeForKids": self.made_for_kids,
            },
        }

        # Загрузка видео
        media = MediaFileUpload(video_file, chunksize=256 * 1024, resumable=True)
        request = self.service.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"[YouTube] Загрузка: {int(status.progress() * 100)}%")

        logger.info(f"[YouTube] Видео загружено: https://youtu.be/{response['id']}")

        # Загрузка миниатюры
        if thumbnail:
            thumbnail = Path(thumbnail)
            if thumbnail.exists():
                ext = thumbnail.suffix.lower()
                mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                media_thumb = MediaFileUpload(thumbnail, mimetype=mime)
                self.service.thumbnails().set(videoId=response["id"], media_body=media_thumb).execute()
                logger.info(f"[YouTube] Миниатюра загружена: {thumbnail}")
            else:
                logger.warning(f"[YouTube] Миниатюра не найдена: {thumbnail}")

        return {"success": True, "video_id": response["id"], "url": f"https://youtu.be/{response['id']}"}
