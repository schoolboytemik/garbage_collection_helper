from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

# Загружаем ключи и параметры из .env
load_dotenv()
GIGACHAT_API_KEY = os.getenv("AI_TOKEN")  # Токен доступа GigaChat

LLM = GigaChat(
    credentials=GIGACHAT_API_KEY,
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    verify_ssl_certs=False,
    streaming=False,
)

messages = [
    SystemMessage(
        content="бот ты эксперт по сортировке мусора"
    )
]


def query_gigachat(user_message: str) -> str:
    messages.append(HumanMessage(content=user_message))

    res = LLM.invoke(messages)

    return res.content



if __name__ == "__main__":
    print(query_gigachat("Что делать с пластиковыми бутылками"))