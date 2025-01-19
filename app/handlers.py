from datetime import datetime, timedelta
import re
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
from database.orm_requests import orm_add_new_friend, orm_check_birthday, orm_check_user_exists, orm_get_all_my_friends, orm_get_friend, orm_get_user_db_id, orm_get_user_full_name, orm_reg_user
from database.orm_requests import orm_update_friend, orm_delete_friend

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.apsched import apsch_send_message_middleware_time, apsch_send_message_middleware_cron

from app.constants import need_reg, what_i_can, correct_year
from app.variables import current_year


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
    full_name = message.text.strip()

    # Проверка, что введено хотя бы два слова (имя и фамилия)
    if len(full_name.split()) < 2:
        await message.answer('Пожалуйста, введите полное имя и фамилию.')
        return

    await state.update_data(fullname=full_name)
    await state.set_state(Add_friend.date_month)
    await message.answer(f'Введите дату рождения и месяц в формате: 01.01')

@router.message(Add_friend.date_month)
async def add_third(message: Message, state: FSMContext):
    date_month = message.text.strip()

    # Проверка, что дата соответствует формату dd.mm
    if not re.match(r'^\d{2}\.\d{2}$', date_month):
        await message.answer(
            'Пожалуйста, введите дату в правильном формате: 01.01 (число.месяц)'
            )
        return

    await state.update_data(datemonth=date_month)
    await state.set_state(Add_friend.birth_year)
    await message.answer(f'Введите год рождения в формате: 1965')

@router.message(Add_friend.birth_year)
async def add_forth(message: Message, state: FSMContext, session: AsyncSession):
    birth_year = message.text.strip()

    # Проверка, что введен год из 4 цифр и это разумный год
    if not re.match(r'^\d{4}$', birth_year):
        await message.answer(
            'Пожалуйста, введите год в правильном формате: 1965'
            )
        return

    if not current_year - 120 < int(birth_year) < current_year:
        await message.answer(correct_year)
        return


    await state.update_data(birthyear=birth_year)
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


class EditFriend(StatesGroup):
    """Описывает состояния пользователя в процессе редактировния
    записи о друге.
    """
    select_friend = State()
    full_name = State()
    date_month = State()
    birth_year = State()

@router.message(Command('edit'))
async def edit_friend_start(message: Message, state: FSMContext, session: AsyncSession):
    """Начало процесса редактирования информации о друге.

    Команда /edit отображает список друзей с их ID.
    Пользователь вводит ID друга, которого нужно редактировать.
    """
    db_id = await orm_get_user_db_id(session, message)
    friends = await orm_get_all_my_friends(session, db_id)

    if not friends:
        await message.answer('У вас пока нет друзей в базе для редактирования.')
        return

    # Формируем список друзей
    friends_list = "\n".join(
        [f"ID: {friend.id}, Имя: {friend.full_name}" for friend in friends]
    )
    await message.answer(f'Выберите ID друга для редактирования:\n{friends_list}')
    await state.set_state(EditFriend.select_friend)


@router.message(EditFriend.select_friend)
async def edit_friend_select(message: Message, state: FSMContext, session: AsyncSession):
    """Сохранение выбранного ID друга.

    Проверяется существование друга в базе по указанному ID.
    Если друг найден, начинается процесс обновления.
    """
    try:
        friend_id = int(message.text)
        friend = await orm_get_friend(session, friend_id)
        if not friend:
            raise ValueError

        await state.update_data(friend_id=friend_id)
        await message.answer(f'Вы редактируете друга: {friend.full_name}\n'
                             f'Введите новое полное имя или оставьте текущее, отправив "."')
        await state.set_state(EditFriend.full_name)
    except ValueError:
        await message.answer('Пожалуйста, введите корректный ID из списка.')


@router.message(EditFriend.full_name)
async def edit_friend_name(message: Message, state: FSMContext):
    """Обновление имени друга."""
    full_name = message.text.strip()
    if full_name != ".":
        # Проверка, что введено хотя бы два слова (имя и фамилия)
        if len(full_name.split()) < 2:
            await message.answer('Пожалуйста, введите полное имя и фамилию.')
            return
        await state.update_data(full_name=full_name)
    await message.answer('Введите новую дату рождения и месяц в формате: 01.01 (день.месяц) или оставьте текущую, отправив "."')
    await state.set_state(EditFriend.date_month)


@router.message(EditFriend.date_month)
async def edit_friend_date_month(message: Message, state: FSMContext):
    """Обновление даты и месяца рождения друга."""
    date_month = message.text.strip()

    if date_month != ".":
        # Проверка, что дата соответствует формату dd.mm
        if not re.match(r'^\d{2}\.\d{2}$', date_month):
            await message.answer(
            'Пожалуйста, введите дату в правильном формате: 01.01 (число.месяц)'
            )
            return

        await state.update_data(date_month=date_month)
    await message.answer('Введите новый год рождения или оставьте текущий, отправив "."')
    await state.set_state(EditFriend.birth_year)


