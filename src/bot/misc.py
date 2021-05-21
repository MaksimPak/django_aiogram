import logging

from aiogram import Bot, Dispatcher
from aiohttp import web
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher.webhook import configure_app
from jinja2 import Environment, PackageLoader, select_autoescape

from bot import config

bot = Bot(token=config.BOT_TOKEN)
storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, db=1)
dp = Dispatcher(bot, storage=storage)
jinja_env = Environment(
    loader=PackageLoader('bot'),
    autoescape=select_autoescape()
)

# Configure logging
logging.basicConfig(level=logging.INFO)


async def api_handler(request):
    return web.json_response({"status": "OK"}, status=200)


def setup():
    from bot import filters
    from bot.utils import executor

    filters.setup(dp)

    logging.info("Configuring handlers...")
    # noinspection PyUnresolvedReferences
    import bot.handlers

    app = web.Application()
    app.add_routes([web.post('/api', api_handler)])
    configure_app(dp, app, "/bot")

    # web.run_app(app, port=9000)
    executor.setup()
