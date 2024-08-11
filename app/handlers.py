import os
import aiohttp
from aiogram import types, Router, Bot
from bs4 import BeautifulSoup
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.keyboards import inline_keyboard
from dotenv import load_dotenv
from app.log_settings import logger_settings

# Настройка логирования с помощью log_settings.py
logger = logger_settings('handlers')


router = Router()
# Создание объекта бота
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
bot = Bot(token=API_TOKEN)


# Команда /start
@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(f'Привет {message.from_user.username}! '
                         f'Я бот конвертор валют! Введите команду /convert для начала работы')
    logger.info(f'Пользователь {message.from_user.username} id: {message.from_user.id} использовал команду /start')


# Команда /convert и вызов инлайн-кнопок
@router.message(Command('convert'))
async def convert(message: Message) -> None:
    inline_keyboards = inline_keyboard()
    await message.answer('Выберите валюту', reply_markup=inline_keyboards)
    logger.info(f'Пользователь {message.from_user.username} id: {message.from_user.id} использовал команду /convert')


# Функция парсинг курса
async def fetch_exchange_rate(query) -> str:
    url = f'https://www.google.com/search?q={query}'
    if query.isascii():
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                result = soup.find("div", class_="BNeawe iBp4i AP7Wnd")
                return result.get_text() if result else None
    else:
        raise AttributeError


# Обработчик инлайн-кнопок USD to RUB и EUR to RUB
@router.callback_query(lambda c: c.data in ['USD to RUB', 'EUR to RUB'])
async def process_callback(callback_query: types.CallbackQuery) -> None:
    query_data = callback_query.data
    logger.info(f'Пользователь {callback_query.from_user.username} id: {callback_query.from_user.id}'
                f' нажал на кнопку {query_data}')

    result = await fetch_exchange_rate(query_data)
    if result:
        await bot.send_message(callback_query.from_user.id, result)
        logger.info(f'Пользователю {callback_query.from_user.username} id: {callback_query.from_user.id}'
                    f' отправлено сообщение {result}')

        # Уведомление Telegram, что callback обработан
        await bot.answer_callback_query(callback_query.id)
    else:
        await bot.send_message(callback_query.from_user.id, 'Не удалось получить курс валюты')
        logger.error(f'Не удалось получить курс валюты для пользователя {callback_query.from_user.username}'
                     f' id: {callback_query.from_user.id} к {query_data}')


class ConvertStates(StatesGroup):
    waiting_for_currency_input = State()


# Обработчик инлайн-кнопки для собственной валюты
@router.callback_query(lambda c: c.data == 'custom')
async def process_custom_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await bot.answer_callback_query(callback_query.id)  # Быстро отвечаем на callback
    await callback_query.message.answer(
        "Введите валюты для конвертации (например, USD to RUB | доллары в рубли)")
    await state.set_state(ConvertStates.waiting_for_currency_input)


# Обработчик собственной валюты
@router.message(ConvertStates.waiting_for_currency_input)
async def handle_custom_currency(message: Message, state: FSMContext) -> None:
    try:
        user_input = message.text.strip()
        result = await fetch_exchange_rate(user_input)
        if result:
            await state.clear()  # Завершаем состояние ожидания ввода
            await message.answer(result)
            logger.info(
                f'Пользователь {message.from_user.username} id: {message.from_user.id}'
                f' запросил курс {user_input} и получил ответ: {result}')
        elif user_input == "/convert":  # Если пользователь во время ожидания ввода нажал на /convert
            await state.clear()
            del user_input
            await convert(message)
        elif user_input == "/start":  # Если пользователь во время ожидания ввода нажал на /start
            await state.clear()
            del user_input
            await start(message)
        else:
            logger.error(f'У пользователя {message.from_user.username} id: {message.from_user.id}'
                         f' не удалось получить курс к: {user_input}')
            await message.answer("Не удалось получить курс валюты, попробуйте еще раз")
            del user_input
    except AttributeError:
        await message.answer("Неверный формат ввода. Введите только текст.")
        logger.info(f'Пользователь {message.from_user.username} id: {message.from_user.id}'
                    f' использовал неверный формат ввода')
