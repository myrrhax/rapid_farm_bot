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
        self.state = ''
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

    def get_current_state(self):
        return self.state

"""
import asyncio
import http
import logging
import signal
import sys
import time

import websockets


async def slow_echo(websocket):
    async for message in websocket:
        # Block the event loop! This allows saturating a single asyncio
        # process without opening an impractical number of connections.
        time.sleep(0.1)  # 100ms
        logging.info(message)
        await websocket.send(message)


async def health_check(path, request_headers):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"
    if path == "/inemuri":
        loop = asyncio.get_running_loop()
        loop.call_later(1, time.sleep, 10)
        return http.HTTPStatus.OK, [], b"Sleeping for 10s\n"
    if path == "/seppuku":
        loop = asyncio.get_running_loop()
        loop.call_later(1, sys.exit, 69)
        return http.HTTPStatus.OK, [], b"Terminating\n"


async def main():
    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with websockets.serve(
        slow_echo,
        host="",
        port=80,
        process_request=health_check,
    ):
        await stop


if __name__ == "__main__":
    asyncio.run(main())


"""