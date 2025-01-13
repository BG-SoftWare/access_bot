import asyncio
import logging
import math
import sys
import uuid
from datetime import datetime

import jwt
from aiogram import Bot, Dispatcher, F, Router, Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQuery
)
from pytz import timezone

from config import *
from telegram_bot.strings import (
    ENTER_LOGIN_PROMPT,
    LOGIN_MUST_BE_TEXT_PROMPT,
    ENTER_PASSWORD_PROMPT,
    PASSWORD_MUST_BE_TEXT_PROMPT,
    AUTH_FAILURE_PROMPT,
    MAIN_PAGE_PROMPT,
    EDIT_TEXT_TRIGGER,
    BUNDLE_EXECUTION_ALLOWED_PROMPT,
    BUNDLE_INFO,
    BUNDLE_EXECUTION_DENIED_PROMPT,
    BUNDLE_NOT_FOUND_PROMPT,
    BUNDLES_LIST_PROMPT,
    NO_BUNDLES_PROMPT,
    IS_NO_PAGE_ALERT,
    BUNDLE_REMOVED_PROMPT,
    LOGOUT_PROMPT,
    ONLY_CHAT_WITH_BOT_SUPPORT,
    ACCESS_DENIED_PLEASE_RELOGIN_PROMPT_INLINE,
    NOT_FOUND_INLINE, EDIT_INLINE_PROMPT
)
from utils.auth_wrapper import *
from utils.database_connector import DatabaseConnector
from utils.http_agent import HTTPAgent
from utils.markups import *

database = DatabaseConnector(DB_CONNECTION_STRING)
form_router = Router()

__ttl = 365 * 24 * 60 * 60

redis_storage = RedisStorage.from_url(REDIS_CONNECTION_STRING, data_ttl=__ttl, state_ttl=__ttl)

bot = Bot(token=TELEGRAM_API_KEY)
dispatcher = Dispatcher(storage=redis_storage)
dispatcher.include_router(form_router)


class Login(StatesGroup):
    login = State()
    password = State()


class MainMenu(StatesGroup):
    main_page = State()


@form_router.message(CommandStart())
async def login_page(message: Message, state: FSMContext) -> None:
    await state.set_state(Login.login)
    await message.answer(ENTER_LOGIN_PROMPT, reply_markup=ReplyKeyboardRemove())


