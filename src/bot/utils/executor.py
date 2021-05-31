from aiogram import Dispatcher
from aiogram.utils.executor import Executor
from loguru import logger

from bot import config
from bot.misc import dp

runner = Executor(dp)


async def on_startup_webhook(dispatcher: Dispatcher):
    logger.info("Configure Web-Hook URL to: {url}", url=config.DOMAIN)
    await dispatcher.bot.set_webhook(config.DOMAIN)


def setup():
    logger.info("Configured executor...")
    runner.on_startup(on_startup_webhook, webhook=True, polling=False)
