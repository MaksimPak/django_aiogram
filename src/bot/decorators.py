from bot.models.db import SessionLocal


def get_db(func):
    async def inner(*args, **kwargs):
        async with SessionLocal() as session:
            result = await func(*args, **kwargs, session=session)

        return result
    return inner
