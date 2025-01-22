import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import router


# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def main():
    try:
        print("Бот стартует...")
        await dp.start_polling(bot)
    finally:
        print("Сессия закрывается...")
        await bot.session.close()


if __name__ == "__main__":
    print(BOT_TOKEN)
    asyncio.run(main())