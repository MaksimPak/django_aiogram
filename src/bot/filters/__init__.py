import logging

from aiogram import Dispatcher


def setup(dispatcher: Dispatcher):
    logging.info('Configuring filters')
    from .is_client import IsClientFilter

    dispatcher.filters_factory.bind(IsClientFilter, event_handlers=[dispatcher.message_handlers])
