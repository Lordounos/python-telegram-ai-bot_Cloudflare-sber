# Python Telegram AI Bot (GigaChat + Cloudflare)

Telegram-бот с AI-ответами на базе **GigaChat от Сбера**. Работает через **Cloudflare Worker**, что позволяет обходить блокировку `api.telegram.org` в РФ. В качестве альтернативы поддерживается локальная **Ollama**.

## Возможности

- Ответы на текстовые сообщения через GigaChat API (Сбер).
- Обход блокировки Telegram через Cloudflare Worker.
- Опциональная поддержка SOCKS5/HTTP-прокси.
- Переключение между GigaChat и локальной Ollama одной строкой в `model.py`.
- Логирование в файл с ротацией (`logs/bot.log`).

---

## Установка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Lordounos/python-telegram-ai-bot_Cloudflare-sber.git
cd python-telegram-ai-bot_Cloudflare-sber

2. Создайте виртуальное окружение
bash

python -m venv venv

Активация:

    Windows:
    powershell

    venv\Scripts\activate

    macOS/Linux:
    bash

    source venv/bin/activate

3. Установите зависимости
bash

pip install -r requirements.txt

4. Настройте переменные окружения

Создайте файл .env в корне проекта:
dotenv

# Telegram
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# Cloudflare Worker (для обхода блокировки api.telegram.org)
WORKER_URL=https://tg-proxy.ваш-домен.workers.dev

# GigaChat (Сбер)
GIGACHAT_CREDENTIALS=ваш_ключ_авторизации_из_Studio
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_CA_BUNDLE_FILE=russian_trusted_root_ca.pem

Переменная	Где получить
TELEGRAM_BOT_TOKEN	@BotFather → /newbot или /mybots → API Token
WORKER_URL	Адрес вашего Cloudflare Worker (см. раздел «Cloudflare Worker»)
GIGACHAT_CREDENTIALS	GigaChat Studio → проект GigaChat API → Настройки API → Получить ключ
GIGACHAT_SCOPE	GIGACHAT_API_PERS для физлиц; GIGACHAT_API_B2B / GIGACHAT_API_CORP для юрлиц
GIGACHAT_CA_BUNDLE_FILE	Путь к файлу russian_trusted_root_ca.pem (скачать с портала Госуслуг или из документации Сбера)
5. Положите сертификат Минцифры

GigaChat API использует цепочку сертификатов Минцифры, которой нет в стандартном наборе Python. Скачайте файл russian_trusted_root_ca.pem и положите его в корень проекта рядом с bot.py.

Если файл называется иначе — поправьте GIGACHAT_CA_BUNDLE_FILE в .env. Не отключайте verify_ssl_certs — передача ca_bundle_file безопаснее и рекомендована Сбером.
6. Запустите бота
bash

python bot.py

В логах должно появиться:
text

INFO - __main__ - Using Cloudflare Worker base URL: https://tg-proxy.ваш-домен.workers.dev

Напишите боту /start в Telegram — он должен ответить.
Выбор LLM-сервиса

В model.py внизу есть две строки инициализации:
python

llm_1 = GigaChatService("prompts/prompt_1.txt")
# llm_1 = OllamaService("prompts/prompt_1.txt")

Раскомментируйте нужную, чтобы переключиться между облачным GigaChat и локальной Ollama. bot.py при этом менять не нужно — он вызывает chat_with_llm, которая работает с любым сервисом, реализующим метод chat(message, history).
Cloudflare Worker: обход блокировки Telegram

В РФ api.telegram.org часто недоступен напрямую. Worker работает как прокси:
text

Ваш бот (локальный ПК) → Cloudflare Worker → api.telegram.org

Создание Worker

    Войдите в Cloudflare Dashboard → Workers & Pages → Create Worker.

    Назовите его (например, tg-proxy), нажмите Deploy.

    Нажмите Edit code, удалите всё и вставьте:

javascript

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

    Save and Deploy.

Проверка Worker
powershell

curl.exe "https://tg-proxy.ваш-домен.workers.dev/bot<ТОКЕН>/getMe"

Должен вернуться JSON с "ok":true.
Структура проекта
text

├── bot.py                       # Точка входа, обработчики Telegram
├── model.py                     # LLM-сервисы (GigaChat, Ollama)
├── prompts/
│   └── prompt_1.txt             # Системный промпт
├── logs/
│   └── bot.log                  # Логи (создаются автоматически)
├── russian_trusted_root_ca.pem  # Сертификат Минцифры для GigaChat
├── requirements.txt
├── .env                         # Ваши ключи (не коммитить!)
└── README.md

Возможные проблемы
Тишина после запуска / таймауты getMe

Убедитесь, что:

    В WORKER_URL нет опечаток (.dev, а не .de).

    В bot.py настроены таймауты:

python

from telegram.request import HTTPXRequest

request = HTTPXRequest(
    connection_pool_size=8,
    connect_timeout=15.0,
    read_timeout=30.0,
    write_timeout=30.0,
    pool_timeout=10.0,
)

401 Unauthorized (Telegram)

Токен отозван или неверный. Сделайте /revoke в @BotFather и замените TELEGRAM_BOT_TOKEN.
CERTIFICATE_VERIFY_FAILED (GigaChat)

Не найден или неверно указан файл russian_trusted_root_ca.pem. Проверьте:

    Файл существует по пути из GIGACHAT_CA_BUNDLE_FILE.

    Файл в формате PEM (начинается с -----BEGIN CERTIFICATE-----).

    Путь относительный (от корня проекта) или абсолютный.

Ошибка GigaChat: ...

Проверьте GIGACHAT_CREDENTIALS и GIGACHAT_SCOPE. Убедитесь, что ключ авторизации активен в GigaChat Studio и выбран правильный scope.
Repository not found при git push

Репозиторий на GitHub не создан или URL в origin указан с опечаткой. Создайте пустой репозиторий через github.com/new (без README и .gitignore) и проверьте git remote -v.
AsyncLibraryNotFoundError

Возникает при остановке бота — не критично, связано с завершением event loop. Игнорируйте.
Безопасность

    Не коммитьте .env — добавьте его в .gitignore.

    Не публикуйте токен бота и ключ GigaChat в чатах и скриншотах. При компрометации перевыпустите ключ в GigaChat Studio и сделайте /revoke в @BotFather.

    Не отключайте verify_ssl_certs для GigaChat — используйте ca_bundle_file.

Лицензия

Учебный проект. Используйте на своё усмотрение.
