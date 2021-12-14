def cert_tmplt_dir(instance, filename):
    return f'cert_media/templates/{filename}'


def cert_upload_dir(instance, filename):
    return f'cert_media/courses/{instance.template.course.id}/{filename}'
