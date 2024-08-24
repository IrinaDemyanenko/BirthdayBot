import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from app.handlers import router

bot = Bot(token=TOKEN)
disp = Dispatcher()

async def main():
    """Starts main code."""
    disp.include_router(router)
    await disp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

