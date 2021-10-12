def form_question_directory(instance, filename):
    return f'form_questions/{instance.form.id}/{filename}'


def form_directory(instance, filename):
    return f'forms/{instance.id}/{filename}'
