import time
from os import getenv

import jwt
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from strings import ACCESS_DENIED_PLEASE_RELOGIN_PROMPT


def check_auth(on_auth_fail):
    def check__auth(func):
        async def alert_user_access_denied(*args, **kwargs):
            message, state = args
            if isinstance(message, Message):
                await message.answer(ACCESS_DENIED_PLEASE_RELOGIN_PROMPT, reply_markup=ReplyKeyboardRemove())
            if isinstance(message, CallbackQuery):
                await message.message.answer(ACCESS_DENIED_PLEASE_RELOGIN_PROMPT, reply_markup=ReplyKeyboardRemove())

            await on_auth_fail(args[0], state)

        async def wrapper_func(message, state):
            data = await state.get_data()
            try:
                if "jwt_key" not in data:
                    await alert_user_access_denied(message, state)
                else:
                    jwt_data = jwt.decode(data["jwt_key"], key=getenv("JWT_KEY"), algorithms="HS256")
                    if jwt_data["valid_until"] < time.time():
                        await alert_user_access_denied(message, state)
                    else:
                        await func(message, state)
            except Exception:  # noqa
                pass

        wrapper_func._original = func
        return wrapper_func
    return check__auth