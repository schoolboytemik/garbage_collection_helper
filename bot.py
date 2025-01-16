import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import os

# Импорт GigaChat (заменить на ваш модуль)
from model import query_gigachat

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Локальное временное хранилище данных
USER_DATA = {}

# FSM для регистраций и настройки напоминаний
class ReminderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_time = State()


# ==========================
# Стартовая команда и регистрация
# ==========================
@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """
    Приветственное сообщение при регистрации.
    """
    await state.clear()
    user_id = message.from_user.id

    # Уже зарегистрированные пользователи
    if user_id in USER_DATA:
        name = USER_DATA[user_id]["name"]
        await message.answer(f"С возвращением, {name}! Вот главное меню:", reply_markup=get_main_menu())
        return

    # Регистрация нового пользователя
    await message.answer("Привет! Как я могу называть вас?")
    await state.set_state(ReminderStates.waiting_for_name)


@dp.message(ReminderStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """
    Запись имени пользователя и регистрация.
    """
    user_id = message.from_user.id
    user_name = message.text.strip()

    # Сохраняем данные пользователя
    USER_DATA[user_id] = {
        "name": user_name,
        "statistics": {"пластик": 0, "стекло": 0, "металл": 0},
        "reminder_time": "09:00",
    }

    await message.answer(
        f"Приятно познакомиться, {user_name}! Теперь вы можете управлять настройками через меню:",
        reply_markup=get_main_menu(),
    )
    await state.clear()


# ==========================
# Главное меню
# ==========================
@dp.message(Command("menu"))
async def show_menu(message: Message):
    """
    Главное меню.
    """
    await message.answer("Вот ваше главное меню:", reply_markup=get_main_menu())


@dp.message(ReminderStates.waiting_for_time)
async def process_reminder_time(message: Message, state: FSMContext):
    """
    Установка времени для напоминаний.
    """
    user_id = message.from_user.id
    reminder_time = message.text.strip()

    # Проверка формата времени
    if not validate_time_format(reminder_time):
        await message.answer("⚠️ Неверный формат времени. Используйте формат ЧЧ:ММ, например, 08:30.")
        return

    # Сохранение нового времени напоминаний
    USER_DATA[user_id]["reminder_time"] = reminder_time
    await message.answer(f"✅ Напоминания установлены на {reminder_time}.", reply_markup=get_main_menu())
    await state.clear()


# ==========================
# Основной обработчик сообщений
# ==========================
@dp.message()
async def handle_messages(message: Message, state: FSMContext):
    """
    Обработка всех сообщений пользователя (обновление статистики и работа с GigaChat).
    """
    user_id = message.from_user.id
    text = message.text.lower().strip()

    # Проверка регистрации пользователя
    if user_id not in USER_DATA:
        await message.answer("Сначала зарегистрируйтесь с помощью команды /start.")
        return

    # Обработка команд меню
    if text == "📊 посмотреть статистику":
        stats = USER_DATA[user_id]["statistics"]
        stats_message = "\n".join(f"✅ {key}: {value}" for key, value in stats.items())
        await message.answer(f"📊 Ваша статистика:\n{stats_message}")
        return

    elif text == "⏰ настроить напоминания":
        await message.answer("Введите время для напоминаний в формате ЧЧ:ММ, например, 08:30.")
        await state.set_state(ReminderStates.waiting_for_time)
        return

    # Обновляем статистику, если сообщение связано с переработкой
    updated = update_statistics(user_id, text)
    if updated:
        stats = USER_DATA[user_id]["statistics"]
        stats_message = "\n".join(f"✅ {key}: {value}" for key, value in stats.items())
        await message.answer(f"✅ Статистика обновлена:\n{stats_message}")
        return

    # В противном случае, отправляем запрос в GigaChat
    try:
        response = query_gigachat(text)
        await message.answer(response)
    except Exception as error:
        print(f"Ошибка запроса к GigaChat: {error}")
        await message.answer("⚠️ Ошибка связи с GigaChat. Попробуйте позже.")


# ==========================
# Утилиты
# ==========================
def get_main_menu():
    """
    Главное меню.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Посмотреть статистику")],
            [KeyboardButton(text="⏰ Настроить напоминания")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def validate_time_format(time_str):
    """
    Проверка формата времени ЧЧ:ММ.
    """
    try:
        hours, minutes = map(int, time_str.split(":"))
        return 0 <= hours < 24 and 0 <= minutes < 60
    except ValueError:
        return False


def update_statistics(user_id: int, text: str) -> bool:
    """
    Обновляем статистику пользователя по ключевым словам.
    """
    if "пластик" in text:
        USER_DATA[user_id]["statistics"]["пластик"] += 1
        return True
    elif "стекло" in text:
        USER_DATA[user_id]["statistics"]["стекло"] += 1
        return True
    elif "металл" in text:
        USER_DATA[user_id]["statistics"]["металл"] += 1
        return True
    return False


# ==========================
# Запуск бота
# ==========================
async def main():
    """
    Главная точка входа.
    """
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
