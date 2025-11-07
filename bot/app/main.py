from aiogram import executor
from .bot import dp

# Импортируем handlers, чтобы они зарегистрировались в Dispatcher
from . import handlers 

async def on_startup(dispatcher):
    print("Bot starting polling...")

async def on_shutdown(dispatcher):
    print("Bot shutting down...")

if __name__ == '__main__':
    executor.start_polling(
        dp, 
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )