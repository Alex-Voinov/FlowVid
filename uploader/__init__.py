from . import youtube, tiktok, instagram, telegram

def upload(video_file: str, networks: list, title: str, description: str, tags: list, thumbnail: str):
    """
    Загружает видео на указанные сети.
    networks: ["YouTube", "TikTok", "Instagram"]
    """
    if not video_file:
        print("Нет видео для загрузки!")
        return

    if "Telegram" in networks:
        telegram.upload_video(video_file, title, description, tags, thumbnail)
    if "YouTube" in networks:
        youtube.upload_video(video_file, title, description, tags, thumbnail)
    if "TikTok" in networks:
        tiktok.upload_video(video_file, title, description, tags, thumbnail)
    if "Instagram" in networks:
        instagram.upload_video(video_file, title, description, tags, thumbnail)

__all__ = ["upload"]