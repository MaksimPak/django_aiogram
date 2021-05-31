import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
DOMAIN = os.environ.get('DOMAIN', 'http://127.0.0.1:8000')

DB_URL = os.environ.get('DB_URL')
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)

WEBHOOK_PATH = f'/{BOT_TOKEN}/webhook'
WEBHOOK_URL = f'{DOMAIN}{WEBHOOK_PATH}'
BOT_PUBLIC_PORT = os.environ.get('BOT_PUBLIC_PORT', 8080)

CHAT_ID = os.environ.get('CHAT_ID')
