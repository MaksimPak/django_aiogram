import functools

from bot.db.config import SessionLocal


def create_session(func):
    """
    Create session for database access.
    """
    @functools.wraps(func)
    async def inner(*args, **kwargs):
        if not kwargs.get('session'):
            async with SessionLocal() as session:
                kwargs['session'] = session
        result = await func(*args, **kwargs)
        return result

    return inner
