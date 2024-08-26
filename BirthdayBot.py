import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from app.handlers import router
from database.db_middleware import DataBaseSession
from database.models import create_db, drop_db, async_session


bot = Bot(token=TOKEN)
disp = Dispatcher()
db = DataBaseSession('birthdaybot.db')

async def main():
    """Starts main code."""

    await create_db()
    # подключим db_middleware к основному роутеру, на самый ранний этап, но уже после прохождения всех фильтров
    disp.update.middleware(DataBaseSession(session_pool=async_session))
    disp.include_router(router)
    await disp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

