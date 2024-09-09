from datetime import datetime, timedelta
from aiogram import F, Bot, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


import app.keyboards as kb
from app.variables import today_year

from database.models import Friend, User
from database.orm_requests import orm_add_new_friend, orm_check_birthday, orm_check_user_exists, orm_get_all_my_friends, orm_get_user_db_id, orm_get_user_full_name, orm_reg_user

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.apsched import apsch_send_message_middleware_time, apsch_send_message_middleware_cron

from app.constants import need_reg, what_i_can


router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message, bot: Bot, session: AsyncSession,
    apscheduler: AsyncIOScheduler
    ):
    # если из БД из модели Юзер нельзя извлечь из столбца tg_id id текущего юзера
    user = await orm_check_user_exists(session, message)
    if not user:
        await message.reply(
        f'Здравствуйте, я BirthdayBot!\n'
        f'Чтобы начать пользоваться сервисом,\n'
        f'пройдите регистрацию, нажав на кнопку',
        reply_markup=kb.reg_button
    )
    else:
        name = await orm_get_user_full_name(session, message)
        await message.reply(f'Здравствуйте, {name}!')
    apscheduler.add_job(
        apsch_send_message_middleware_time,
        trigger='date',
        next_run_time=datetime.now() + timedelta(seconds=5),
        kwargs={'bot': bot, 'chat_id': message.from_user.id}
        )

class Reg_user(StatesGroup):
    """Describes user`s states during registration."""

    user_name = State()


# После нажатия на кнопку начинается регистрация
@router.message(F.text == 'Зарегистрироваться')
async def reg_user_first(message: Message, state: FSMContext):
    await state.set_state(Reg_user.user_name)
    await message.answer('Введите Ваше полное имя')

@router.message(Reg_user.user_name)
async def reg_user_second(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(username=message.text)
    data = await state.get_data()
    data['telegram_id'] = message.from_user.id
    #data['chatid'] = message.chat.id
    # записываем данные в БД
    await orm_reg_user(session, data)
    # выводим данные в сообщении, чтобы легче проверить правильность ввода
    await message.reply(
        f'Ваш ID: {data['telegram_id']},\n'
        f'Имя: {data['username']}',
        #f'Чат ID: {data['chatid']}'
        )
    await state.clear()


class Add_friend(StatesGroup):
    """Describes user`s states while appending new friends."""
    full_name = State()
    date_month = State()
    birth_year = State()

# после команды /add начнётся регистрация нового пользователя
@router.message(Command('add'))
async def add_first(message: Message, state: FSMContext):
    await state.set_state(Add_friend.full_name)
    await message.answer(f'Введите полное имя и фамилию человека,'
                         f' и я напомню Вам о его Дне Рождения!'
                          )

@router.message(Add_friend.full_name)
async def add_second(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await state.set_state(Add_friend.date_month)
    await message.answer(f'Введите дату рождения и месяц в формате: 01.01')

@router.message(Add_friend.date_month)
async def add_third(message: Message, state: FSMContext):
    await state.update_data(datemonth=message.text)
    await state.set_state(Add_friend.birth_year)
    await message.answer(f'Введите год рождения в формате: 1965')

@router.message(Add_friend.birth_year)
async def add_forth(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(birthyear=message.text)
    data = await state.get_data()
    db_id = await orm_get_user_db_id(session, message)
    data['userid'] = db_id
    # теперь вся сохранённая инф хранится в виде словаря,
    # эту информацию можно за один раз отправить в БД и
    # создать новую запись о новом друге
    await orm_add_new_friend(session, data)
  
    # теперь отправим пользователю сообщение
    await message.answer(f'Спасибо, запись добавлена.\n'
                         f'Полное имя: {data['fullname']},\n'
                         f'Число и месяц рождения: {data['datemonth']},\n'
                         f'Год рождения: {data['birthyear']},\n'
                         f'Ваш id в БД: {data['userid']}'
                         )
    # очистим состояние, чтобы не засорять кэш бота
    await state.clear()


@router.message(Command('help'))
async def get_help(message: Message, session: AsyncSession):
    # если из БД из модели Юзер нельзя извлечь из столбца tg_id id текущего юзера
    user = await orm_check_user_exists(session, message)
    if not user:
        await message.reply(need_reg)
    else:
        await message.reply(what_i_can)


@router.message(Command('check'))
async def check(message: Message, session: AsyncSession):
    """Включение принудительной проверки наличия именниников в БД."""
    db_id = await orm_get_user_db_id(session, message)
    birthdays = await orm_check_birthday(session, db_id)
    for birth in birthdays:
        years_old = today_year - birth.birth_year
        await message.answer(f'Сегодня именинник {birth.full_name}!\n'
                             f'Исполняется {years_old} лет :)'
                             )

@router.message(Command('remind_me'))
async def remind_me(message: Message, session: AsyncSession,
                    bot: Bot, apscheduler: AsyncIOScheduler
                    ):
    """Включение принудительной проверки наличия именниников в БД."""
    chat_id = message.from_user.id
    apscheduler.add_job(
        apsch_send_message_middleware_cron,
        trigger='cron',
        hour=datetime.now().hour,  # текущий час hour=datetime.now().hour
        minute=datetime.now().minute + 1,  # запустится через 1 минуту
        #second=datetime.now().second + 1,  # запустится через 1 минуту
        start_date=datetime.now(),  # задача начнёт выполнятся начиная с сегодня
        kwargs={'bot': bot, 'chat_id': chat_id, 'message': message, 'session': session}
    )


@router.message(Command('all_friends'))
async def get_all_friends(message: Message, session: AsyncSession):
    """Получение списка всех друзей.

    Пока каждый будет выводиться отдельным сообщением.
    """
    db_id = await orm_get_user_db_id(session, message)
    for friend in await orm_get_all_my_friends(session, db_id):
        await message.answer(
            f'ID: {friend.id},\n'
            f'Полное имя: {friend.full_name},\n'
            f'Дата и год рождения: {friend.date_month}.{friend.birth_year}'
        )



# apsch_send_message_middleware_cron,
#         trigger='cron',
#         hour=datetime.now().hour,  # текущий час hour=datetime.now().hour
#         minute=datetime.now().minute + 1,  # запустится через 1 минуту
#         second=datetime.now().second + 1,  # запустится через 1 секунду
#         start_date=datetime.now(),  # задача начнёт выполнятся начиная с сегодня
#         kwargs={'bot': bot, 'chat_id': chat_id, 'message': message, 'session': session}