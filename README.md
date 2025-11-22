# FlowVid Uploader

Универсальный инструмент для загрузки видео на разные платформы через GUI или скрипт.

Поддерживаемые платформы:
- YouTube (Shorts и обычные видео)
- Telegram (каналы)
- Rutube Reels
- В будущем: TikTok, Instagram, VK и другие

Приложение использует **PyQt6** для GUI и **Selenium** для платформ, где требуется автоматизация браузера.

---

## Установка

1. Клонируйте репозиторий:
    
    git clone your-repo-url
    cd FlowVid

2. Создайте и активируйте виртуальное окружение:

    **Windows**
    
    python -m venv .venv
    .venv\Scripts\activate

    **Linux/macOS**
    
    python -m venv .venv
    source .venv/bin/activate

3. Установите зависимости:

    pip install -r requirements.txt

4. Создайте файл `.env` в корне проекта с ключами и параметрами платформ:

    # Telegram
    TG_API_ID=your_api_id
    TG_API_HASH=your_api_hash
    TG_CHANNEL=@your_channel_username

    # YouTube
    YT_CLIENT_SECRET=client_secret.json

> Убедитесь, что пути к ключам и секретам указаны корректно.

---

## Платформы

### Telegram
1. Перейдите на [my.telegram.org](https://my.telegram.org) → API development tools.
2. Создайте приложение и получите `api_id` и `api_hash`.
3. В `.env` укажите ваш публичный канал, например: `@mychannel`.
4. При первом запуске авторизация будет через номер телефона и код.
5. Создается сессия `telegram_session.session`, её **не коммитить**.

### YouTube
1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Включите **YouTube Data API v3**.
3. Создайте **OAuth 2.0 Client ID** для Desktop.
4. Скачайте JSON с client secrets и укажите путь в `.env`:

    YT_CLIENT_SECRET=client_secret.json

5. При первом запуске откроется браузер для авторизации. Токен сохранится в `token_youtube.pickle`.

> Пока приложение не прошло проверку Google, API доступен только для тестовых пользователей.

### Rutube Reels
- Для работы нужен Selenium и профиль браузера.
- Добавляйте загрузчик как функцию `upload` в `upload/rutube.py`.
- В конфиге `NETWORKS` добавляйте соответствующий `NetworkConfig`.

---

## Использование

1. Запускать **главный скрипт**:

    python main.py

2. В GUI:
- Выберите видео (MP4)
- Отметьте платформы для загрузки
- Добавьте заголовок, описание, теги
- Выберите миниатюру
- Нажмите **Загрузить**

3. В терминале будут выводиться прогресс и ссылки на загруженные видео.

---

## Добавление новой платформы

1. Создайте функцию `upload` в `upload/<key>.py`.
2. Добавьте запись в `config/networks.py`:

    NetworkConfig(
        key="newkey",
        title="New Platform",
        uses_selenium=True/False,
        enabled=True
    )

3. Менеджер `UploaderManager` сможет использовать новый загрузчик без изменений в коде.

---

## Примечания

- Файлы `.session` и `token_youtube.pickle` **не коммитить**.
- Telegram работает через обычный аккаунт, **не бот**.
- YouTube API доступен только тестовым пользователям до проверки приложения.
- Rutube Reels требует Selenium для автоматизации браузера.
- Все новые платформы подключаются через `upload/<key>.py` и конфиг `NETWORKS`.

---

## Лицензия

[CC0 1.0 Universal (Public Domain)](LICENSE)
