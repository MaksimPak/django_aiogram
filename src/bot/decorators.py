from functools import wraps

from bot.models.db import SessionLocal


def create_session(func):
    """
    Create session for database access.
    """
    @wraps(func)
    async def inner(*args, **kwargs):
        async with SessionLocal() as session:
            result = await func(*args, **kwargs, session=session)

        return result
    return inner
