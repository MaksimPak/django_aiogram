def lesson_upload_directory(instance, filename):
    return f'courses/{instance.course.id}/{filename}'
