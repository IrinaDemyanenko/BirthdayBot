from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types.base import TelegramObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
    
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        # в словарь с данными хэндлера добавляем объект apscheduler
        # и обновляем данные о хэндлере с помощью return handler
        data['apscheduler'] = self.scheduler
        return await handler(event, data)
        # теперь по параметру scheduler (как message, state) будет
        # доступен шедуляр(расписание задач);
        # подключим к основному роутеру, хотя можно и к любому второстепенному роутеру

