def prepare_promo_data(
        chat_id,
        video_id,
        message,
        duration,
        width,
        height,
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

    return data
