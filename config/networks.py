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
    # Видео-параметры
    "privacy_status": "unlisted",
    "made_for_kids": True,
    "category_id": "22",

    # OAuth
    "token_path": Path("token_youtube.pickle"),
    "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    "client_secret_path": Path("client_secret.json"),   # <-- новая опция
    "oauth_host": "localhost",
    "oauth_port": 8080,

    # Upload
    "chunk_size": 256 * 1024, 
}

RUTUBE_SETTINGS = {
    "upload_url": "https://studio.rutube.ru/uploader/",
    "editor_url": "https://studio.rutube.ru/video/",
    "base_video_url": "https://rutube.ru/video/",

    # Таймауты
    "wait_timeout": 20,
    "post_ready_delay": 1.0,
    "post_publish_delay": 1.0,
    "dialog_open_delay": 1.0,

    # Категория по умолчанию
    "default_category": "Дизайн",

    # Поведение
    "scroll_into_view": True
}

VK_SETTINGS = {
    "group_name": "free_eg",

    # Кнопка "Добавить" (в сообществе)
    "btn_add_xpath": "//span[text()='Добавить']/ancestor::span[contains(@class,'vkuiButton__in')]",

    # Поле выбора файла
    "file_input_xpath": "//input[@type='file' and contains(@class,'vkuiVisuallyHidden')]",

    # Кнопки для входа
    "login_buttons": [
        "//button[contains(text(),'Войти')]",
        "//button[contains(@class,'quick_login_button')]",
        "//button[contains(@class,'quick_reg_button')]"
    ]
}



# Список всех сетей, поддерживаемых FlowVid
NETWORKS = [
    NetworkConfig(key="rutube",    title="Rutube Reels",    uses_selenium=True,  platform_settings=RUTUBE_SETTINGS),
    NetworkConfig(key="pinterest", title="Pinterest Reels", uses_selenium=False),
    NetworkConfig(key="tiktok",    title="TikTok Reels",    uses_selenium=False),
    NetworkConfig(key="instagram", title="Instagram Reels", uses_selenium=False),
    NetworkConfig(key="vk",        title="VK",              uses_selenium=True,  platform_settings=VK_SETTINGS),
    NetworkConfig(key="telegram",  title="Telegram",        uses_selenium=True),
    NetworkConfig(key="youtube",   title="YouTube",         uses_selenium=True,  platform_settings=YOUTUBE_SETTINGS),
]