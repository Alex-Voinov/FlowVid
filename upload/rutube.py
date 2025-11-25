from pathlib import Path
from .base_uploader import BaseUploader
from config.networks import NetworkConfig
from utils.logger import log
from core.selenium_manager import SeleniumManager
import pyautogui
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class Uploader(BaseUploader):

    def __init__(self, config: NetworkConfig):
        self.config = config
        # platform_settings может быть None
        self.settings = config.platform_settings or {}

        # профиль (как было)
        profile_path = self.settings.get("profile_path")

        # читаем параметры из настроек с дефолтами
        self.upload_url = self.settings.get("upload_url", "https://studio.rutube.ru/uploader/")
        self.editor_url = self.settings.get("editor_url", "https://studio.rutube.ru/video/")
        self.base_video_url = self.settings.get("base_video_url", "https://rutube.ru/video/")

        self.wait_timeout = self.settings.get("wait_timeout", 20)
        self.post_ready_delay = self.settings.get("post_ready_delay", 1.0)
        self.post_publish_delay = self.settings.get("post_publish_delay", 1.0)
        self.dialog_open_delay = self.settings.get("dialog_open_delay", 1.0)

        self.default_category = self.settings.get("default_category", "Дизайн")
        self.scroll_into_view = self.settings.get("scroll_into_view", True)

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
        wait = WebDriverWait(driver, self.wait_timeout)
        driver.get(self.upload_url)

        # Загрузка видео
        self._upload_file(driver, wait, video_file)
        self._wait_processing(wait)

        # Заполняем метаданные
        self._fill_metadata(driver, wait, title, description, tags)
    
        # Выбираем категорию
        self._select_category(driver, wait, category=self.default_category) 

        # Загружаем обложку
        if thumbnail:
            self._upload_thumbnail(driver, wait, thumbnail)
            self._click_ready_button(driver, wait)

        # Получаем ссылку на видео
        video_url = self._wait_video_ready_and_publish(driver, wait)

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
    # Выбор категории из выпадающего списка
    # ================================================================
    def _select_category(self, driver, wait, category: str):
        log(f"[{self.config.title}] Выбираем категорию: {category}")

        # 1. Открываем селект (combobox)
        combobox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='combobox']"))
        )
        if self.scroll_into_view:
            driver.execute_script("arguments[0].scrollIntoView(true);", combobox)
        combobox.click()

        # 2. Ждём появления списка опций
        options = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='option']"))
        )

        # 3. Ищем нужный текст
        found = False
        for opt in options:
            if category.lower() in opt.text.lower():
                opt.click()
                log(f"[{self.config.title}] Категория выбрана: {opt.text}")
                found = True
                break

        if not found:
            log(f"[{self.config.title}] Категория '{category}' не найдена", level="warning")

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

    def _wait_video_ready_and_publish(self, driver, wait):
        log(f"[{self.config.title}] Ждём появления ссылки на видео...")

        # Ждём ссылку вида rutube.ru/video/...
        link_el = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href,'rutube.ru/video')]")
            )
        )
        video_url = link_el.get_attribute("href")
        log(f"[{self.config.title}] Ссылка появилась: {video_url}")

        # Доп. пауза — Rutube долго дохерачит внутренние процессы
        time.sleep(self.post_ready_delay)

        # Жмём "Опубликовать"
        self._click_publish(driver, wait)

        # Даём загрузке обработать команду
        time.sleep(self.post_publish_delay)

        return video_url

    def _click_publish(self, driver, wait):
        """
        Кликает по кнопке 'Опубликовать'
        """
        log(f"[{self.config.title}] Нажимаем кнопку 'Опубликовать'")

        # Ждём появления кнопки
        publish_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[text()='Опубликовать']]"
            ))
        )

        if self.scroll_into_view:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", publish_btn)
        # Кликаем (через JS, как было)
        driver.execute_script("arguments[0].click();", publish_btn)

    def _validate_thumbnail(self, thumbnail):
        if not thumbnail:
            return None
        thumbnail = Path(thumbnail)
        if not thumbnail.exists():
            log(f"[{self.config.title}] Миниатюра не найдена: {thumbnail}", level="warning")
            return None
        return thumbnail

    def _click_ready_button(self, driver, wait):
        """
        Жмёт кнопку 'Готово' после выбора изображения.
        """
        # Ждём, пока кнопка станет кликабельной
        btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[contains(text(),'Готово')]]")
            )
        )

        if self.scroll_into_view:
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)

        # Жмём
        btn.click()

        log(f"[{self.config.title}] Нажали кнопку 'Готово'")

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
        if self.scroll_into_view:
            driver.execute_script("arguments[0].scrollIntoView(true);", upload_btn)
        upload_btn.click()

        # Ждём открытия диалога выбора файла
        time.sleep(self.dialog_open_delay)  # Можно увеличить, если диалог открывается медленно

        # Вводим путь к файлу и нажимаем Enter
        pyautogui.write(str(thumbnail.resolve()))
        pyautogui.press("enter")

        log(f"[{self.config.title}] Файл {thumbnail} отправлен в диалог загрузки")
       

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
