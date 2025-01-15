from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import asyncio

API_TOKEN = ""  # Telegram-бот
HF_AUTH_TOKEN = ""  # Hugging Face

model_name = "TheBloke/Llama-2-7B-Chat-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=HF_AUTH_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    use_auth_token=HF_AUTH_TOKEN,
    device_map="auto",
    torch_dtype="auto"
)
text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

base_prompt = """<s>[INST] <<SYS>>
You are a virtual garbage sort helper. Speak Russian and use Russian sort rules. Help people properly sort their waste.
<</SYS>>"""


def generate_response(prompt):
    outputs = text_generator(prompt, max_new_tokens=150, temperature=0.7, do_sample=True)
    return outputs[0]["generated_text"]


bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привет! Я бот, помогающий сортировать мусор!")


# Обработка текстовых сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_input = message.text
    try:
        await message.answer("Генерирую ответ, подождите немного...")
        response = generate_response(user_input)
        await message.answer(response)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
