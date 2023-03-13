import json
from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.menu_keyboards import make_callback_data, levels, get_zero_level_kb, navigation_cd, get_scripts_kb, script_kb, interval_info_kb, interval_cd
from db_api import db 
from aiogram.utils.deep_linking import get_start_link
from config_loader import config
from aiogram.dispatcher import FSMContext
from states.dialog_state import DialogState
import websockets

async def back_to_start(call: CallbackQuery, **kwargs):
    is_admin = call.from_user.id in [i.get('telegram_id') for i in await db.select_users()]
    await call.message.edit_text(f'Здравствуйте, {call.from_user.get_mention(as_html=True)}. Вот, что я умею: ', 
                                                  reply_markup=get_zero_level_kb(is_admin))

async def help(call: CallbackQuery, **kwargs):
    await call.message.edit_text("Данный бот разработан студентами ИОТ ШКОЛА ИКС",
                                 reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='Назад', callback_data=make_callback_data(levels['start']))
                                        ]
                                    ]
                                 ))
    

async def admin(call: CallbackQuery, **kwargs):
    link = await get_start_link(config.admin_link_payload.get_secret_value())
    await call.message.edit_text(f"Для получения полных возможностей бота, пользователь должен перейти по данной ссылке: {link}",
                                 reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='Назад', callback_data=make_callback_data(levels['start']))
                                        ]
                                    ]
                                 ))
    

async def scripts(call: CallbackQuery, **kwargs):
    await call.message.edit_text(text='Сценарии позволяют более гибко настроить вашу ферму',
                                 reply_markup=await get_scripts_kb())

async def add_script(call: CallbackQuery, state: FSMContext, **kwargs):
    await call.message.edit_text("Введите название нового сценария: ")
    await state.set_state(DialogState.enter_name)

async def enter_name(message: Message, state: FSMContext):
    name = message.text
    await state.finish()
    try:
        await db.add_script(name, json.dumps([]))
        await message.answer(text='Сценарии позволяют более гибко настроить вашу ферму',
                                            reply_markup=await get_scripts_kb())
    except Exception as e:
        await message.answer(e)

async def script_info(call: CallbackQuery, script_id: int, **kwargs):
    script = await db.select_script(id=int(script_id))
    await call.message.edit_text(text=f'Информация о сценарии {script.get("name")}',
                                 reply_markup=await script_kb(script=script))
    
async def delete_script(call: CallbackQuery, script_id: int, **kwargs):
    await db.delete_script(id=int(script_id))
    await call.message.edit_text(text='Сценарии позволяют более гибко настроить вашу ферму',
                                            reply_markup=await get_scripts_kb())
    
async def interval_info(call: CallbackQuery, script_id: int, interval_id: int, **kwargs):
    await call.message.edit_text("Информация об интервале", 
                                 reply_markup=await interval_info_kb(script_id, interval_id))

async def add_interval(call: CallbackQuery, script_id: int, **kwargs):
    script = await db.select_script(id=script_id)
    intervals: list[dict] = json.loads(script.get('intervals_json'))
    default_settings = {'min_wet': 30, 'max_wet': 70, 'light': 3000, 'w_interval':  24 * 60 * 60,
                        'days': 15}
    intervals.append(default_settings)
    await db.update_script(id=script_id, intervals_json=json.dumps(intervals))
    await call.message.edit_text(text=f'Информация о сценарии {script.get("name")}',
                                 reply_markup=await script_kb(script=await db.select_script(id=script_id)))

async def delete_interval(call: CallbackQuery, script_id: int, interval_id: int, **kwargs):
    script = await db.select_script(id=script_id)
    intervals: list[dict] = json.loads(script.get('intervals_json'))
    del intervals[interval_id]
    await db.update_script(id=script_id, intervals_json=json.dumps(intervals))
    await call.message.edit_text(text=f'Информация о сценарии {script.get("name")}',
                                 reply_markup=await script_kb(script=await db.select_script(id=script_id)))

async def on_interval_changes(call: CallbackQuery, callback_data: dict):
    script = await db.select_script(id=int(callback_data.get('script_id')))
    if script is None:
        await call.message.edit_text(text='Сценарии позволяют более гибко настроить вашу ферму',
                                 reply_markup=await get_scripts_kb())
        return
    intervals:list = json.loads(script.get('intervals_json'))
    interval:dict = intervals[int(callback_data.get('interval_id'))]

    min_wet = int(callback_data.get('min_wet'))
    max_wet = int(callback_data.get('max_wet'))
    light = int(callback_data.get('light'))
    w_interval = int(callback_data.get('w_interval'))
    days = int(callback_data.get('days'))


    interval.update(
        {
            'min_wet': min_wet if (min_wet >= 20 and min_wet <= 60) and (min_wet != max_wet) else int(interval.get('min_wet')),
            'max_wet': max_wet if (max_wet >= 60 and max_wet <= 80) and (max_wet != min_wet) else int(interval.get('max_wet')),
            'light': light if light >= 1000 and light <= 5000 else int(interval.get('light')),
            'w_interval': w_interval if w_interval > 12 else int(interval.get('w_interval')),
            'days': days if days > 0 else interval.get('days')
        })
    await db.update_script(id=int(script.get('id')), intervals_json=json.dumps(intervals))
    try:
        await call.message.edit_reply_markup(reply_markup=await interval_info_kb(script_id=int(script.get('id')), interval_id=callback_data.get('interval_id')))
    except Exception as e:
        await call.answer()

async def state_check(call: CallbackQuery, **kwargs):
    connection = websockets.connect(uri='wss://socketsbay.com/wss/v2/1/demo/')

async def navigate(call: CallbackQuery, state: FSMContext, callback_data: dict):
    level = int(callback_data.get('level'))
    script_id = callback_data.get('script_id')
    interval_id = callback_data.get('interval_id')

    levels_nav =  {
        0: back_to_start,
        1: help,
        2: state_check,
        3: admin,
        4: scripts,
        5: script_info,
        6: interval_info,
        7: delete_script,
        8: add_script,
        9: delete_interval,
        10: add_interval
    }

    callback = levels_nav.get(level)
    await callback(call, state=state, script_id=int(script_id), interval_id=int(interval_id))


def register_menu(dp: Dispatcher):
    dp.register_callback_query_handler(navigate, navigation_cd.filter())
    dp.register_message_handler(enter_name, state=DialogState.enter_name)
    dp.register_callback_query_handler(on_interval_changes, interval_cd.filter())
