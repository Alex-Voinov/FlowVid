from pathlib import Path
from time import sleep, time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base_uploader import BaseUploader
from utils.logger import log
from core.selenium_manager import SeleniumManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException


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

        # 3. Кнопка "Добавить", вызывает выпадающий список
        self._click_add_button(driver, wait)

        # 4. Кнопка "загрузить" в выпадающем списке
        self._click_upload_video_menu_item(driver, wait)

        # 5. Загрузка файла
        self._upload_video_file(driver, wait, video_file)

        # 6. Если есть кнопка "Понятно" (всегда для shrots?) нажимает ее
        self._click_ok_if_present(driver, wait)

        # 7. Определяем является ли видео shorts
        self.is_shorts = self._is_shorts(driver, title, wait)

        # 8. Заполняет описание + теги
        self._fill_description(driver, description, tags)

        self._fetch_uploaded_video_link(wait)

        if self.is_shorts:
            log("Видео является Shorts")
        else:
            log("Видео обычное")
            self._attach_thumbnail(driver, wait, thumbnail)
            self._set_publication_and_switch(wait)

        self._wait_and_publish(driver, wait, poll_interval=2, timeout=300)


        log(f"[{self.config.title}] Видео успешно загружено: {self.video_link}", level="success")

        return {
            "success": True,
            "platform": self.config.title,
            "video_path": str(video_file),
            "video_url": self.video_link,
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

    def _is_shorts(self, driver, title: str, wait=None, ) -> bool:
        """
        Проверяет, является ли загруженное видео Shorts.

        Логика:
        - Если на странице присутствует <input> с атрибутом 
        `data-testid="video-edit-title"` — это обычное видео.
        - Если такого элемента нет — это Shorts.

        Args:
            driver: Selenium WebDriver
            wait: WebDriverWait (опционально)

        Returns:
            True  — видео Shorts
            False — обычное видео
        """
        selector = 'input[data-testid="video-edit-title"]'
        try:
            elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))) if wait else driver.find_element(By.CSS_SELECTOR, selector)
            # Элемент найден — обычное видео
            if title:
                elem.clear()
                elem.send_keys(title)
            return False
        except (NoSuchElementException, TimeoutException):
            return True



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
        """
        Кликает кнопку 'Добавить' в группе VK.
        
        Сначала пробует CSS-селектор из конфигурации, затем запасной XPath.
        Логирование выполнения действия.
        """
        # Сначала пробуем CSS
        css_selector = self.ps.get("btn_add_css")
        xpath_selector = self.ps.get("btn_add_xpath")

        btn = None
        if css_selector:
            try:
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            except Exception:
                log(f"[{self.config.title}] Кнопка 'Добавить' по CSS не найдена, пробуем XPath", level="warning")

        # Если CSS не сработал, используем XPath
        if not btn and xpath_selector:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))

        if btn:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            btn.click()
            log(f"[{self.config.title}] Нажали кнопку 'Добавить'")
        else:
            log(f"[{self.config.title}] Не удалось найти кнопку 'Добавить'", level="error")
            raise RuntimeError("Кнопка 'Добавить' не найдена на странице")


    def _click_upload_video_menu_item(self, driver, wait):
        """
        Кликает по элементу 'Загрузить видео' в меню действий группы.

        Используется после открытия меню через кнопку 'Добавить'.
        Селектор ориентирован на класс и текст внутри.
        """
        xpath = (
            "//div[contains(@class,'ui_actions_menu_item') "
            "and contains(normalize-space(.),'Загрузить видео')]"
        )

        try:
            menu_item = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", menu_item)
            menu_item.click()
            log(f"[{self.config.title}] Нажали 'Загрузить видео' в меню")
        except Exception as e:
            log(f"[{self.config.title}] Не удалось найти или кликнуть 'Загрузить видео': {e}", level="error")
            raise RuntimeError("Не удалось кликнуть 'Загрузить видео'")



    def _upload_video_file(self, driver, wait, video_file):
        xpath = self.ps["file_input_xpath"]
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_input)
        file_input.send_keys(str(video_file.resolve()))
        log(f"[{self.config.title}] Видео отправлено: {video_file}")

    # ================================================================
    # ОБРАБОТКА И МЕТА
    # ================================================================
    def _wait_and_publish(self, driver, wait, poll_interval=2, timeout=300):
        """
        Пытается нажать 'Опубликовать' каждые `poll_interval` секунд
        до тех пор, пока:
        1. URL изменится (публикация завершена) или
        2. Появится элемент с текстом "Видео обработано и загружено"
        """
        start_url = driver.current_url
        start_time = time()
        success_text = "Видео обработано и загружено"

        while True:
            try:
                self._click_publish(wait)
            except Exception as e:
                log(f"[{self.config.title}] Попытка публикации не удалась: {e}", level="warning")

            # Проверяем изменение URL
            current_url = driver.current_url
            if current_url != start_url:
                log(f"[{self.config.title}] Видео опубликовано, URL изменился → {current_url}")
                break

            # Проверяем наличие текста на странице
            if success_text.lower() in driver.page_source.lower():
                log(f"[{self.config.title}] Видео обработано и загружено — публикация завершена")
                break

            # Тайм-аут
            if time() - start_time > timeout:
                log(f"[{self.config.title}] Видео не опубликовалось вовремя", level="error")
                break

            sleep(poll_interval)


    def _click_ok_if_present(self, driver, wait=None):
        """
        Если на странице есть кнопка с текстом "Понятно", нажимает её и логирует.
        """
        xpath = "//span[normalize-space(text())='Понятно']/ancestor::button"
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath))) if wait else driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            btn.click()
            log(f"[{self.config.title}] Кликнули по кнопке 'Понятно'")
        except (TimeoutException, NoSuchElementException):
            log(f"[{self.config.title}] Кнопка 'Понятно' отсутствует — продолжаем", level="info")



    def _fill_description(self, driver, description: str = "", tags: list[str] | None = None):
        """
        Заполняет поле описания видео/клипа.
        - Определяет правильный <textarea> по self.is_shorts:
            * shorts → data-testid="clips-upload-description"
            * обычное видео → data-testid="video-edit-description"
        - Добавляет теги через #, если переданы.
        - Логирует действие.
        """
        if not description and not tags:
            return  # ничего заполнять не нужно

        # Определяем data-testid
        testid = "clips-upload-description" if getattr(self, "is_shorts", False) else "video-edit-description"
        
        try:
            textarea = driver.find_element(By.CSS_SELECTOR, f"textarea[data-testid='{testid}']")
            text_value = description or ""
            if tags:
                text_value += "\n" + " ".join(f"#{tag}" for tag in tags)
            
            textarea.clear()
            textarea.send_keys(text_value)
            log(f"[{self.config.title}] Описание заполнено")
        except (NoSuchElementException, TimeoutException) as e:
            log(f"[{self.config.title}] Не удалось найти поле описания (data-testid='{testid}'): {e}", level="warning")


    def _click_publish(self, wait):
        """
        Кликает кнопку 'Опубликовать'.
        Объединяет логику для обычного видео и шортсов.
        """
        try:
            xpath = (
                "//span[contains(@class,'vkuiButton__content') and text()='Опубликовать']"
                if self.is_shorts else
                "//button[@data-testid='video_upload_end_editing']//span[text()='Опубликовать']"
            )
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            btn.click()
            log(f"[{self.config.title}] Кликнули кнопку 'Опубликовать'")
        except (TimeoutException, NoSuchElementException) as e:
            log(f"[{self.config.title}] Кнопка 'Опубликовать' не найдена: {e}", level="warning")


    def _fetch_uploaded_video_link(self, wait):
        """
        Находит ссылку на загруженное видео или шорт и сохраняет в self.video_link.
        Ориентируется на self.is_shorts.
        """
        try:
            if self.is_shorts:
                selector = "a[data-testid='clips-upload-clip-link']"
            else:
                selector = "a[data-testid='video_upload_page_copy_video_link']"

            link_el = wait.until(
                lambda d: d.find_element(By.CSS_SELECTOR, selector)
            )
            self.video_link = link_el.get_attribute("href")
            log(f"[{self.config.title}] Ссылка на видео сохранена: {self.video_link}")
        except Exception:
            self.video_link = None
            log(f"[{self.config.title}] Не удалось найти ссылку на видео", level="warning")

    def _wait_for_thumbnail_uploaded(self, driver, timeout=20, poll_interval=0.5) -> bool:
        """
        Ожидает, пока миниатюра успешно загрузится.

        Args:
            driver: Selenium WebDriver
            timeout: максимальное время ожидания (сек)
            poll_interval: интервал между проверками (сек)

        Returns:
            True — миниатюра загружена
            False — тайм-аут
        """
        start_time = time()
        while True:
            try:
                selected_icon = driver.find_element(By.CSS_SELECTOR, "[data-testid='media-attach-selected-icon']")
                if selected_icon.is_displayed():
                    log(f"[{self.config.title}] Обложка успешно загружена и готова к выбору")
                    return True
            except NoSuchElementException:
                pass

            if time() - start_time > timeout:
                log(f"[{self.config.title}] Обложка не загрузилась за {timeout} секунд", level="warning")
                return False

            sleep(poll_interval)



    def _attach_thumbnail(self, driver, wait, thumbnail: str | Path):
        """
        Отправляет файл миниатюры и ждёт, пока она будет успешно загружена.

        Args:
            driver: Selenium WebDriver
            wait: WebDriverWait
            thumbnail: путь к изображению
        """
        if not thumbnail:
            return

        thumbnail_path = Path(thumbnail).resolve()
        if not thumbnail_path.exists():
            log(f"[{self.config.title}] Миниатюра не найдена: {thumbnail_path}", level="warning")
            return

        try:
            # Находим input для загрузки и отправляем файл
            file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", file_input)
            file_input.send_keys(str(thumbnail_path))
            log(f"[{self.config.title}] Файл миниатюры отправлен: {thumbnail_path}")

            # --- Проверяем статус загрузки ---
            self._wait_for_thumbnail_uploaded(driver)

        except Exception as e:
            log(f"[{self.config.title}] Не удалось загрузить миниатюру: {e}", level="warning")


    def _set_publication_and_switch(self, wait):
        """
        1. Кликает по табу "Публикация" в разделе публикации видео.
        2. Включает/выключает переключатель (switch) рядом.
        """
        try:
            # --- 1. Таб "Публикация"
            publication_label = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//label[input[@data-testid='video_upload_publication_tab'] or span[text()='Публикация']]"
                ))
            )
            publication_label.click()
            log(f"[{self.config.title}] Кликнули по табу 'Публикация'")
        except Exception as e:
            log(f"[{self.config.title}] Не удалось найти/кликнуть по табу 'Публикация': {e}", level="warning")

        try:
            # --- 2. Переключатель (switch)
            switch_label = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//label[input[@type='checkbox'] and contains(@class,'vkuiSwitch__host')]"
                ))
            )
            switch_label.click()
            log(f"[{self.config.title}] Кликнули по переключателю (switch)")
        except Exception as e:
            log(f"[{self.config.title}] Не удалось найти/кликнуть по переключателю: {e}", level="warning")


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
            return None
        return thumbnail
