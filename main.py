import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from app.handlers import router
from app.log_settings import logger_settings

# Настройка логирования с помощью log_settings.py
logger = logger_settings('main')


# Загрузка токена из переменных окружения
API_TOKEN = os.getenv('API_TOKEN')

# Создание объекта бота и диспетчера
load_dotenv()
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main() -> None:
    try:
        logger.info('Запуск бота')
        dp.include_router(router)
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Остановка бота')
