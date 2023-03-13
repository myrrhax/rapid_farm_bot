import json
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData 
from db_api import db

navigation_cd = CallbackData('nav', 'level', 'script_id', 'interval_id')
interval_cd = CallbackData('int', 'script_id', 'interval_id', 'min_wet', 'max_wet', 'light', 'w_interval', 'days')

'''
    start: 0,
    help: 1,
    state: 2,
    admin: 3,
    scripts: 4, <-> script: 5 <-> interval: 6
'''

levels = {
    'start': 0,
    'help': 1,
    'state': 2,
    'admin': 3,
    'scripts': 4,
    'script': 5,
    'interval': 6,
    'delete_script': 7,
    'add_script': 8,
    'delete_interval': 9,
    'add_interval': 10
}

def make_callback_data(level: int, script_id=0, interval_id=0):
    return navigation_cd.new(level=level, script_id=script_id, interval_id=interval_id)

def make_interval_data(script_id:int, interval_id:int, min_wet: int, max_wet: int, light: int, w_interval: int, days: int):
    return interval_cd.new(script_id=script_id, interval_id=interval_id, min_wet=min_wet, max_wet=max_wet, light=light, w_interval=w_interval, days=days)

def get_zero_level_kb(is_admin: bool) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton("Состояние", callback_data=make_callback_data(levels['state'])),
        ],
    ]
    if (is_admin):
        kb[0].append(InlineKeyboardButton('Сценарии', callback_data=make_callback_data(levels['scripts'])))
        kb.append([InlineKeyboardButton('Администрирование', callback_data=make_callback_data(levels['admin']))])

    kb.append([InlineKeyboardButton('Помощь', callback_data=make_callback_data(levels['help']))])

    return InlineKeyboardMarkup(inline_keyboard=kb)

async def get_scripts_kb() -> InlineKeyboardMarkup:
    scripts = await db.select_scripts()
    kb = []
    for i in scripts:
        kb.append([
            InlineKeyboardButton(text=f'{i.get("name")}', 
                                 callback_data=make_callback_data(level=levels.get('script'),
                                                                  script_id=i.get('id'))),
            InlineKeyboardButton(text='X', 
                                 callback_data=make_callback_data(level=levels.get('delete_script'),
                                                                  script_id=i.get('id')))
        ])
    
    kb.append([InlineKeyboardButton(text='Добавить сценарий', 
                                    callback_data=make_callback_data(level=levels.get('add_script')))])
    kb.append([InlineKeyboardButton(
        text="<<<",
        callback_data=make_callback_data(level=levels.get('start'))
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)


async def script_kb(script: dict):
    script_id = script.get('id')
    intervals = json.loads(script.get('intervals_json'))
    kb = []
    for i in range(0, len(intervals)):
        kb.append([InlineKeyboardButton(
            text=f'Интервал {i+1}',
            callback_data=make_callback_data(level=levels.get('interval'), script_id=script_id, interval_id=i)
        ),
        InlineKeyboardButton(
            text="X",
            callback_data=make_callback_data(level=levels['delete_interval'], script_id=script_id, interval_id=i)
        )])

    kb.append([
        InlineKeyboardButton(
            text='Добавить интервал',
            callback_data=make_callback_data(level=levels['add_interval'], script_id=script_id)
        )
        ])
    kb.append([InlineKeyboardButton(text='<<<', callback_data=make_callback_data(level=levels.get('scripts')))])
    return InlineKeyboardMarkup(inline_keyboard=kb)


async def interval_info_kb(script_id: int, interval_id: int) -> InlineKeyboardMarkup:
    script = await db.select_script(id=script_id)
    intervals = json.loads(script.get('intervals_json'))
    interval = dict(intervals[int(interval_id)])

    min_wet = interval.get('min_wet')
    max_wet = interval.get('max_wet')
    light = interval.get('light')
    w_interval = interval.get('w_interval')
    days = interval.get('days')

    kb = [
        [
            InlineKeyboardButton('Влажность: ', callback_data='ignore')
        ],
        [
            InlineKeyboardButton('Мин', callback_data='ignore'),
            InlineKeyboardButton('+', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id, min_wet=min_wet+10, max_wet=max_wet, light=light, w_interval=w_interval, days=days)),
            InlineKeyboardButton(min_wet, 
                                 callback_data='ignore'),
            InlineKeyboardButton('-', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet-10, max_wet=max_wet, light=light, w_interval=w_interval, days=days))  
        ],
        [
            InlineKeyboardButton('Макс', callback_data='ignore'),
            InlineKeyboardButton('+', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet+10, light=light, w_interval=w_interval, days=days)),
            InlineKeyboardButton(max_wet, callback_data='ignore'),
            InlineKeyboardButton('-', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet-10, light=light, w_interval=w_interval, days=days))  
        ],
        [
            InlineKeyboardButton('Свет', callback_data='ignore'),
        ],
        [
            InlineKeyboardButton('+', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet, light=light+1000, w_interval=w_interval, days=days)),
            InlineKeyboardButton(int(interval.get('light')), callback_data='ignore'),
            InlineKeyboardButton('-', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet, light=light-1000, w_interval=w_interval, days=days))
        ],
        [
            InlineKeyboardButton('Интервал полива(часы)', callback_data='ignore'),
        ],
        [
            InlineKeyboardButton('+', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet, light=light, w_interval=w_interval+12*60*60, days=days)),
            InlineKeyboardButton(int(interval.get('w_interval') / (60 * 60)), callback_data='ignore'),
            InlineKeyboardButton('-', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet, light=light, w_interval=w_interval-12*60*60, days=days))
        ],
        [
            InlineKeyboardButton('Рабочих дней', callback_data='ignore'),
        ],
        [
            InlineKeyboardButton('+', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet, light=light, w_interval=w_interval, days=days+1)),
            InlineKeyboardButton(interval.get('days'), callback_data='ignore'),
            InlineKeyboardButton('-', callback_data=make_interval_data(script_id=script_id, interval_id=interval_id,min_wet=min_wet, max_wet=max_wet, light=light, w_interval=w_interval, days=days-1))
        ],
        [
            InlineKeyboardButton('<<<', callback_data=make_callback_data(level=levels['script'], script_id=script_id))
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)