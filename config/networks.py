"""
Конфигурация поддерживаемых платформ для загрузки видео.

Содержит:
- NetworkConfig: описание одной сети
- NETWORKS: список всех сетей с настройками
- Константы для YouTube API
"""

from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class NetworkConfig:
    """
    Конфигурация одной социальной сети или платформы.

    Атрибуты:
        key (str): короткое имя сети, используется для импорта загрузчика и путей.
        title (str): отображаемое имя сети в GUI.
        uses_selenium (bool): нужен ли Selenium для загрузки.
        enabled (bool): можно ли включать/отключать сеть без правки кода.
    """
    key: str
    title: str
    uses_selenium: bool
    enabled: bool = True
    platform_settings: dict | None = None


# -----------------------------
# Настройки конкретных платформ
# -----------------------------
YOUTUBE_SETTINGS = {
    "privacy_status": "unlisted",
    "made_for_kids": True,
    "category_id": "22",
    "token_path": Path("token_youtube.pickle"),
    "scopes": ["https://www.googleapis.com/auth/youtube.upload"]
}


# Список всех сетей, поддерживаемых FlowVid
NETWORKS = [
    NetworkConfig(key="rutube",    title="Rutube Reels",    uses_selenium=True),
    NetworkConfig(key="pinterest", title="Pinterest Reels", uses_selenium=False),
    NetworkConfig(key="tiktok",    title="TikTok Reels",    uses_selenium=False),
    NetworkConfig(key="instagram", title="Instagram Reels", uses_selenium=False),
    NetworkConfig(key="vk",        title="VK",              uses_selenium=True),
    NetworkConfig(key="telegram",  title="Telegram",        uses_selenium=True),
    NetworkConfig(key="youtube",   title="YouTube",         uses_selenium=True,  platform_settings=YOUTUBE_SETTINGS),
]