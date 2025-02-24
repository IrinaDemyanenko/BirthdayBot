from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (AsyncAttrs,
                                    async_sessionmaker,
                                    create_async_engine
                                    )
from config import db_username, db_localhost, db_password, yourdbname
# creates DB
# echo=True to show info in terminal
# sqlite Database Management System, DBMS - СУБД
# aiosqlite driver
# birthdaybot.db name
#engine = create_async_engine(url='sqlite+aiosqlite:///birthdaybot.db', echo=True)

DATABASE_URL = f'postgresql+asyncpg://{db_username}:{db_password}@{db_localhost}:5432/{yourdbname}'

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

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
    tg_id = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    #chat_id: Mapped[int] = mapped_column()  # для автосообщений от бота
    # нашла инф что chat.id конкретному пользователю равен id этого пользователя


class Friend(Base):
    """Information about relatives and friends."""

    __tablename__ = 'friends'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_month: Mapped[str] = mapped_column(String(50), nullable=False)
    birth_year: Mapped[int] = mapped_column()
    # each user has personal list of friends,
    # total list is filtered by user`s id
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'), nullable=False)
    notify_week_before: Mapped[bool] = mapped_column(Boolean, default=False)


# let`s create all the tables
# с помощью контекстного менеджера, через engine начать сессию
# и создать новую переменную conn; используя это подключение,
# запустить синхронизацию, в которую передадим основной класс Base,
# где, в метаданных, хранятся все дочерние классы (т.е. наши таблиицы);
# создаём эти классы-таблицы
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



# to delete all the tables at db
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
