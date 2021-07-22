from pathlib import Path

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger

from bot import config
from bot.middlewares.i18n import I18nMiddleware

bot = Bot(token=config.BOT_TOKEN)
redis = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, state_ttl=60*5, db=config.DATABASES['FSM'])
dp = Dispatcher(bot, storage=redis)
jinja_env = Environment(
    loader=PackageLoader('bot'),
    autoescape=select_autoescape(),
)
app_dir: Path = Path(__file__).parent
locales_dir = app_dir / 'locales'
i18n = I18nMiddleware('bot', locales_dir, default='ru')

jinja_env.globals['config'] = config


def setup():
    from bot import middlewares
    from bot.utils import executor

    middlewares.setup(dp)
    executor.setup()

    logger.info("Configured handlers...")
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

