import json


def prepare_promo_data(
        chat_id,
        video_id,
        message,
        duration,
        width,
        height,
        is_markup=False
):
    data = {
        'chat_id': chat_id,
        'caption': message,
        'duration': duration,
        'width': width,
        'height': height,
        'parse_mode': 'html',
    }

    if video_id:
        data['video'] = video_id

    if is_markup:
        data['reply_markup'] = json.dumps(
            {'inline_keyboard': [[{'text': 'Регистрация', 'callback_data': 'data|tg_reg'}]]}
        )
    return data
