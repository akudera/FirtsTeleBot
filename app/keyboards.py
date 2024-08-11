from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def inline_keyboard():
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USD/RUB", callback_data='USD to RUB'),
         InlineKeyboardButton(text="EUR/RUB", callback_data='EUR to RUB')],
        [InlineKeyboardButton(text="Своя валюта", callback_data='custom')]])
    return inline_kb
