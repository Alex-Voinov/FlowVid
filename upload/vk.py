from pathlib import Path
from time import sleep, time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base_uploader import BaseUploader
from utils.logger import log
from core.selenium_manager import SeleniumManager


class Uploader(BaseUploader):
    """
    Загрузчик видео в VK для FlowVid.

    Основные особенности:
    - Авторизация отслеживается ТОЛЬКО по URL (не ломается при изменениях DOM).
    - Поддержка всех промежуточных VK/ID/redirect URL.
    - Все селекторы, тайминги и кнопки — в config.platform_settings.
    - Чистая структура и подробная документация.
    """

    def __init__(self, config):
        """
        Args:
            config: NetworkConfig с описанием платформы + селекторов.
        """
        self.config = config
        super().__init__(getattr(config, "profile_path", None))

        self.ps = config.platform_settings
        log(f"[{self.config.title}] Инициализация завершена", level="info")

    # ================================================================
    # ОСНОВНОЙ МЕТОД
    # ================================================================
    def upload(
        self,
        video_file: str | Path,
        title: str = "",
        description: str = "",
        tags: list[str] | None = None,
        thumbnail: str | Path | None = None,
        profile_name: str = "default",
    ):
        """Полный цикл загрузки видео."""
        video_file = self._validate_video(video_file)
        thumbnail = self._validate_thumbnail(thumbnail)

        driver = SeleniumManager.instance().start(profile_name=profile_name, headless=False)
        wait = WebDriverWait(driver, self.ps.get("default_wait", 20))

        # 1. Переходим на страницу группы
        group_url = f"https://vk.com/{self.ps['group_name']}"
        log(f"[{self.config.title}] Открываем группу: {group_url}")
        driver.get(group_url)

        # 2. Нужна ли авторизация
        self._handle_login_if_needed(driver)

        # 3. Кнопка "Добавить"
        self._click_add_button(driver, wait)

        # 4. Загрузка файла
        self._upload_video_file(driver, wait, video_file)

        # 5. Ожидание обработки
        self._wait_video_processing()

        # 6. Метаданные
        self._fill_metadata(driver, wait, title, description, tags)

        # 7. URL результата
        video_url = self._get_video_url(wait)

        log(f"[{self.config.title}] Видео успешно загружено: {video_url}", level="success")

        return {
            "success": True,
            "platform": self.config.title,
            "video_path": str(video_file),
            "video_url": video_url,
            "message": "Видео успешно загружено!",
        }

    # ================================================================
    # АВТОРИЗАЦИЯ
    # ================================================================
    def _handle_login_if_needed(self, driver):
        """
        Ищет кнопки входа (список селекторов — в config).
        Если кнопка видима → кликаем → ждём завершения авторизации по URL.
        """
        for selector in self.ps["login_buttons"]:
            try:
                btn = driver.find_element(By.XPATH, selector)
                if btn.is_displayed():
                    log(f"[{self.config.title}] Клик по кнопке входа: {selector}")
                    btn.click()
                    self._wait_for_auth(driver)
                    return
            except Exception:
                continue

        log(f"[{self.config.title}] Авторизация не требуется (кнопки входа не найдены)")

    def _wait_for_auth(self, driver):
        """
        Ждёт, пока:
        1. пользователь уйдёт со стартовой страницы
        2. затем снова вернётся на неё

        Работает со всеми vk.com/id.vk.com/login?u редиректами.
        """
        start_url = driver.current_url
        max_time = self.ps.get("max_auth_time", 180)
        poll = self.ps.get("poll_interval", 0.5)

        log(f"[{self.config.title}] Ожидание начала авторизации…")

        start_time = time()
        left_start = False

        while True:
            current = driver.current_url

            # Уход со стартового URL
            if not left_start and current != start_url:
                left_start = True
                log(f"[{self.config.title}] Авторизация началась → {current}")

            # Возврат к исходному URL
            if left_start and current == start_url:
                log(f"[{self.config.title}] Авторизация завершена → {current}")
                return True

            # Тайм-аут
            if time() - start_time > max_time:
                log(f"[{self.config.title}] Авторизация не завершилась вовремя", level="error")
                return False

            sleep(poll)

    # ================================================================
    # ЗАГРУЗКА ФАЙЛА
    # ================================================================
    def _click_add_button(self, driver, wait):
        xpath = self.ps["btn_add_xpath"]
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()
        log(f"[{self.config.title}] Нажали кнопку 'Добавить'")

    def _upload_video_file(self, driver, wait, video_file):
        xpath = self.ps["file_input_xpath"]
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        file_input.send_keys(str(video_file.resolve()))
        log(f"[{self.config.title}] Видео отправлено: {video_file}")

    # ================================================================
    # ОБРАБОТКА И МЕТА
    # ================================================================
    def _wait_video_processing(self):
        """
        Заглушка. При желании можно заменить на отслеживание DOM.
        """
        log(f"[{self.config.title}] Ожидание обработки видео…")
        sleep(self.ps.get("processing_sleep", 5))

    def _fill_metadata(self, driver, wait, title, description, tags):
        """
        Заглушка — интерфейс VK для заполнения метаданных сложный.
        Оставлено для реализации в будущем.
        """
        if title or description:
            log(f"[{self.config.title}] (Заглушка) Заполнение title/description")

    def _get_video_url(self, wait):
        """Возвращает URL загруженного видео."""
        try:
            element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'vk.com/video')]"))
            )
            return element.get_attribute("href")
        except Exception:
            log(f"[{self.config.title}] Не удалось получить ссылку на видео", level="warning")
            return None

    # ================================================================
    # ВАЛИДАЦИЯ
    # ================================================================
    def _validate_video(self, video_file):
        path = Path(video_file)
        if not path.exists():
            raise FileNotFoundError(f"Видео не найдено: {path}")
        return path

    def _validate_thumbnail(self, thumbnail):
        if not thumbnail:
            return None
        thumbnail = Path(thumbnail)
        if not thumbnail.exists():
            log(f"[{self.config.title}] миниатюра не найдена: {thumbnail}", level="warning")
            return None
        return thumbnail
