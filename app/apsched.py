from aiogram import Bot

from database.orm_requests import orm_check_birthday, orm_get_user_db_id

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.variables import today_year


async def apsch_send_message_middleware_time(bot: Bot, chat_id: int):
    """Сообщение отправляется через определённое время.
    
    В данном случае несколько секунд после команды /start, т е
    старта. Задача сформирована через middleware - apscheduler."""
    await bot.send_message(chat_id, # для личных сообщений chat_id == telegramm_id пользователя
                           f'Вот что я умею:\n'
                           f'/start - форма регистрации,\n'
                           f'/add - добавление новых друзей в Ваш '
                           f'персональный список близких людей,\n'
                           f'/check - проверка наличия именинников сегодня,\n'
                           f'/remind_me - включение уведомлений,\n'
                           f'/help - список доступных команд\n'
                           )


async def apsch_send_message_middleware_cron(
        bot: Bot, chat_id: int, message: Message, session: AsyncSession
        ):
    """Сообщение отправляется по расписанию каждый день.
    
    В данном случае несколько секунд после команды /remind_me,
    запустится механизм ежедневной проверки БД на наличие именниников сегодня.
    В случае, если именинники есть, придёт уведомление.
    Задача сформирована через middleware - apscheduler."""
    db_id = await orm_get_user_db_id(session, message)
    birthdays = await orm_check_birthday(session, db_id)
    for birth in birthdays:
        years_old = today_year - birth.birth_year
        await bot.send_message(chat_id, # для личных сообщений chat_id == telegramm_id пользователя
                               f'Сегодня именинник {birth.full_name}!\n'
                               f'Исполняется {years_old} лет :)'
                            )

# async def send_message_time(bot: Bot):
#     """Сообщение отправляется через несколько секунд после старта."""
#     await bot.send_message(530876949, f'Это сообщ через неск сек после старта')


# async def send_message_cron(bot: Bot):
#     """Сообщение отправляется ежедневно в указанное время."""
#     await bot.send_message(530876949, f'Это сообщ ежедневно в указанное время')


# async def send_message_interval(bot: Bot):
#     """Сообщение отправляется с интервалом времени"""
#     await bot.send_message(530876949, f'Это сообщ отпр с интервалом в 1 мин')

