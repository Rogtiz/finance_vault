import os

API_BASE = os.getenv('API_BASE_URL', 'http://localhost:8000')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('Set TELEGRAM_BOT_TOKEN env var')