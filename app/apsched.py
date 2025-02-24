import datetime
from aiogram import Bot

from database.orm_requests import orm_check_birthday, orm_get_user_db_id, orm_get_upcoming_birthdays

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.variables import today_year
from app.constants import what_i_can


async def apsch_send_message_middleware_time(bot: Bot, chat_id: int):
    """Сообщение отправляется через определённое время.

    В данном случае несколько секунд после команды /start, т е
    старта. Задача сформирована через middleware - apscheduler."""
    await bot.send_message(chat_id, # для личных сообщений chat_id == telegramm_id пользователя
                           what_i_can
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


async def apsch_send_birthday_reminders_week_before(bot: Bot, session: AsyncSession):
    """Отправляет напоминания за неделю до дня рождения,
    если включена функция notify_week_before.
    """
    try:
        # Получаем дату через 7 дней
        next_week_date = datetime.datetime.now() + datetime.timedelta(days=7)
        # Приводим к формату ДД.ММ
        next_week_date_month = next_week_date.strftime('%d.%m')

        # Запрашиваем всех пользователей и их друзей с ДР через неделю
        upcoming_birthdays = await orm_get_upcoming_birthdays(session, next_week_date_month)
        # Логируем полученные данные
        print(f"Upcoming birthdays for {next_week_date_month}: {upcoming_birthdays}")

        # Проходим по всем пользователям, у которых есть друзья с ДР
        for user_id, friends in upcoming_birthdays.items():
            reminders = []  # список строк напоминай для каждого друга

            # Перебираем друзей каждого пользователя
            for friend in friends:
                if friend.notify_week_before:  # Проверяем, включено ли напоминание
                    years_old = today_year - friend.birth_year
                    reminders.append(f'{friend.full_name} - ему/ей исполнится {years_old} лет!')

            # Если у пользователя есть напоминания, отправляем сообщение
            if reminders:
                message_text = f'Напоминаю, через неделю день рождения у:\n' + '\n'.join(reminders)
                await bot.send_message(user_id, message_text)
    except Exception as e:
        print(f"Error while sending birthday reminders: {e}")




# async def send_message_time(bot: Bot):
#     """Сообщение отправляется через несколько секунд после старта."""
#     await bot.send_message(530876949, f'Это сообщ через неск сек после старта')


# async def send_message_cron(bot: Bot):
#     """Сообщение отправляется ежедневно в указанное время."""
#     await bot.send_message(530876949, f'Это сообщ ежедневно в указанное время')


# async def send_message_interval(bot: Bot):
#     """Сообщение отправляется с интервалом времени"""
#     await bot.send_message(530876949, f'Это сообщ отпр с интервалом в 1 мин')
