import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from core.browser_profile import BrowserProfile
from utils.logger import log
from utils.paths import site_profile
import time
from typing import Dict

class SeleniumManager:
    """
    Singleton manager. Хранит драйверы по имени профиля.
    start(profile_name) -> webdriver.Chrome
    stop(profile_name) / stop_all()
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._drivers: Dict[str, webdriver.Chrome] = {}
        self._drivers_lock = threading.RLock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self, profile_name: str = "default", headless: bool = False, extra_args: list = None, timeout: int = 20):
        """
        Запускает/возвращает драйвер для profile_name.
        Если драйвер уже запущен — вернёт существующий.
        """
        extra_args = extra_args or []
        with self._drivers_lock:
            if profile_name in self._drivers:
                try:
                    # quick alive check
                    _ = self._drivers[profile_name].title
                    log(f"Reusing existing driver for profile {profile_name}")
                    return self._drivers[profile_name]
                except Exception:
                    log(f"Existing driver for {profile_name} не отвечает — перезапускаем", level="warning")
                    self.stop(profile_name)

            # ensure profile lock removed
            BrowserProfile.remove_lock(profile_name)

            profile_path = site_profile(profile_name)
            options = Options()
            options.add_argument(f"--user-data-dir={profile_path}")
            # do NOT set --profile-directory to avoid CDP conflicts
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
            # safety flags
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            for a in extra_args:
                options.add_argument(a)

            try:
                log(f"Запуск Chrome для профиля {profile_name} (path={profile_path})")
                driver = webdriver.Chrome(options=options)  # CDP встроенный
                # wait for browser to be usable
                started = False
                start_ts = time.time()
                while time.time() - start_ts < timeout:
                    try:
                        _ = driver.current_url  # will raise if not ready
                        started = True
                        break
                    except Exception:
                        time.sleep(0.2)
                if not started:
                    log("Chrome запустился, но не отвечает в отведённое время", level="warning")
                self._drivers[profile_name] = driver
                return driver
            except WebDriverException as e:
                log(f"Ошибка запуска Chrome: {e}", level="error")
                raise

    def stop(self, profile_name: str):
        with self._drivers_lock:
            drv = self._drivers.pop(profile_name, None)
            if drv:
                try:
                    drv.quit()
                except Exception:
                    try:
                        # best-effort kill processes for profile (platform dependent)
                        log(f"Не удалось корректно закрыть драйвер для {profile_name}", level="warning")
                    except Exception:
                        pass

    def stop_all(self):
        with self._drivers_lock:
            names = list(self._drivers.keys())
            for name in names:
                self.stop(name)
            log("Остановлены все драйверы Selenium")
