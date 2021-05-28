from aiogram.utils.callback_data import CallbackData

simple_data = CallbackData('data', 'value', sep='|')
short_data = CallbackData('data', 'property', 'value', sep='|')
two_valued_data = CallbackData('data', 'property', 'first_value', 'second_value', sep='|')
three_valued_data = CallbackData('data', 'property', 'first_value', 'second_value', 'third_value', sep='|')
