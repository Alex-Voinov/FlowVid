# FlowVid Uploader

Простой инструмент для загрузки видео на разные платформы:

- YouTube (Shorts и обычные видео)
- Telegram (каналы)
- (в будущем — TikTok, Instagram, VK и другие)

Приложение имеет **GUI на PyQt6**, где можно выбрать видео, добавить заголовок, описание, теги и миниатюру.

---

## Установка

1. Клонируйте репозиторий:

```
git clone <repo_url>
cd FlowVid
```

2. Создайте виртуальное окружение и активируйте его:

```
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

3. Установите зависимости:

```
pip install -r requirements.txt
```

4. Создайте файл `.env` в корне проекта. Пример содержимого:

```
# Telegram
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_CHANNEL=@your_channel_username

# YouTube
YT_CLIENT_SECRET=client_secret.json
```

---

## Telegram

### Регистрация приложения

1. Перейдите на [my.telegram.org](https://my.telegram.org) → API development tools.
2. Создайте новое приложение (App title, Short name, Platform, Description).
3. Получите `api_id` и `api_hash` и вставьте их в `.env`.
4. Укажите в `.env` ваш **публичный канал** (например `@mychannel`).

### Авторизация

- При первом запуске скрипт попросит **номер телефона** и **код из Telegram**.
- После успешного входа создается файл `telegram_session.session` (его **не нужно коммитить**, добавьте в `.gitignore`).
- В дальнейшем вход будет происходить автоматически.

---

## YouTube

### Создание проекта и OAuth

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Создайте новый проект → включите **YouTube Data API v3**.
3. Создайте **OAuth 2.0 Client ID** для Desktop.
4. Скачайте JSON-файл с client secrets и положите его в корень проекта.
   - В `.env` пропишите путь к нему:

```
YT_CLIENT_SECRET=client_secret.json
```

5. При первом запуске скрипт откроет браузер для авторизации Google или выдаст ссылку для консоли.
   - После успешной авторизации токен сохранится в `token_youtube.pickle`.

**Важно:** пока приложение не прошло проверку Google, YouTube API доступен **только для тестовых пользователей**, которых нужно добавить в OAuth consent screen → Test users.

---

## Использование

1. Запустите GUI:

```
python gui.py
```

2. В окне приложения:
- Выберите видео (MP4)
- Отметьте платформы для загрузки (Telegram, YouTube)
- Добавьте заголовок, описание, теги
- Выберите миниатюру
- Нажмите **Загрузить**

3. В терминале будут выводиться прогресс и ссылки на загруженные видео.

---

## Примечания

- Файлы `.session` и `token_youtube.pickle` **не коммитить**, они для личного доступа.
- Для Telegram используется обычный аккаунт, **не бот**.
- Для YouTube API загрузка возможна только с тестового аккаунта до проверки приложения.

---

## Лицензия

[CC0 1.0 Universal (Public Domain)](LICENSE)
