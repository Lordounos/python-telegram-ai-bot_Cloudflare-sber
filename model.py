import os
import logging

import dotenv
import requests

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Загружаем переменные окружения из файла .env
try:
    env = dotenv.dotenv_values(".env")
    GIGACHAT_CREDENTIALS = env["GIGACHAT_CREDENTIALS"]
except FileNotFoundError:
    raise FileNotFoundError(
        "Файл .env не найден. Убедитесь, что он существует в корневой директории проекта."
    )
except KeyError as e:
    raise KeyError(
        f"Переменная окружения {str(e)} не найдена в файле .env. Проверьте его содержимое."
    )


class GigaChatService:
    """
    Сервис для взаимодействия с GigaChat API (Сбер).
    """

    def __init__(self, prompt_file):
        """
        Аргументы:
            prompt_file (str): Путь к файлу с системным промптом.
        """
        with open(prompt_file, encoding="utf-8") as f:
            self.sys_prompt = f.read()

        self.client = GigaChat(
            credentials=os.getenv("GIGACHAT_CREDENTIALS", GIGACHAT_CREDENTIALS),
            scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
            ca_bundle_file=os.getenv(
                "GIGACHAT_CA_BUNDLE_FILE", "russian_trusted_root_ca.pem"
            ),
            model="GigaChat-2",
            verify_ssl_certs=True,
        )

    def chat(self, message, history):
        """
        Отправляет сообщение в GigaChat и получает ответ.

        Аргументы:
            message (str): Сообщение пользователя.
            history (list): История сообщений (список dict с ключами 'role' и 'content').

        Возвращает:
            str: Ответ GigaChat.
        """
        messages = [Messages(role=MessagesRole.SYSTEM, content=self.sys_prompt)]

        for item in history[-4:]:
            role = (
                MessagesRole.USER
                if item["role"] == "user"
                else MessagesRole.ASSISTANT
            )
            messages.append(Messages(role=role, content=item["content"]))

        messages.append(Messages(role=MessagesRole.USER, content=message))

        try:
            response = self.client.chat(Chat(messages=messages))
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GigaChat error: {str(e)}")
            return f"Ошибка GigaChat: {str(e)}"


class OllamaService:
    """
    Сервис для взаимодействия с локальным Ollama API.
    """

    def __init__(
        self,
        prompt_file,
        base_url="http://localhost:11434",
        model="hf.co/mlabonne/gemma-3-4b-it-abliterated-GGUF:Q8_0",
    ):
        """
        Аргументы:
            prompt_file (str): Путь к файлу с системным промптом.
            base_url (str): URL Ollama API.
            model (str): Название модели Ollama.
        """
        with open(prompt_file, encoding="utf-8") as f:
            self.sys_prompt = f.read()
        self.base_url = base_url
        self.model = model

    def chat(self, message, history):
        """
        Отправляет сообщение в Ollama и получает ответ.

        Аргументы:
            message (str): Сообщение пользователя.
            history (list): История сообщений (список dict с ключами 'role' и 'content').

        Возвращает:
            str: Ответ Ollama.
        """
        messages = [{"role": "system", "content": self.sys_prompt}] + history[
            -4:
        ] + [{"role": "user", "content": message}]
        payload = {"model": self.model, "messages": messages, "stream": False}
        try:
            response = requests.post(
                f"{self.base_url}/api/chat", json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama error: {str(e)}")
            return f"Ошибка Ollama: {str(e)}"


# Переключение между сервисами: раскомментируйте нужную строку
llm_1 = GigaChatService("prompts/prompt_1.txt")
# llm_1 = OllamaService("prompts/prompt_1.txt")


def chat_with_llm(user_message, history):
    """
    Чат с использованием выбранного сервиса LLM.
    К переменной history добавляется сообщение пользователя и ответ LLM.

    Аргументы:
        user_message (str): Сообщение пользователя.
        history (list): История сообщений.

    Возвращает:
        str: Ответ LLM.
    """
    llm_response = llm_1.chat(user_message, history)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": llm_response})
    return llm_response
