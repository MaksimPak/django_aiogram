from aiogram import Dispatcher
from aiogram.utils.executor import Executor
from loguru import logger

from bot import config
from bot.misc import dp

runner = Executor(dp)


async def on_startup_webhook(dispatcher: Dispatcher):
    logger.info('Configure Web-Hook URL to: {url}', url=config.WEBHOOK_URL)
    await dispatcher.bot.set_webhook(config.WEBHOOK_URL)


def setup():
    logger.info('Configured executor...')
    runner.on_startup(on_startup_webhook, webhook=True, polling=False)
