import json
import re
from aiogram import Dispatcher
from aiogram.types import Message
from db_api import db
from keyboards.menu_keyboards import get_zero_level_kb
from aiogram.utils.deep_linking import decode_payload
from config_loader import config
from aiogram.dispatcher.filters.builtin import CommandStart

async def start_with_deeplink(message: Message):
    args = message.get_args()
    is_admin = False
    if args == config.admin_link_payload.get_secret_value():
        await db.add_user(message.from_user.id)
        await message.answer('Теперь вам доступен полный функционал бота')
        is_admin = True
        
    
    await message.answer(f'Здравствуйте, {message.from_user.get_mention(as_html=True)}. Вот, что я умею: ', 
                                                  reply_markup=get_zero_level_kb(is_admin))

async def start(message: Message):
    is_admin = message.from_user.id in [i.get('telegram_id') for i in await db.select_users()]
    await message.answer(f'Здравствуйте, {message.from_user.get_mention(as_html=True)}. Вот, что я умею: ', 
                                                  reply_markup=get_zero_level_kb(is_admin))

def register_start(dp: Dispatcher):
    dp.register_message_handler(start_with_deeplink, CommandStart(deep_link=re.compile(r'^([0-9A-Fa-f]{8}[-]?[0-9A-Fa-f]{4}[-]?[0-9A-Fa-f]{4}[-]?[0-9A-Fa-f]{4}[-]?[0-9A-Fa-f]{12})$')))
    dp.register_message_handler(start, commands=['start'])
