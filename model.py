from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv
import os


load_dotenv()
GIGACHAT_API_KEY = os.getenv("AI_TOKEN")

LLM = GigaChat(
    credentials=GIGACHAT_API_KEY,
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    verify_ssl_certs=False,
    streaming=False,
)

messages = [
    SystemMessage(
        content="Ты виртуальный помощник в сортировке и утилизации мусора и иных отходов в России. Помогай собеседнику правильно сортировать и выкидывать мусор. Все ответы должны быть краткими и информативными поддерживай контекст. Всегда отвечай только на последний вопрос"
    )
]

MAX_HISTORY = 5

# Функция для отправки сообщения и получения ответа
def query_gigachat(user_message: str) -> str:
    try:
        messages.append(HumanMessage(content=user_message))

        if len(messages) > MAX_HISTORY + 1:
            messages[1:-MAX_HISTORY] = []

        response = LLM.invoke(messages)

        messages.append(AIMessage(content=response.content))

        return response.content
    except Exception as e:
        print(f"Ошибка при запросе к GigaChat: {e}")
        return "Произошла ошибка. Попробуйте повторить запрос позже."


if __name__ == "__main__":
    print(query_gigachat("Что делать с пластиковыми бутылками?"))
    print(query_gigachat("А с бумажными стаканчиками?"))
    print(query_gigachat("А бананы?"))
    print(query_gigachat("Где сдавать батарейки?"))