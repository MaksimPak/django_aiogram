
def promo_upload_directory(instance, filename):
    if getattr(instance, 'course'):
        return f'promos/{instance.course.id}/{filename}'
    else:
        return f'promos/{filename}'
