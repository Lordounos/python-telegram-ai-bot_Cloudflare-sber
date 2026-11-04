
# Python Telegram AI Bot

## Инструкции по установке

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Lordounos/python-telegram-ai-bot_Cloudflare.git
cd python-telegram-ai-bot_Cloudflare
```

Или скачайте и распакуйте архив, откройте папку в VS Code.

### 2. Создайте виртуальное окружение

```bash
python -m venv venv
```

Активация:
- **Windows:**
  ```powershell
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Установите зависимости

В VS Code можно поставить галочку на `requirements.txt` при создании окружения.  
Или через терминал:

```bash
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

Создайте файл `.env` в корне проекта:

```dotenv
# Telegram
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# YandexGPT
YA_API_KEY=ваш_яндекс_api_key
YA_FOLDER_ID=ваш_каталог_яндекс_консоли

# Cloudflare Worker (для обхода блокировки api.telegram.org)
WORKER_URL=https://tg-proxy.ваш-домен.workers.dev
```

Где взять значения:

| Переменная | Где получить |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` или `/mybots` → API Token |
| `YA_API_KEY` | [Yandex Cloud Console](https://console.cloud.yandex.ru/) → сервисный аккаунт → API-ключ |
| `YA_FOLDER_ID` | Yandex Cloud Console → каталог (folder ID) |
| `WORKER_URL` | Адрес вашего Cloudflare Worker (см. раздел «Cloudflare Worker») |

### 5. Запустите бота

```bash
python bot.py
```

В логах должно появиться:
```
INFO - __main__ - Using Cloudflare Worker base URL: https://tg-proxy.ваш-домен.workers.dev
```

Напишите боту `/start` в Telegram — он должен ответить.

---

## Cloudflare Worker: обход блокировки Telegram

В РФ `api.telegram.org` часто недоступен напрямую. Worker работает как прокси:

```
Ваш бот (локальный ПК) → Cloudflare Worker → api.telegram.org
```

### Создание Worker

1. Войдите в [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create Worker**.
2. Назовите его (например, `tg-proxy`), нажмите **Deploy**.
3. Нажмите **Edit code**, удалите всё и вставьте:

```javascript
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = new URL(`https://api.telegram.org${url.pathname}${url.search}`);
    const res = await fetch(target, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
    return res;
  },
};
```

4. **Save and Deploy**.

### Проверка Worker

```powershell
curl.exe "https://tg-proxy.ваш-домен.workers.dev/bot<ТОКЕН>/getMe"
```

Должен вернуться JSON с `"ok":true`.

---

## Что даёт Cloudflare помимо обхода блокировки

- **Изоляция кода** — Worker выполняется в sandbox без доступа к файловой системе и внутренней сети.
- **Автоматический TLS** — Cloudflare управляет сертификатами, вы не думаете о них.
- **Базовая защита от DDoS** — бесплатно и без настройки.
- **Ограничение исходящих запросов** — защита от SSRF-атак.
- **Бесплатный тариф** — 100 000 запросов в день, чего для учебного бота более чем достаточно.

**Ограничения:** Cloudflare видит трафик в памяти (не пишет на диск), Spectre-риски теоретически существуют, но для учебного проекта не критичны.

---

## Структура проекта

```
├── bot.py                  # Точка входа, обработчики Telegram
├── model.py                # LLM-сервис (YandexGPT)
├── prompts/
│   └── prompt_1.txt        # Системный промпт
├── logs/
│   └── bot.log             # Логи (создаются автоматически)
├── requirements.txt
├── .env                    # Ваши ключи (не коммитить!)
└── README.md
```

---

## Возможные проблемы

### `Тишина после запуска` / таймауты `getMe`

Убедитесь, что:
1. В `WORKER_URL` нет опечаток (`.dev`, а не `.de`).
2. В `bot.py` настроены таймауты:

```python
from telegram.request import HTTPXRequest

request = HTTPXRequest(
    connection_pool_size=8,
    connect_timeout=15.0,
    read_timeout=30.0,
    write_timeout=30.0,
    pool_timeout=10.0,
)
```

### `401 Unauthorized`

Токен отозван или неверный. Сделайте `/revoke` в @BotFather и замените `TELEGRAM_BOT_TOKEN`.

### `Ошибка YandexGPT: ...`

Проверьте `YA_API_KEY` и `YA_FOLDER_ID`. Убедитесь, что у сервисного аккаунта есть роль `ai.languageModels.user`.

### `AsyncLibraryNotFoundError`

Возникает при остановке бота — не критично, связано с завершением event loop. Игнорируйте.

---

## Безопасность

- **Не коммитьте `.env`** — добавьте его в `.gitignore`.
- **Не публикуйте токен бота** в чатах и скриншотах. Если засветился — `/revoke` в @BotFather.

---

о.
