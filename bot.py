from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import asyncio
import os

# Импортируем функцию для взаимодействия с GigaChat
from model import query_gigachat

# Загружаем токен Telegram
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Создаём бота и диспетчер
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: Message):
    """
    Приветственное сообщение при вводе команды /start
    """
    await message.answer("Привет! Я бот, который поможет вам разобраться в сортировке мусора. Задайте свой вопрос!")


# Основной обработчик для сообщений пользователя
@dp.message()
async def handle_user_message(message: Message):
    """
    Получает текст от пользователя, перенаправляет через GigaChat и возвращает ответ.
    """
    user_input = message.text  # Получаем текст сообщения от пользователя
    try:
        # Отправляем текст пользователя в GigaChat и ждём ответа
        response = query_gigachat(user_input)
        # Возвращаем полученный ответ пользователю
        await message.answer(response)
    except Exception as e:
        # Если возникает ошибка, выводим сообщение об ошибке
        await message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        print(f"Ошибка: {e}")


# Запуск бота
async def main():
    """
    Основной цикл запуска Telegram-бота.
    """
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
