from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger
import sentry_sdk


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

    if config.APP_ENVIRONMENT != 'development':
        sentry_sdk.init(
            "https://8c853fb11a534fe692ac7b6db063b6fb@o437434.ingest.sentry.io/5803464",

            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0
        )

