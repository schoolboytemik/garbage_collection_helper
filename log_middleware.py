import csv
from aiogram.types import Update
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, log_file="logs.csv"):
        super().__init__()
        self.log_file = log_file

        try:
            with open(self.log_file, mode='x', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "user_id", "username", "message"])  # Заголовки
        except FileExistsError:
            pass

    async def __call__(self, handler, event: Update, data: dict):
        if event.message:
            user_id = event.message.from_user.id
            username = event.message.from_user.username or "Anonymous"
            text = event.message.text or ""
            timestamp = event.message.date.strftime('%Y-%m-%d %H:%M:%S')

            with open(self.log_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, user_id, username, text])

        return await handler(event, data)
