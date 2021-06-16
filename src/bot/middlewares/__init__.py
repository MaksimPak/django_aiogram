from aiogram import Dispatcher
from loguru import logger


def setup(dispatcher: Dispatcher):
    logger.info("Configure middlewares...")
    from bot.misc import i18n

    dispatcher.middleware.setup(i18n)
