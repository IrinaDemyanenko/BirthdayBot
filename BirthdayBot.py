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

from apscheduler.triggers.cron import CronTrigger
from app.apsched import apsch_send_birthday_reminders_week_before  # Подключаем функцию напоминаний

bot = Bot(token=TOKEN)
disp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Эта функция добавляет задачу в планировщик
def schedule_birthday_reminders_week_before(bot, sessionmaker):
    """Запускает планировщик для напоминаний за неделю до ДР."""
    async def job():
        # Создаём сессию внутри контекстного менеджера
        async with sessionmaker() as session:
            await apsch_send_birthday_reminders_week_before(bot, session)

    # Запускаем функцию каждый день в 12:00
    scheduler.add_job(
        job,  # Запуск новой функции, которая создаст сессию
        CronTrigger(hour=12, minute=00),  # Напоминания будут отправляться каждый день в 15:35
    )

    # Запуск планировщика уже есть в main()
    #scheduler.start()

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
    # Запуск планировщика напоминаний о днях рождения за неделю до
    schedule_birthday_reminders_week_before(bot, async_session)
    # запускаем задачи по расписанию
    scheduler.start()
    await disp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
