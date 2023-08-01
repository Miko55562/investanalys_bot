from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def markup_main():
    kb = [
            [
                KeyboardButton(text='Профиль'),
                KeyboardButton(text='Уведомления')
            ],
            [
                KeyboardButton(text='График'),
                KeyboardButton(text='Настройки')
            ],
        ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    return keyboard


def markup_cancle():
    kb = [
            [
                KeyboardButton(text='Назад'),
            ],
        ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    return keyboard


def markup_interval():
    kb = [
            [
                KeyboardButton(text="4 hour", callback_data="4 hour"),
                KeyboardButton(text="1 day", callback_data="1 day"),
                KeyboardButton(text="1 wick", callback_data="1 wick")
            ]
          ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    return keyboard
