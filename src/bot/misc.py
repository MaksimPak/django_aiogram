from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger


from bot import config

bot = Bot(token=config.BOT_TOKEN)
storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, db=1)
dp = Dispatcher(bot, storage=storage)
jinja_env = Environment(
    loader=PackageLoader('bot'),
    autoescape=select_autoescape(),
)
jinja_env.globals['config'] = config


def setup():
    from bot.utils import executor

    logger.info("Configured handlers...")
    executor.setup()

    # noinspection PyUnresolvedReferences
    import bot.handlers

