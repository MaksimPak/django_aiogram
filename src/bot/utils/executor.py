from aiogram import Dispatcher
from aiogram.utils.executor import Executor
from loguru import logger

from bot import config
from bot.misc import dp
from bot.models.db import engine

runner = Executor(dp)


async def on_startup_webhook(dispatcher: Dispatcher):
    logger.info('Configure Web-Hook URL to: {url}', url=config.WEBHOOK_URL)
    await dispatcher.bot.set_webhook(config.WEBHOOK_URL)


async def on_shutdown(dispatched: Dispatcher):
    logger.info('Shutting down db engine')
    await engine.dispose()


def setup():
    logger.info('Configured executor...')
    runner.on_startup(on_startup_webhook, webhook=True, polling=False)
    runner.on_shutdown(on_shutdown)
