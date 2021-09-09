import re
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Regexp

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.serializers import MessageSender, KeyboardGenerator
from bot.utils.callback_settings import short_data
from aiogram.dispatcher.filters import Text


@dp.message_handler(Text(equals='🛠️ Ассеты'), state='*')
@create_session
async def list_assets(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    await state.reset_state()
    contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
    contact_assets = await repo.ContactAssetRepository.contact_assets(contact.id, session)
    assets_data = [(contact_asset.asset.title, ('asset', contact_asset.asset.id)) for contact_asset in contact_assets]
    markup = KeyboardGenerator(assets_data).keyboard

    await message.reply(
        'Выберите Ассет',
        reply_markup=markup
    )


@dp.message_handler(CommandStart(re.compile(r'asset_(\d+)')))
@dp.message_handler(Regexp(re.compile(r'asset_(\d+)')))
@dp.callback_query_handler(short_data.filter(property='asset'))
@create_session
async def send_asset(
        response: Union[types.Message, types.CallbackQuery],
        session: SessionLocal,
        callback_data: dict = None,
        regexp: re.Match = None,
        deep_link: re.Match = None
):
    if type(response) == types.CallbackQuery:
        await response.answer()
        asset_id = callback_data['value']
    else:
        asset_id = regexp.group(1) if regexp else deep_link.group(1)

    contact = await repo.ContactRepository.get_or_create(
        response.from_user.id,
        response.from_user.first_name,
        response.from_user.last_name,
        session
    )

    asset = await repo.AssetRepository.get('id', int(asset_id), session)

    if contact.access_level >= asset.access_level.value:
        await repo.ContactAssetRepository.unique_create(contact.id, asset.id, session)
        await MessageSender(response.from_user.id, asset.desc, file=asset.file).send()
    else:
        delta = asset.access_level.value - contact.access_level
        if delta == 2:
            kb = KeyboardGenerator([('Регистрация', ('tg_reg',))]).keyboard
            return await bot.send_message(contact.tg_id, 'Пожалуйста, пройдите регистрацию', reply_markup=kb)
        else:
            await bot.send_message(contact.tg_id, 'Недостаточно доступа')
