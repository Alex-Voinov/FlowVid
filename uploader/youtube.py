import os
import pickle
import google.auth.transport.requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = "token_youtube.pickle"

def get_authenticated_service():
    creds = None

    # Загружаем сохранённый токен
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Если нет токена или он просрочен
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("YT_CLIENT_SECRET"), SCOPES,
                redirect_uri="http://localhost"
            )
            creds = flow.run_local_server(host="localhost", port=8080, authorization_prompt_message="Открой ссылку в браузере для авторизации:")
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

def upload_video(video_file: str, title: str, description: str = "",
                 tags: list[str] = None, thumbnail: str = None):

    youtube = get_authenticated_service()
    tags = tags or []
    # Добавляем хэштеги ТОЛЬКО в описание
    description += "\n\n" + " ".join([f"#{tag}" for tag in tags])
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": 'unlisted',
            "selfDeclaredMadeForKids": True,
        },
    }

    media = MediaFileUpload(video_file, chunksize=256 * 1024, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[YouTube] Загрузка: {int(status.progress() * 100)}%")

    print(f"[YouTube] Видео загружено: https://youtu.be/{response['id']}")

    # === Миниатюра ===
    if thumbnail:
        # указание MIME обязательно
        ext = thumbnail.lower()
        mime = "image/jpeg" if ext.endswith(".jpg") or ext.endswith(".jpeg") else "image/png"

        media_thumb = MediaFileUpload(thumbnail, mimetype=mime)
        youtube.thumbnails().set(
            videoId=response["id"],
            media_body=media_thumb
        ).execute()

        print(f"[YouTube] Миниатюра загружена: {thumbnail}")

