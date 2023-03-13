from typing import *
from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import Update
from db_api import db

class AdminFilter(BaseFilter):
    async def __call__(self, update: Update) -> Union[bool, Dict[str, Any]]:
        users = list(await db.select_users())
        users_id = [dict(i).get("telegram_id") for i in users]
        return update.from_user.id in users_id