@router.message(EditFriend.birth_year)
async def edit_friend_birth_year(message: Message, state: FSMContext, session: AsyncSession):
    """Обновление года рождения друга."""
    birth_year = message.text
    if birth_year != ".":
        # Проверка, что введен год из 4 цифр и это разумный год
        if not re.match(r'^\d{4}$', birth_year):
            await message.answer(
            'Пожалуйста, введите год в правильном формате: 1965'
            )
            return

        if not current_year - 120 < int(birth_year) < current_year:
            await message.answer(correct_year)
            return

        await state.update_data(birth_year=birth_year)

    # Получаем все данные
    data = await state.get_data()
    friend_id = data.get('friend_id')

    # Формируем новые данные для обновления
    new_data = {}
    if 'full_name' in data:
        new_data['full_name'] = data['full_name']
    if 'date_month' in data:
        new_data['date_month'] = data['date_month']
    if 'birth_year' in data:
        new_data['birth_year'] = int(data['birth_year'])

    # Выполняем обновление в базе данных
    await orm_update_friend(session, friend_id, new_data)

    await message.answer('Данные друга успешно обновлены.')
    await state.clear()


# Добавляем состояния для удаления записи друга
class DeleteFriend(StatesGroup):
    """Описывает состояния пользователя в процессе
    удаления записи друга из БД."""
    select_friend = State()
    make_sure = State()

# Реализация команды удаления записи друга
@router.message(Command('delete'))
async def delete_friend_start(message: Message, state: FSMContext, session: AsyncSession):
    """Начало процесса удаления друга из БД."""
    # получаем id текущего пользователя
    db_id = await orm_get_user_db_id(session, message)
    # получаем список его друзей, связанных с его id
    friends = await orm_get_all_my_friends(session, db_id)

    # если у пользователя ещё нет друзей в БД
    if not friends:
        # то отпрвить сообщение пользователю
        await message.answer('У вас пока нет друзей в Базе Данных.')
        return

    # Формируем список друзей для пользователя, чтобы он мог выбрать
    # id того друга, которого нужно удалить из БД
    friends_list = "\n".join(
        [f'ID: {friend.id}, Имя: {friend.full_name}' for friend in friends]
    )

    # теперь отправим пользователю список его друзей
    # и сообщение, чтобы выбрал нужный id и направил его нам
    await message.answer(f'Выберите ID друга для удаления:\n{friends_list}')
    # установим состояние select_friend
    await state.set_state(DeleteFriend.select_friend)

# теперь бот ожидает id
@router.message(DeleteFriend.select_friend)
async def delete_friend_select(message: Message, state: FSMContext, session: AsyncSession):
    """Удаление выбранного друга по ID."""

    # проверим, что друг с таким ID есть в БД
    try:
        friend_id = int(message.text)
        friend = await orm_get_friend(session, friend_id)
        # если такого друга нет в БД, вернём ошибку
        if not friend:
            raise ValueError

        # Выводим имя друга для пользователя, чтобы он убедился в правильности выбора
        await state.update_data(friend_id=friend_id)  # Сохраняем friend_id в состояние, чтобы использовать его позже при подтверждении удаления
        await message.answer(f'Вы удаляете друга: {friend.full_name}\n'
                            f'Чтобы подтвердить удаление, отправьте "."\n'
                            f'Чтобы отменить удалени, отправьте "!"'
                            )
        # Назначаем новое сотояние
        await state.set_state(DeleteFriend.make_sure)
    except ValueError:
        await message.answer('Пожалуйста, введите корректный ID из списка.')

# теперь бот ожидает или подтверждение удаления "."
# или отмену удаления "!"
@router.message(DeleteFriend.make_sure)
async def delete_friend_make_sure(message: Message, state: FSMContext, session: AsyncSession):
    # ответ пользователя
    answer = message.text
    # получаем данные из состояния
    data = await state.get_data()
    friend_id = data.get('friend_id')
    # проведём проверку
    if answer == "!":
        await message.answer(f'Удаление отменено.')
    elif answer == ".":
        await orm_delete_friend(session, friend_id)
        await message.answer(
            f'Пользователь с ID: {friend_id} успешно удалён из БД.'
            )
    else:
        await message.answer(
            f'Пожалуйста, отправьте "." для подтверждения удаления'
            f' или "!" для отмены.'
            )









# apsch_send_message_middleware_cron,
#         trigger='cron',
#         hour=datetime.now().hour,  # текущий час hour=datetime.now().hour
#         minute=datetime.now().minute + 1,  # запустится через 1 минуту
#         second=datetime.now().second + 1,  # запустится через 1 секунду
#         start_date=datetime.now(),  # задача начнёт выполнятся начиная с сегодня
#         kwargs={'bot': bot, 'chat_id': chat_id, 'message': message, 'session': session}
