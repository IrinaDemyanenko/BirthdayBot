from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (AsyncAttrs, 
                                    async_sessionmaker,
                                    create_async_engine
                                    )
# creates DB
# echo=True to show info in terminal
# sqlite Database Management System, DBMS - СУБД
# aiosqlite driver
# db.sqlite3 name
engine = create_async_engine(url='sqlite+aiosqlite:///birthdaybot.db', echo=True)

# creates connection
# expire_on_commit=False to reuse session
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    """For easy managment of all the tables."""
    # два поля будут в каждой таблице по умолчанию
    # время создания и время изменения (с автозаполнением)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
        )


class User(Base):
    """Info about users."""

    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    # uniqe telegram user`s number
    tg_id = mapped_column(BigInteger)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)


class Friend(Base):
    """Information about relatives and friends."""

    __tablename__ = 'friends'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_month: Mapped[str] = mapped_column(String(50), nullable=False)
    birth_year: Mapped[int] = mapped_column()
    # each user has personal list of friends,
    # total list is filtered by user`s id
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))


# let`s create all the tables
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# to delete all the tables at db
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)