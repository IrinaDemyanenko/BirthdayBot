from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import Message

from database.models import User


async def orm_reg_user(session: AsyncSession, data: dict):
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


#async def orm_add_friend(session: AsyncSession, data: dict):
    #"""Stores data in the database at the table 'friends'."""

