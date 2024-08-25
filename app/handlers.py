from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery


import app.keyboards as kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(
        f'Здравствуйте, я BirthdayBot!\n'
        f'Чтобы начать пользоваться сервисом,\n'
        f'пройдите регистрацию, нажав на кнопку',
        reply_markup=kb.reg_button
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
async def reg_user_second(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    data['telegram_id'] = message.from_user.id
    await message.reply(
        f'''Ваш ID: {data['telegram_id']},
        Имя: {data['username']},
        '''
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
async def add_forth(message: Message, state: FSMContext):
    await state.update_data(birthyear=message.text)
    data = await state.get_data()
    # теперь вся сохранённая инф хранится в виде словаря,
    # эту информацию можно за один раз отправить в БД и
    # создать новую запись о новом пользователе
    # теперь отправим пользователю сообщение
    await message.answer(f'Спасибо, запись добавлена.\n'
                         f'Полное имя: {data['fullname']},\n'
                         f'Число и месяц рождения: {data['datemonth']},\n'
                         f'Год рождения: {data['birthyear']}.'
                         )
    # очистим состояние, чтобы не засорять кэш бота
    await state.clear()

