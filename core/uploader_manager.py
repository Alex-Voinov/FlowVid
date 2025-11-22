from importlib import import_module
from utils.logger import log
from core.selenium_manager import SeleniumManager
from config.networks import NETWORKS, NetworkConfig
from typing import Callable


class UploaderManager:
    """
    Менеджер загрузки видео на соцсети.
    Список сетей передается ключами (key).
    Динамически импортирует модули из папки upload.
    Управляет Selenium при необходимости.
    """

    @staticmethod
    def _get_network_config(key: str) -> NetworkConfig | None:
        return next((net for net in NETWORKS if net.key == key), None)

    @staticmethod
    def _import_uploader(module_path: str):
        try:
            return import_module(module_path)
        except ModuleNotFoundError:
            log(f"Uploader module not found: {module_path}", level="warning")
        except Exception as e:
            log(f"Error importing uploader '{module_path}': {e}", level="error")
        return None

    @staticmethod
    def _get_upload_callable(mod, cfg: NetworkConfig) -> Callable | None:
        """
        Возвращает метод `upload` из класса `Uploader` модуля.

        Параметры:
            mod: импортированный модуль загрузчика

        Возвращает:
            callable — метод `Uploader().upload`
            None — если класс или метод отсутствуют или при инициализации произошла ошибка
        """

        uploader_cls = getattr(mod, "Uploader", None)
        if not uploader_cls:
            log(f"No Uploader class in module {mod}", level="warning")
            return None

        try:
            instance = uploader_cls(cfg)
            upload_method = getattr(instance, "upload", None)
            if callable(upload_method):
                return upload_method
            else:
                log(f"Uploader.upload is not callable in module {mod}", level="warning")
                return None
        except Exception as e:
            log(f"Failed to initialize Uploader() in {mod}: {e}", level="error")
            return None


    @staticmethod
    def upload(
        video_file: str,
        networks: list[str],
        title: str,
        description: str,
        tags: list[str] | None = None,
        thumbnail: str | None = None
    ) -> dict:
        """
        Загружает видео на выбранные соцсети.

        Параметры:
            video_file: путь к видеофайлу
            networks: список ключей соцсетей, указанных в config/network.py
            title: заголовок публикации
            description: описание видео
            tags: список тегов (добавляются при необходимости)
            thumbnail: путь к миниатюре (если поддерживается загрузчиком)

        Возвращает:
            dict:
                {"ok": True} — если загрузка прошла успешно на все сети
                {"errors": [...]} — если возникли ошибки
        """
        # ---------------------------------------------------------
        # Проверка входных данных
        # ---------------------------------------------------------
        if not video_file:
            log("Видео не указано.", level="error")
            return {"errors": ["video missing"]}

        errors: list[str] = []
        tags = tags or []

        # ---------------------------------------------------------
        # Определяем, нужен ли Selenium (для хотя бы одной сети)
        # ---------------------------------------------------------
        selenium_required = any(
            (cfg := UploaderManager._get_network_config(k)) and cfg.enabled and cfg.uses_selenium
            for k in networks
        )
        selenium = SeleniumManager.instance() if selenium_required else None

        # ---------------------------------------------------------
        # Основной цикл по выбранным сетям
        # ---------------------------------------------------------
        for key in networks:
            cfg = UploaderManager._get_network_config(key)

            # Пропускаем несуществующие или отключенные сети
            if not cfg:
                errors.append(f"{key}: config not found")
                continue
            if not cfg.enabled:
                log(f"{key} disabled, skipping", level="info")
                continue

            # Импортируем модуль загрузчика
            mod = UploaderManager._import_uploader(f"upload.{cfg.key}")
            if not mod:
                errors.append(f"{key}: module missing")
                continue

            # Получаем функцию загрузки
            upload_callable = UploaderManager._get_upload_callable(mod, cfg)
            if not upload_callable:
                errors.append(f"{key}: no entrypoint")
                continue

            # Выполняем загрузку
            try:
                log(f"[UPLOAD] {cfg.key} | selenium={cfg.uses_selenium} | video={video_file}")
                upload_callable(video_file, title, description, tags, thumbnail)
            except Exception as e:
                log(f"{key}: {e}", level="error")
                errors.append(f"{key}: {e}")

        # ---------------------------------------------------------
        # Останавливаем Selenium, если он использовался
        # ---------------------------------------------------------
        if selenium:
            try:
                selenium.stop_all()
            except Exception as e:
                log(f"Error stopping Selenium: {e}", level="warning")

        # ---------------------------------------------------------
        # Результат
        # ---------------------------------------------------------
        return {"errors": errors} if errors else {"ok": True}

