import asyncio
import io
import json
import logging
import signal

import websockets
import PIL.Image as Image
from aiogram import Bot
from aiogram.types import InputFile

from db_api import db


class WebSocketServer:

    def __init__(self, port: int, host: str, bot: Bot):
        self.port = port
        self.host = host
        self.connected_sockets = []
        self.bot = bot
        self.safe_mode = False

    async def handle_updates(self, websocket):
        current_script = await db.select_script(iscurrent=True)
        logging.info(current_script)
        self.connected_sockets.append(websocket)
        await websocket.send(str(self.safe_mode))
        await websocket.send(json.dumps(current_script))
        try:
            async for message in websocket:
                if type(message) == str:
                    self.state = json.loads(message)
                    return
                admins = [int(i.get("telegram_id")) for i in await db.select_users()]
                for i in admins:
                    photo = InputFile(path_or_bytesio=io.BytesIO(message))
                    await self.bot.send_photo(chat_id=i, photo=photo)
        except websockets.ConnectionClosed as e:
            print("Connection with socket was closed")

    async def send_script(self, data):
        if len(self.connected_sockets) > 0:
            for i in self.connected_sockets:
                try:
                    if type(data) == bool:
                        await i.send(str(data))
                    else:
                        await i.send(json.dumps(data))
                except Exception as e:
                    continue

    async def start_listening(self):
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

        async with websockets.serve(
            self.handle_updates,
            host="",
            port=80,
        ):
            await stop