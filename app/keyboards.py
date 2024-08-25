from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


reg_button = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Зарегистрироваться')]
],
                                 resize_keyboard=True,
                                 input_field_placeholder='Выберите пункт меню'
)

