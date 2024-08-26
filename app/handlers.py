from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


import app.keyboards as kb
from database.models import Friend, User
from database.orm_requests import orm_reg_user

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    # если из БД из модели Юзер нельзя извлечь из столбца tg_id id текущего юзера
    query = select(User).where(User.tg_id == message.from_user.id)
    result = await session.execute(query)
    if not result:
        await message.reply(
        f'Здравствуйте, я BirthdayBot!\n'
        f'Чтобы начать пользоваться сервисом,\n'
        f'пройдите регистрацию, нажав на кнопку',
        reply_markup=kb.reg_button
    )
    await message.reply(f'Здравствуйте, {????}\n')


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
    # записываем данные в БД
    await orm_reg_user(session, data)
    # выводим данные в сообщении, чтобы легче проверить правильность ввода
    await message.reply(
        f'Ваш ID: {data['telegram_id']},\n'
        f'Имя: {data['username']}'
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
    data['userid'] = message.from_user.id
    # теперь вся сохранённая инф хранится в виде словаря,
    # эту информацию можно за один раз отправить в БД и
    # создать новую запись о новом пользователе
    obj = Friend(
        full_name = data['fullname'],
        date_month = data['datemonth'],
        birth_year = data['birthyear'],
    # each user has personal list of friends,
    # total list is filtered by user`s id
        user_id = data['userid']
    )
    # теперь отправим пользователю сообщение
    await message.answer(f'Спасибо, запись добавлена.\n'
                         f'Полное имя: {data['fullname']},\n'
                         f'Число и месяц рождения: {data['datemonth']},\n'
                         f'Год рождения: {data['birthyear']}.\n'
                         f'Ваш id в системе: {data['userid']}'
                         )
    # очистим состояние, чтобы не засорять кэш бота
    await state.clear()


@router.message(Command('help'))
async def get_help(message: Message, session: AsyncSession):
    # если из БД из модели Юзер нельзя извлечь из столбца tg_id id текущего юзера
    query = select(User).where(User.tg_id == message.from_user.id)
    result = await session.execute(query)
    if not result:
        await message.reply(f'Вы не зарегистрированы\n')
    await message.reply(f'Вы зарегистрированы\n')