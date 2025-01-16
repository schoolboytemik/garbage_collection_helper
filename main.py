import os
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import requests
import logging
import asyncio

# Загрузка ключей из .env
load_dotenv()
TELEGRAM_BOT_API_KEY = os.getenv("TELEGRAM_BOT_API_KEY")
LLAMA_API_URL = os.getenv("LLAMA_API_URL")  # URL языковой модели

# Логирование
logging.basicConfig(level=logging.INFO)

# Бот и диспетчер
bot = Bot(token=TELEGRAM_BOT_API_KEY)
dp = Dispatcher(storage=MemoryStorage())
router = Router()  # Используем Router для организации хэндлеров

# Статистика пользователей (имитация БД)
user_stats = {}

# FSM для регистрации
class Registration(StatesGroup):
    name = State()
    schedule = State()

# Функция для запросов к языковой модели
async def query_llama(prompt):
    try:
        response = requests.post(LLAMA_API_URL, json={"prompt": prompt})
        if response.status_code == 200:
            return response.json().get("response", "Не удалось получить корректный ответ.")
        return "Ошибка: проверьте соединение с моделями."
    except Exception as ex:
        logging.error(f"Ошибка при запросе к языковой модели: {ex}")
        return "Не удалось подключиться к языковой модели."

# Хэндлер для команды /start
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_stats:
        user_stats[user_id] = {"queries": 0}  # Инициализировать статистику для пользователя
    await state.set_state(Registration.name)  # Устанавливаем начальное состояние
    await message.answer("Привет! Я помогу с раздельным сбором отходов. Как я могу к вам обращаться?")

# Хэндлер для ввода имени
@router.message(Registration.name)
async def set_user_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.schedule)
    await message.answer("Когда вам напоминать о раздельном сборе? Укажите время в формате HH:MM (например, 08:30).")

# Хэндлер для ввода расписания
@router.message(Registration.schedule)
async def set_user_schedule(message: types.Message, state: FSMContext):
    schedule = message.text
    try:
        hour, minute = map(int, schedule.split(":"))
        if 0 <= hour < 24 and 0 <= minute < 60:
            await state.update_data(schedule=schedule)
            user_data = await state.get_data()
            user_stats[message.from_user.id].update(user_data)  # Сохраняем настройки в "БД"
            await state.clear()
            await message.answer(f"Регистрация завершена! Имя: {user_data['name']}, напоминания: {schedule}.")
        else:
            raise ValueError
    except ValueError:
        await message.answer("Некорректный формат времени. Укажите время в формате HH:MM.")

# Хэндлер для обработки помощи
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Я здесь, чтобы помочь с сортировкой отходов!\n"
        "- Задайте мне вопрос, например, 'Куда выбросить пластик?'\n"
        "- Используйте /stats, чтобы проверить вашу статистику."
    )

# Хэндлер для основной обработки вопросов
@router.message()
async def handle_query(message: types.Message):
    user_id = message.from_user.id
    user_stats[user_id]["queries"] = user_stats[user_id].get("queries", 0) + 1  # Увеличение статистики запросов
    answer = await query_llama(message.text)
    await message.answer(answer)

# Хэндлер для отображения статистики
@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    user_data = user_stats.get(user_id, {})
    queries = user_data.get("queries", 0)
    schedule = user_data.get("schedule", "не настроено")
    await message.answer(
        f"📊 Ваша статистика:\n"
        f"- Запросов: {queries}\n"
        f"- Время напоминаний: {schedule}"
    )

# Напоминания через Apscheduler
async def send_reminder():
    for user_id, data in user_stats.items():
        schedule = data.get("schedule")
        if schedule:
            await bot.send_message(user_id, "🔔 Время напоминания! Проверьте, как у вас идёт сортировка отходов.")

# Настройка периодических задач
scheduler = AsyncIOScheduler()
scheduler.add_job(send_reminder, "interval", hours=24)
scheduler.start()

# Запуск бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