@form_router.message(Login.login)
async def password_page(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer(LOGIN_MUST_BE_TEXT_PROMPT)
        return

    await state.update_data(login=message.text)
    await state.update_data(login_msg_id=message.message_id)
    await state.set_state(Login.password)
    await message.answer(ENTER_PASSWORD_PROMPT)


@form_router.message(Login.password)
async def password_verify(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text is None:
        await message.answer(PASSWORD_MUST_BE_TEXT_PROMPT)
        return None

    if await database.validate_user(data["login"], message.text):
        await state.update_data(
            jwt_key=jwt.encode(
                {"valid_until": int(time.time()) + int(getenv("JWT_TTL_SECONDS"))},
                getenv("JWT_KEY"),
                "HS256"
            )
        )
        await main_menu(message, state)
        await bot.delete_messages(message.chat.id, [data["login_msg_id"], message.message_id])
    else:
        await message.answer(AUTH_FAILURE_PROMPT)
        await login_page(message, state)


async def main_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(MainMenu.main_page)
    await message.answer(
        MAIN_PAGE_PROMPT.format(nickname=(await bot.me()).username),
        reply_markup=main_screen_keyboard_markup(),
    )


@form_router.message(MainMenu.main_page, F.text.startswith(EDIT_TEXT_TRIGGER))
@check_auth(on_auth_fail=check_auth)
async def jump_to_edit(message: Message, state: FSMContext) -> None:
    bundle_name = message.text.split(" ")[1]
    try:
        bundle_status, last_access = await database.get_bundle_info(bundle_name)
        bundle_status_text = BUNDLE_EXECUTION_ALLOWED_PROMPT if bundle_status else BUNDLE_EXECUTION_DENIED_PROMPT
        await message.answer(
            text=BUNDLE_INFO.format(
                bundle_name=bundle_name,
                bundle_status=bundle_status_text,
                last_access=datetime.fromtimestamp(last_access, tz=timezone(TIMEZONE)).strftime("%d/%m/%Y, %H:%M:%S")
            ),
            reply_markup=edit_bundle_inline_markup(bundle_name, bundle_status)
        )
    except Exception:  # noqa
        await message.answer(BUNDLE_NOT_FOUND_PROMPT)
        await main_menu(message, state)


@form_router.message(MainMenu.main_page, F.text == BUNDLES_LIST_BUTTON)
@check_auth(on_auth_fail=check_auth)
async def init_list_bundles(message: Message, state: FSMContext) -> None:
    limit = APPS_ON_PAGE
    count_rows, bundles = await database.get_bundles_list(limit, 0)
    pages = math.ceil(count_rows / limit)
    payload_for_inline_widget = []

    if count_rows > 0:
        for bundle in bundles:
            status = "✅" if bundle[1] else "❌"
            payload_for_inline_widget.append(
                {
                    "text": f"{status} - {bundle[0]}",
                    "callback_data": f"control_bundle@{bundle[0]}"
                }
            )

        await message.answer(
            BUNDLES_LIST_PROMPT,
            reply_markup=generate_inline_buttons_with_pagination(payload_for_inline_widget, 0, pages, "view_apps")[0]
        )
    else:
        await message.answer(NO_BUNDLES_PROMPT)


@form_router.callback_query(MainMenu.main_page, F.data.startswith("control_bundle"))
@check_auth(on_auth_fail=check_auth)
async def control_bundle(call: CallbackQuery, state: FSMContext) -> None:
    bundle_status, last_access = await database.get_bundle_info(call.data.split("@")[1])
    bundle_status_text = BUNDLE_EXECUTION_ALLOWED_PROMPT if bundle_status else BUNDLE_EXECUTION_DENIED_PROMPT

    await call.message.edit_text(
        text=BUNDLE_INFO.format(
            bundle_name=call.data.split("@")[1],
            bundle_status=bundle_status_text,
            last_access=datetime.fromtimestamp(last_access, tz=timezone(TIMEZONE)).strftime("%d/%m/%Y, %H:%M:%S")
        ),
        reply_markup=edit_bundle_inline_markup(call.data.split("@")[1], bundle_status)
    )


@form_router.callback_query(MainMenu.main_page, F.data.startswith("view_apps"))
@check_auth(on_auth_fail=check_auth)
async def init_control_app(call: CallbackQuery, state: FSMContext) -> None:
    page = int(call.data.split("@")[1])
    offset = page * APPS_ON_PAGE
    count_rows, bundles = await database.get_bundles_list(APPS_ON_PAGE, offset)
    pages = math.ceil(count_rows / APPS_ON_PAGE)
    payload_for_inline_widget = []

    for bundle in bundles:
        status = "✅" if bundle[1] else "❌"
        payload_for_inline_widget.append({
            "text": f"{status} - {bundle[0]}",
            "callback_data": f"control_bundle@{bundle[0]}"
        })
    new_markup = generate_inline_buttons_with_pagination(payload_for_inline_widget, page, pages, "view_apps")[0]

    if len(call.message.reply_markup.inline_keyboard[-1]) == 3:
        if new_markup.inline_keyboard[-1][1].text == call.message.reply_markup.inline_keyboard[-1][1].text:
            await call.answer(IS_NO_PAGE_ALERT)
        else:
            await call.message.edit_reply_markup(reply_markup=new_markup)
    else:
        await call.message.edit_text(BUNDLES_LIST_PROMPT, reply_markup=new_markup)


@form_router.callback_query(MainMenu.main_page, F.data.startswith("block_bundle"))
@check_auth(on_auth_fail=check_auth)
async def block_app(call: CallbackQuery, state: FSMContext) -> None:
    bundle_id = call.data.split("@")[1]
    await database.change_execution_for_bundle(bundle_id, False)
    await control_bundle(call, state)


@form_router.callback_query(MainMenu.main_page, F.data.startswith("allow_bundle"))
@check_auth(on_auth_fail=check_auth)
async def allow_app(call: CallbackQuery, state: FSMContext) -> None:
    bundle_id = call.data.split("@")[1]
    await database.change_execution_for_bundle(bundle_id, True)
    await control_bundle(call, state)


@form_router.callback_query(MainMenu.main_page, F.data.startswith("remove_bundle"))
@check_auth(on_auth_fail=check_auth)
async def remove_app(call: CallbackQuery, state: FSMContext) -> None:
    bundle_id = call.data.split("@")[1]
    await database.remove_bundle(bundle_id)
    await call.message.edit_text(BUNDLE_REMOVED_PROMPT)
    await init_list_bundles(call.message, state)


@form_router.message(MainMenu.main_page, F.text == LOGOUT_BUTTON)
@check_auth(on_auth_fail=check_auth)
async def init_logout(message: Message, state: FSMContext) -> None:
    await state.update_data(jwt_key="")
    await message.answer(LOGOUT_PROMPT, reply_markup=ReplyKeyboardRemove())
    await login_page(message, state)


@form_router.message(Command("cancel"))
@check_auth(on_auth_fail=check_auth)
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return None

    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.inline_query()
async def inline_echo(inline_query: InlineQuery) -> None:
    if inline_query.chat_type != "sender":
        result_id = str(uuid.uuid4())
        item = InlineQueryResultArticle(
            id=result_id,
            title=ONLY_CHAT_WITH_BOT_SUPPORT,
            input_message_content=InputTextMessageContent(message_text="Nope"),
        )
        await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)

    else:
        data = await dispatcher.storage.get_data(StorageKey(bot.id, inline_query.from_user.id, inline_query.from_user.id))

        try:
            if "jwt_key" not in data:
                result_id = str(uuid.uuid4())
                item = InlineQueryResultArticle(
                    id=result_id,
                    title=ACCESS_DENIED_PLEASE_RELOGIN_PROMPT_INLINE,
                    input_message_content=InputTextMessageContent(message_text="Nope"),
                )
                await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
            else:
                jwt_data = jwt.decode(data["jwt_key"], key=getenv("JWT_KEY"), algorithms="HS256")
                if jwt_data["valid_until"] > time.time():
                    data = await database.search_by_bundle_id(inline_query.query)
                    if len(data) == 0:
                        result_id = str(uuid.uuid4())
                        item = InlineQueryResultArticle(
                            id=result_id,
                            title=NOT_FOUND_INLINE.format(request=inline_query.query),
                            input_message_content=InputTextMessageContent(message_text="Nope"),
                        )
                        await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
                    else:
                        items = []
                        for row in data:
                            result_id = str(uuid.uuid4())
                            items.append(
                                InlineQueryResultArticle(
                                    id=result_id,
                                    title=EDIT_INLINE_PROMPT.format(bundle=row[0]),
                                    input_message_content=InputTextMessageContent(
                                        message_text=EDIT_INLINE_PROMPT.format(bundle=row[0])),
                                )
                            )
                        await bot.answer_inline_query(inline_query.id, results=items, cache_time=1)
                else:
                    result_id = str(uuid.uuid4())
                    item = InlineQueryResultArticle(
                        id=result_id,
                        title=ACCESS_DENIED_PLEASE_RELOGIN_PROMPT_INLINE,
                        input_message_content=InputTextMessageContent(message_text="Nope"),
                    )
                    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
        except Exception:  # noqa
            result_id = str(uuid.uuid4())
            item = InlineQueryResultArticle(
                id=result_id,
                title=ACCESS_DENIED_PLEASE_RELOGIN_PROMPT_INLINE,
                input_message_content=InputTextMessageContent(message_text="Nope"),
            )
            await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


async def main():
    HTTPAgent()
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    asyncio.run(main())
