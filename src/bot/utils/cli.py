import functools

import click
from aiogram.__main__ import SysInfo
from loguru import logger

try:
    import aiohttp_autoreload
except ImportError:
    aiohttp_autoreload = None


@click.group()
def cli():
    from bot.utils import logging
    from bot import misc

    logging.setup()
    misc.setup()


def auto_reload_mixin(func):
    @click.option(
        "--autoreload", is_flag=True, default=False, help="Reload application on file changes"
    )
    @functools.wraps(func)
    def wrapper(autoreload: bool, *args, **kwargs):
        if autoreload and aiohttp_autoreload:
            logger.warning(
                "Application started in live-reload mode. Please disable it in production!"
            )
            aiohttp_autoreload.start()
        elif autoreload and not aiohttp_autoreload:
            click.echo("`aiohttp_autoreload` is not installed.", err=True)
        return func(*args, **kwargs)

    return wrapper


@cli.command()
def version():
    """
    Get application version
    """
    click.echo(SysInfo())


@cli.command()
@click.option("--skip-updates", is_flag=True, default=False, help="Skip pending updates")
@auto_reload_mixin
def polling(skip_updates: bool):
    """
    Start application in polling mode
    """
    from bot.utils.executor import runner

    runner.skip_updates = skip_updates
    runner.start_polling(reset_webhook=True)


@cli.command()
@auto_reload_mixin
def webhook():
    """
    Run application in webhook mode
    """
    from bot.utils.executor import runner
    from bot import config

    runner.start_webhook(webhook_path=config.WEBHOOK_PATH, port=config.BOT_PUBLIC_PORT)
