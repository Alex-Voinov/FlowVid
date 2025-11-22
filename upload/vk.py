import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERVICE_TOKEN = os.getenv("VK_SERVICE_TOKEN")
OWNER_ID = int(os.getenv("VK_OWNER_ID"))  # группа: отрицательный ID, пользователь: положительный

if not SERVICE_TOKEN or not OWNER_ID:
    raise RuntimeError("VK_SERVICE_TOKEN или VK_OWNER_ID не заданы в .env")


def upload_video(video_path: str, title: str = "", description: str = "", tags: list[str] = [], thumbnail: str = None):
    """
    Загружает видео в VK (личный профиль или сообщество)
    """

    # 1. Получаем сервер для загрузки
    upload_url_req = requests.get(
        "https://api.vk.com/method/video.save",
        params={
            "access_token": SERVICE_TOKEN,
            "v": "5.131",
            "name": title,
            "description": description,
            "privacy_view": "nobody", # nobody - скрыто, потом поменять на all
            "group_id": abs(OWNER_ID) if OWNER_ID < 0 else None
        },
    ).json()

    if "error" in upload_url_req:
        raise Exception(f"VK API error (video.save): {upload_url_req['error']}")

    upload_url = upload_url_req["response"]["upload_url"]

    # 2. Загружаем видео
    with open(video_path, "rb") as f:
        files = {"video_file": f}
        upload_resp = requests.post(upload_url, files=files).json()

    if "error" in upload_resp:
        raise Exception(f"VK API error (upload): {upload_resp['error']}")

    video_id = upload_resp["video_id"]
    owner_id = upload_resp["owner_id"]

    print(f"[VK] Видео загружено: https://vk.com/video{owner_id}_{video_id}")
    return f"https://vk.com/video{owner_id}_{video_id}"
