import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import os
from user_middleware import UserDBMiddleware
from log_middleware import LoggingMiddleware
from model import query_gigachat, analyze_message

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключение Middleware
dp.update.middleware(UserDBMiddleware(db_file="users.csv"))
dp.update.middleware(LoggingMiddleware(log_file="logs.csv"))

# Локальное временное хранилище данных
global USER_DATA
USER_DATA = {}


# FSM для регистраций и настройки напоминаний
class ReminderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_time = State()
    waiting_for_feedback = State()


# ==========================
# Стартовая команда и регистрация
# ==========================
@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """
    Приветственное сообщение при регистрации.
    """
    await state.clear()
    global USER_DATA
    user_id = message.from_user.id

    # Уже зарегистрированные пользователи
    if user_id in USER_DATA:
        name = USER_DATA[user_id]["name"]
        await message.answer(f"С возвращением, {name}! Вот главное меню:", reply_markup=get_main_menu())
        return

    # Регистрация нового пользователя
    await message.answer("Привет! Как я могу называть Вас?")
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
        f"Приятно познакомиться, {user_name}! Теперь Вы можете управлять настройками через меню:",
        reply_markup=get_main_menu(),
    )
    await state.clear()


@dp.message(ReminderStates.waiting_for_feedback)
async def feedback_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    review = message.text.lower().strip()
    with open(f"reviews/{user_id}.txt", "a") as file:
        file.write(review + "\n")
    await message.answer("Спасибо за ваш отзыв!")
    await state.clear()


# ==========================
# Главное меню
# ==========================
@dp.message(Command("menu"))
async def show_menu(message: Message):
    """
    Главное меню.
    """
    await message.answer("Вот Ваше главное меню:", reply_markup=get_main_menu())


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

    elif text == "☎️ обратная связь":
        await message.answer("Спасибо, что пользуетесь нашим сервисом! Напишите ваш отзыв:")
        await state.set_state(ReminderStates.waiting_for_feedback)
        return

    elif text == "🚮 правила сортировки":
        photo_1 = FSInputFile('images/first_type.jpg')
        photo_2 = FSInputFile('images/2nd_type.jpg')

        # MD
        text_1 = """
        В России существуют два проекта по раздельному сбору мусора.
        **Проект 1:**
        Представляет собой разделение на 2 контейнера для вторсырья и смешанных отходов синего и серого цветов соответственно.
        Контейнеры с синей наклейкой и надписью «Вторсырье» предназначены для отходов, которые подлежат переработке. Бумагу, пластик, стекло и металл следует выбрасывать именно в них. В контейнеры с серой наклейкой и надписью «Смешанные отходы» можно бросать все остальное: пищевые отходы, средства личной гигиены, неперерабатываемые емкости из-под продуктов питания и другое.
         """

        text_2 = """
        **Проект 2:** 
        Представляет собой разделение на 4 цвета.
        Желтые - для пластика;
        Синие - для стекла;
        Зеленые - для бумаги;
        Красный - для несортируемых отходов.
        
        Куда выкинуть батарейки, лампочки, термометры?

        Это опасные отходы, их нельзя выбрасывать в обычные контейнеры. Люминесцентные лампы, содержащие ртуть, можно сдать в помещениях объединенных диспетчерских служб ([ОДС](https://data.mos.ru/opendata/2459)). Информация о графике работы размещена на входных дверях ОДС, на информационных стендах и в подъездах домов. В столице более 900 таких точек приема.
        
        Ртутные термометры принимают по адресу: Варшавское шоссе, дом 93.

        Отработанные батарейки можно сдать в магазинах, офисных центрах, оставить в уличных боксах. Полный список точек приема опубликован [на сайте](https://eco2eco.ru/map/). 
        """

        await bot.send_photo(message.chat.id, photo=photo_1, caption=text_1, parse_mode="Markdown")
        await bot.send_photo(message.chat.id, photo=photo_2, caption=text_2, parse_mode="Markdown")
        return

    # Обновляем статистику, если сообщение связано с переработкой
    resource = analyze_message(text)  # Вызов функции анализа текста (из gigachat_utils.py)
    updated = update_statistics(user_id, resource)
    if updated:
        try:
            stats_message = get_user_statistics(user_id)
            await message.answer(f"✅ Статистика обновлена:\n{stats_message}")
        except Exception as error:
            print(f"Ошибка при работе с GigaChat: {error}")
            await message.answer("⚠️ Ошибка связи с GigaChat. Попробуйте позже.")

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
            [KeyboardButton(text="🚮 Правила сортировки")],
            [KeyboardButton(text="☎️ Обратная связь")],
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


def update_statistics(user_id: int, resource: str) -> bool:
    valid_resources = ["пластик", "стекло", "металл", "бумага", "батарейки"]
    resource = resource.lower()

    # Проверяем, что ресурс допустим и обновляем статистику
    if resource in valid_resources:
        USER_DATA[user_id]["statistics"].setdefault(resource, 0)
        USER_DATA[user_id]["statistics"][resource] += 1
        return True
    return False


def get_user_statistics(user_id: int) -> str:
    stats = USER_DATA.get(user_id, {}).get("statistics", {})
    if not stats:
        return "Статистика пока пуста."

    return "\n".join(f"✅ {key.capitalize()}: {value}" for key, value in stats.items())


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
