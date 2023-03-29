import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config_loader import config
from db_api import db
from handlers.navigation import register_menu
from handlers.start import register_start
from ws_api import WebSocketServer


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    storage = MemoryStorage()
    bot = Bot(config.bot_token.get_secret_value(), parse_mode="HTML")
    wss = WebSocketServer(host='', port=32080, bot=bot)
    dp = Dispatcher(bot, storage=storage)
    bot['wss'] = wss

    register_start(dp)
    register_menu(dp)

    await db.create_table_users()
    await db.create_scripts_table()

    await dp.skip_updates()
    tasks = [dp.start_polling(), wss.start_listening()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())