from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery


router = Router()

class Add_relative(StatesGroup):
    """Describes user`s states during registration."""
    full_name = State()
    date_month = State()
    birth_year = State()

# после команды /add начнётся регистрация нового пользователя
@router.message(Command('add'))
async def add_first(message: Message, state: FSMContext):
    await state.set_state(Add_relative.full_name)
    await message.answer(f'Введите польное имя и фамилию человека,
                          и я напомню Вам о его Дне Рождения!')

@router.message(Add_relative.full_name)
async def add_second(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await state.set_state(Add_relative.date_month)
    await message.answer(f'Введите дату рождения и месяц в формате: 01.01')

@router.message(Add_relative.date_month)
async def add_third(message: Message, state: FSMContext):
    await state.update_data(datemonth=message.text)
    await state.set_state(Add_relative.birth_year)
    await message.answer(f'Введите год рождения в формате: 1965')

@router.message(Add_relative.birth_year)
async def add_fourth(message: Message, state: FSMContext):
    await state.update_data(birthyear=message.text)
    data = await state.get_data
    # теперь вся сохранённая инф хранится в виде словаря,
    # эту информацию можно за один раз отправить в БД и
    # создать новую запись о новом пользователе
    # теперь отправим пользователю сообщение
    await message.answer(f'''Спасибо, запись добавлена.\n
                         Полное имя: {data['full_name']}\n
                         Число и месяц рождения: {data['date_month']},
                         Год рождения: {data['birth_year']}
                         '''
                         )
    # очистим состояние, чтобы не засорять кэш бота
    await state.clear()
