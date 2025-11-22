import os
import shutil
from utils.paths import chrome_profiles_dir
from utils.logger import log

class BrowserProfile:
    @staticmethod
    def path(profile_name: str) -> str:
        p = os.path.join(chrome_profiles_dir(), profile_name)
        os.makedirs(p, exist_ok=True)
        return p

    @staticmethod
    def clear(profile_name: str):
        path = BrowserProfile.path(profile_name)
        log(f"Очистка профиля: {profile_name}")
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except Exception as e:
                log(f"Не удалось удалить {item_path}: {e}", level="warning")

    @staticmethod
    def remove_lock(profile_name: str):
        lock_path = os.path.join(BrowserProfile.path(profile_name), "LOCK")
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
                log(f"Удалён lock-файл профиля {profile_name}")
            except Exception:
                log(f"Не удалось удалить lock-файл {profile_name}", level="warning")
