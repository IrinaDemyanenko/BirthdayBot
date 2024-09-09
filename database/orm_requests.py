from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import Message

from database.models import Friend, User

from app.variables import today_date_month


async def orm_reg_user(session: AsyncSession, data: dict) -> None:
    """Stores data in the database at the table 'users'."""
    # создаём объект
    obj = User(
        tg_id = data['telegram_id'],
        full_name = data['username'],
    )
    # добавляем данные из словаря в таблицу в БД
    session.add(obj)
    # фиксируем изменения в БД
    await session.commit()


async def orm_get_user_full_name(session: AsyncSession, message: Message):
    query_name = select(User.full_name).where(User.tg_id == message.from_user.id)
    return await session.scalar(query_name)
    # scalar возвращает значение _ одно, scalars - несколько


async def orm_check_user_exists(session: AsyncSession, message: Message):
    # извлечь из столбца tg_id id текущего юзера
    query = select(User).where(User.tg_id == message.from_user.id)
    return await session.scalar(query)


async def orm_get_user_db_id(session: AsyncSession, message: Message):
    user = select(User.id).where(User.tg_id == message.from_user.id)
    return await session.scalar(user)


async def orm_add_new_friend(session: AsyncSession, data: dict) -> None:
    # создаём объект
    obj = Friend(
        full_name = data['fullname'],
        date_month = data['datemonth'],
        birth_year = data['birthyear'],
    # each user has personal list of friends,
    # total list is filtered by user`s id
        user_id = data['userid']
    )
    # добавляем данные из словаря в таблицу в БД
    session.add(obj)
    # фиксируем изменения в БД
    await session.commit()


async def orm_check_birthday(session: AsyncSession, db_id: int):
    # today_date_month - переменная, сегодняшее число и месяц
    # найти в таблице friends строки где число и дата совпадают
    # с сегодняшним днём, а user_id == db_id того, кто отправил сообщение
    query = select(Friend).where(Friend.date_month == today_date_month).where(Friend.user_id == db_id)
    # таких людей может быть несколько
    # запрос возвращает целые строки со всем сожержимым
    return await session.scalars(query)


async def orm_get_all_my_friends(session: AsyncSession, db_id: int):
    """Получить весь список всех друзей."""
    query = select(Friend).where(Friend.user_id == db_id)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_friend(session: AsyncSession, id: int):
    """Получить одного друга по id."""
    query = select(Friend).where(Friend.id == id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_friend(session: AsyncSession, id: int, data: dict):
    """Изменить данные одного друга по id."""
    query = update(Friend).where(Friend.id == id).values(
        full_name = data['fullname'],
        date_month = data['datemonth'],
        birth_year = data['birthyear'],
    # each user has personal list of friends,
    # total list is filtered by user`s id
        user_id = data['userid']
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_friend(session: AsyncSession, id: int):
    """Удалить друга из БД."""
    query = delete(Friend).where(Friend.id == id)
    await session.execute(query)
    await session.commit()

