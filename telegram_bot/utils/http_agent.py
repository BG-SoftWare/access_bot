from multiprocessing import Process
import time

import uvicorn
from fastapi import FastAPI, Request, Response
from utils.database_connector import DatabaseConnector

from telegram_bot.config import (
    DB_CONNECTION_STRING,
    APP_ID_HEADER,
    BLOCKED_RESPONSE,
    OK_RESPONSE,
    LISTEN_HOST,
    LISTEN_PORT
)


class HTTPAgent:
    app = FastAPI()
    db = DatabaseConnector(DB_CONNECTION_STRING)

    def __init__(self):
        @self.app.get("/")
        async def verify_app(request: Request):
            header = request.headers.get(APP_ID_HEADER)
            if header is None:
                return Response(BLOCKED_RESPONSE)
            else:
                if await self.db.check_or_create_bundle(header):
                    return Response(OK_RESPONSE)
                else:
                    return Response(BLOCKED_RESPONSE)

        self.server = Process(target=uvicorn.run, kwargs={"app": self.app, "host": LISTEN_HOST, "port": LISTEN_PORT})
        self.server.start()


if __name__ == "__main__":
    HTTPAgent()
    while True:
        time.sleep(1)
