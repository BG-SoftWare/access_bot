from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup

from telegram_bot.strings import (
    BUNDLES_LIST_BUTTON,
    LOGOUT_BUTTON,
    BUNDLE_SWITCH_DENY_BUTTON,
    BUNDLE_SWITCH_ALLOW_BUTTON,
    BUNDLE_REMOVE_BUTTON
)


def main_screen_keyboard_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUNDLES_LIST_BUTTON)],
            [KeyboardButton(text=LOGOUT_BUTTON)]
        ]
    )
    return markup


def edit_bundle_inline_markup(bundle_id: str, switch_from: bool) -> InlineKeyboardMarkup:
    if switch_from:
        switch_to = InlineKeyboardButton(text=BUNDLE_SWITCH_DENY_BUTTON, callback_data=f"block_bundle@{bundle_id}")
    else:
        switch_to = InlineKeyboardButton(text=BUNDLE_SWITCH_ALLOW_BUTTON, callback_data=f"allow_bundle@{bundle_id}")

    back_button = InlineKeyboardButton(text=BUNDLES_LIST_BUTTON, callback_data="view_apps@0")
    remove_bundle = InlineKeyboardButton(text=BUNDLE_REMOVE_BUTTON, callback_data=f"remove_bundle@{bundle_id}")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [switch_to],
            [remove_bundle],
            [back_button]
        ]
    )
    return markup


def generate_inline_buttons_with_pagination(
        items: list,
        page: int = 0,
        max_page: int = 0,
        page_prefix: str = "page_prefix"
) -> tuple[InlineKeyboardMarkup, int]:
    buttons = [InlineKeyboardButton(text=item['text'], callback_data=item['callback_data']) for item in items]
    keyboard = [[button] for button in buttons]

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️" if page > 0 else "❌",
                callback_data=f"{page_prefix}@{page - 1}" if page > 0 else f"{page_prefix}@{page}"
            ),
            InlineKeyboardButton(
                text=f"{page + 1}",
                callback_data=f"{page_prefix}@{page}"
            ),
            InlineKeyboardButton(
                text="➡️" if page < max_page - 1 else "❌",
                callback_data=f"{page_prefix}@{page + 1}" if page < max_page - 1 else f"{page_prefix}@{page}"
            )
        ]
    )
    markup = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

    return markup, page
