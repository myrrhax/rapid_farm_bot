import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config_loader import config
from db_api import db
from handlers.navigation import register_menu
from handlers.start import register_start


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    storage = MemoryStorage()
    bot = Bot(config.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)
    
    register_start(dp)
    register_menu(dp)

    await db.create_table_users()
    await db.create_scripts_table()

    await dp.skip_updates()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())