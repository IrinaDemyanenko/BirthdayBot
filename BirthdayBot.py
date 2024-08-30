import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from app.handlers import router
from database.db_middleware import DataBaseSession
from database.models import create_db, drop_db, async_session

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app import apsched
from datetime import datetime, timedelta
from app.apschedular_middleware import SchedulerMiddleware

bot = Bot(token=TOKEN)
disp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# scheduler.add_job(
#     apsched.send_message_time,
#     trigger='date',
#     next_run_time=datetime.now() + timedelta(seconds=10),
#     kwargs={'bot': bot }
#     )

# scheduler.add_job(
#     apsched.send_message_cron,
#     trigger='cron',
#     hour=datetime.now().hour,  # текущий час
#     minute=datetime.now().minute + 1,  # запустится через 1 минуту
#     start_date=datetime.now(),  # задача начнёт выполнятся начиная с сегодня
#     kwargs={'bot': bot }
#     )

# scheduler.add_job(
#     apsched.send_message_interval,
#     trigger='interval',
#     seconds=25, 
#     kwargs={'bot': bot }
#     )



async def main():
    """Starts main code."""

    await create_db()
    # подключим db_middleware к основному роутеру, на самый ранний этап, но уже после прохождения всех фильтров
    disp.update.middleware(DataBaseSession(session_pool=async_session))
    # регистрируем второй мидлваре SchedulerMiddleware, тоже на все обновления
    disp.update.middleware(SchedulerMiddleware(scheduler))
    disp.include_router(router)
    # запускаем задачи по расписанию
    scheduler.start()
    await disp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

