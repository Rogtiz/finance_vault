import asyncio
import logging
from .bot import dp, bot

# Импортируем handlers, чтобы они зарегистрировались в Dispatcher
from . import handlers 

async def on_startup(dispatcher):
    print("Bot starting polling...")

async def on_shutdown(dispatcher):
    print("Bot shutting down...")

async def main():
    logging.info("Bot starting polling...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot shutting down...")