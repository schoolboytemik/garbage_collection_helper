import csv
from aiogram.types import Update
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class UserDBMiddleware(BaseMiddleware):
    def __init__(self, db_file="users.csv"):
        super().__init__()
        self.db_file = db_file

        try:
            with open(self.db_file, mode='x', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "username"])
        except FileExistsError:
            pass

    async def __call__(self, handler, event: Update, data: dict):
        if event.message:
            user_id = event.message.from_user.id
            username = event.message.from_user.username or "Anonymous"

            # Проверяем, есть ли пользователь в базе
            with open(self.db_file, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                users = {row[0] for row in reader}

            # Если пользователя нет, добавляем его
            if str(user_id) not in users:
                with open(self.db_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([user_id, username])

        return await handler(event, data)
