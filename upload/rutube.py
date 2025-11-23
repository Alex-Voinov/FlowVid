from pathlib import Path
from .base_uploader import BaseUploader
from config.networks import NetworkConfig
from utils.logger import log
from core.selenium_manager import SeleniumManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class Uploader(BaseUploader):

    def __init__(self, config: NetworkConfig):
        self.config = config
        profile_path = None
        if config.platform_settings:
            profile_path = config.platform_settings.get("profile_path")
        super().__init__(profile_path)
        log(f"[{self.config.title}] Инициализация завершена", level="info")

    # ================================================================
    # Проверка авторизации (пока заглушка)
    # ================================================================
    def check_login(self) -> bool:
        log(f"[{self.config.title}] Проверка логина (заглушка) — OK", level="info")
        return True

    # ================================================================
    # Основная точка входа
    # ================================================================
    def upload(
        self,
        video_file: str | Path,
        title: str,
        description: str,
        tags: list[str] | None = None,
        thumbnail: str | Path | None = None,
        profile_name: str = "default",
    ):
        video_file = self._validate_video(video_file)
        thumbnail = self._validate_thumbnail(thumbnail)

        driver = SeleniumManager.instance().start(profile_name=profile_name, headless=False)
        wait = WebDriverWait(driver, 20)
        driver.get("https://studio.rutube.ru/uploader/")

        # Загрузка видео
        self._upload_file(driver, wait, video_file)
        self._wait_processing(wait)

        # Заполняем метаданные
        self._fill_metadata(driver, wait, title, description, tags)

        # Загружаем обложку
        if thumbnail:
            self._upload_thumbnail(driver, wait, thumbnail)

        # Получаем ссылку на видео
        video_url = self._get_video_url(wait)

        result = {
            "success": True,
            "platform": self.config.title,
            "video_path": str(video_file),
            "video_url": video_url,
            "message": "Видео успешно загружено!",
        }
        log(f"[{self.config.title}] Завершено. Ссылка: {video_url}", level="success")
        return result

    # ================================================================
    # Проверка входных данных
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

    # ================================================================
    # Загрузка файла
    # ================================================================
    def _upload_file(self, driver, wait, video_file: Path):
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        file_input.send_keys(str(video_file.resolve()))
        log(f"[{self.config.title}] Файл отправлен в загрузку: {video_file}")

    # ================================================================
    # Загрузка обложки
    # ================================================================
    def _upload_thumbnail(self, driver, wait, thumbnail: Path):
        log(f"[{self.config.title}] Загружаем обложку: {thumbnail}")

        upload_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'cover-uploader-module__container')]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", upload_btn)
        upload_btn.click()

        file_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file' and contains(@accept, 'image')]")
            )
        )
        file_input.send_keys(str(thumbnail.resolve()))
        log(f"[{self.config.title}] Обложка загружена")

    # ================================================================
    # Ожидание обработки видео
    # ================================================================
    def _wait_processing(self, wait):
        log(f"[{self.config.title}] Ожидание обработки видео…")
        wait.until(EC.presence_of_element_located((By.NAME, "title")))
        wait.until(EC.presence_of_element_located((By.NAME, "description")))
        log(f"[{self.config.title}] Поля редактирования готовы")

    # ================================================================
    # Заполнение метаданных
    # ================================================================
    def _fill_metadata(self, driver, wait, title: str, description: str, tags: list[str] | None):
        title_input = wait.until(EC.presence_of_element_located((By.NAME, "title")))
        desc_input = wait.until(EC.presence_of_element_located((By.NAME, "description")))

        # Очистка и заполнение заголовка
        driver.execute_script("arguments[0].value='';", title_input)
        title_input.clear()
        title_input.send_keys(title)
        log(f"[{self.config.title}] Заголовок установлен")

        # Очистка и заполнение описания
        driver.execute_script("arguments[0].value='';", desc_input)
        desc_input.clear()
        desc_input.send_keys(self._build_description(description, tags))
        log(f"[{self.config.title}] Описание установлено")

        # Уходим с поля, чтобы Rutube сохранил изменения
        desc_input.send_keys(Keys.TAB)

    def _build_description(self, description: str, tags: list[str] | None) -> str:
        if tags:
            return f"{description}\n\n" + " ".join(f"#{t}" for t in tags)
        return description

    # ================================================================
    # Получение ссылки на видео
    # ================================================================
    def _get_video_url(self, wait) -> str | None:
        try:
            link_el = wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'rutube.ru/video')]"))
            )
            return link_el.get_attribute("href")
        except Exception:
            log(f"[{self.config.title}] Не удалось получить ссылку на видео", level="warning")
            return None
