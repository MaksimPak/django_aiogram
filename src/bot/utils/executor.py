from aiogram.utils.executor import Executor
from bot.misc import dp

runner = Executor(dp)


def setup():
    runner.start_polling()
