import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config.networks import NetworkConfig
from utils.logger import log 


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
        self.privacy_status = self.settings.get("privacy_status", "unlisted")
        self.made_for_kids = self.settings.get("made_for_kids", True)
        self.category_id = self.settings.get("category_id", "22")
        self.chunk_size = self.settings.get("chunk_size", 256 * 1024)

        # Настраиваем путь к client_secret
        default_secret = Path(__file__).parent.parent / "client_secret.json"
        self.client_secret_path = Path(self.settings.get("client_secret_path", default_secret))

        if not self.client_secret_path.exists():
            raise FileNotFoundError(f"Client secret not found: {self.client_secret_path}")

        # OAuth сервер
        self.oauth_host = self.settings.get("oauth_host", "localhost")
        self.oauth_port = self.settings.get("oauth_port", 8080)

        self.service = self._get_authenticated_service()

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
                    log("[YouTube] Токен обновлён через refresh_token", level="info")
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.client_secret_path), self.scopes
                    )
                    creds = flow.run_local_server(
                        host=self.oauth_host,
                        port=self.oauth_port,
                        authorization_prompt_message="Откройте ссылку для авторизации Google:"
                    )
                    log("[YouTube] Новый токен получен через OAuth", level="info")
                # Сохраняем токен
                with open(self.token_path, "wb") as f:
                    pickle.dump(creds, f)
            except Exception as e:
                log(f"[YouTube] Ошибка OAuth: {e}", level="error")
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
            log(f"[YouTube] Видео не найдено: {video_file}", level="error")
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

        try:
            # Загрузка видео
            media = MediaFileUpload(video_file, chunksize=self.chunk_size, resumable=True)
            request = self.service.videos().insert(part="snippet,status", body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    log(f"[YouTube] Загрузка: {int(status.progress() * 100)}%", level="info")

            log(f"[YouTube] Видео загружено: https://youtu.be/{response['id']}", level="info")

            # Загрузка миниатюры
            if thumbnail:
                thumbnail = Path(thumbnail)
                if thumbnail.exists():
                    ext = thumbnail.suffix.lower()
                    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                    media_thumb = MediaFileUpload(thumbnail, mimetype=mime)
                    self.service.thumbnails().set(videoId=response["id"], media_body=media_thumb).execute()
                    log(f"[YouTube] Миниатюра загружена: {thumbnail}", level="info")
                else:
                    log(f"[YouTube] Миниатюра не найдена: {thumbnail}", level="warning")

            return {"success": True, "video_id": response["id"], "url": f"https://youtu.be/{response['id']}"}

        except Exception as e:
            log(f"[YouTube] Ошибка загрузки: {e}", level="error")
            return {"success": False, "error": str(e)}
