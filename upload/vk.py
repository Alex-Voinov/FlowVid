from pathlib import Path
from .base_uploader import BaseUploader
from utils.logger import log
from core.selenium_manager import SeleniumManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time


class Uploader(BaseUploader):
    """
    Загрузчик видео в VK группу через Selenium.
    Проверка авторизации делается только по URL:
    - URL меняется после клика "Войти" (авторизация началась)
    - URL возвращается на исходный (авторизация завершена)
    """

    def __init__(self, config):
        self.config = config
        profile_path = getattr(config, "profile_path", None)
        super().__init__(profile_path)
        log(f"[{self.config.title}] Инициализация завершена", level="info")

    # ================================================================
    # Основной метод загрузки
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
        video_file = self._validate_video(video_file)
        thumbnail = self._validate_thumbnail(thumbnail)

        driver = SeleniumManager.instance().start(profile_name=profile_name, headless=False)
        wait = WebDriverWait(driver, 20)

        # Открываем страницу группы
        group_url = f"https://vk.com/{self.config.platform_settings.get('group_name')}"
        log(f"[{self.config.title}] Открываем группу: {group_url}")
        driver.get(group_url)

        # Проверяем авторизацию
        self._handle_login_if_needed(driver, wait)

        # Кликаем "Добавить"
        add_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Добавить']/ancestor::span[contains(@class,'vkuiButton__in')]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
        add_btn.click()
        log(f"[{self.config.title}] Кликнули 'Добавить'")
        time.sleep(1)

        # Загружаем видео через input
        file_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file' and contains(@class,'vkuiVisuallyHidden__focusableInput')]")
            )
        )
        file_input.send_keys(str(video_file.resolve()))
        log(f"[{self.config.title}] Видео отправлено в загрузку: {video_file}")

        # Ожидаем обработки видео
        self._wait_video_processing(wait)

        # Заполняем описание и теги
        self._fill_metadata(driver, wait, title, description, tags)

        # Получаем ссылку на видео после публикации
        video_url = self._get_video_url(wait)

        log(f"[{self.config.title}] Видео успешно загружено: {video_url}", level="success")

        return {
            "success": True,
            "platform": self.config.title,
            "video_path": str(video_file),
            "video_url": video_url,
            "message": "Видео успешно загружено!"
        }

    # ================================================================
    # Авторизация через клик по кнопке, ожидание завершения
    # ================================================================
    def _handle_login_if_needed(self, driver, wait):
        login_buttons_selectors = [
            "//button[contains(text(),'Войти')]",
            "//button[contains(@class,'quick_login_button')]",
            "//button[contains(@class,'quick_reg_button')]"
        ]

        for selector in login_buttons_selectors:
            try:
                btn = driver.find_element(By.XPATH, selector)
                if btn.is_displayed():
                    log(f"[{self.config.title}] Кликнули по кнопке входа/регистрации")
                    btn.click()
                    self._wait_for_login_by_url(driver)
                    break
            except Exception:
                continue

    def _wait_for_login_by_url(self, driver, timeout: int = 600):
        start_url = driver.current_url
        log(f"[{self.config.title}] Ожидание начала авторизации по URL...")

        # Ждём, пока URL изменится (начало авторизации)
        WebDriverWait(driver, timeout).until(lambda d: d.current_url != start_url)
        log(f"[{self.config.title}] Авторизация началась. Текущий URL: {driver.current_url}")

        # Ждём, пока URL вернётся на исходный (авторизация завершена)
        WebDriverWait(driver, timeout).until(lambda d: d.current_url == start_url)
        log(f"[{self.config.title}] Авторизация завершена. Текущий URL: {driver.current_url}")
        time.sleep(1)  # небольшая пауза для полной загрузки страницы

    # ================================================================
    # Вспомогательные методы
    # ================================================================
    def _validate_video(self, video_file: str | Path) -> Path:
        video_file = Path(video_file)
        if not video_file.exists():
            msg = f"Видео не найдено: {video_file}"
            log(f"[{self.config.title}] {msg}", level="error")
            raise FileNotFoundError(msg)
        return video_file

    def _validate_thumbnail(self, thumbnail):
        if not thumbnail:
            return None
        thumbnail = Path(thumbnail)
        if not thumbnail.exists():
            log(f"[{self.config.title}] Миниатюра не найдена: {thumbnail}", level="warning")
            return None
        return thumbnail

    def _wait_video_processing(self, wait):
        log(f"[{self.config.title}] Ожидание обработки видео…")
        time.sleep(5)  # базовая пауза

    def _fill_metadata(self, driver, wait, title: str, description: str, tags: list[str] | None):
        if title or description:
            log(f"[{self.config.title}] Заполняем метаданные (title/description) — пока заглушка")

    def _get_video_url(self, wait) -> str | None:
        try:
            link_el = wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'vk.com/video')]"))
            )
            video_url = link_el.get_attribute("href")
            log(f"[{self.config.title}] Ссылка на видео: {video_url}")
            return video_url
        except Exception:
            log(f"[{self.config.title}] Не удалось получить ссылку на видео", level="warning")
            return None
