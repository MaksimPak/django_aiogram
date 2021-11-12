from tempfile import NamedTemporaryFile

import qrcode
from django.db import connection
from django.shortcuts import render
from qrcode.image.svg import SvgImage

from forms import models
from forms.utils.helpers import normalize_answer, stringify_bool, generate_report


def get_answers_percentage(form_id, questions):
    resp = {}
    for question in questions:
        total_count = 0
        counts = []
        for static_ans in question.answers.all():
            # Retrieve count of times answer was selected and close session
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM forms_contactformanswers WHERE
                    form_id=%s AND (data->'%s')::jsonb ? %s
                    """, [form_id, question.id, static_ans.text])
                count, = cursor.fetchone()
            total_count += count
            counts.append((static_ans.id, count))
            resp[static_ans.id] = count
        for answer_id, answer_count in counts:
            resp[answer_id] = round((answer_count/total_count)*100) if answer_count else 0

    return resp


def form_statistics(request, form_id: int):
    """
    Generate HTML page for displaying statistics
    """
    form = models.Form.objects.get(pk=form_id)
    questions = form.formquestion_set.all()
    percentage = get_answers_percentage(form_id, questions)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                       image_factory=SvgImage)
    qr.add_data(form.link)
    img_2 = qr.make_image()
    context = {
        'form': form,
        'questions': questions,
        'percentage': percentage
    }
    with NamedTemporaryFile() as tmp:
        img_2.save(tmp.name)
        stream = tmp.read().decode()
        context['qr'] = stream
        return render(request, 'forms/statistics.html', context=context)


def form_report(request, form_id: int):
    """
    Generate xlsx file for form
    """
    form = models.Form.objects.get(pk=form_id)
    questions = form.formquestion_set.all()
    answers = form.contactformanswers_set.all()

    headers = ['Id', 'Студент', 'Дата прохождения', 'Зареган'] + [x.text for x in questions]
    collected_answers = []
    for answer in answers:
        date_passed = (answer.updated_at if answer.updated_at else answer.created_at).strftime('%m/%d/%Y, %H:%M')
        collected_answers.append(
            [answer.id, answer.contact.__str__(), date_passed, stringify_bool(answer.contact.is_registered)]
            + [normalize_answer(answer.data.get(str(x.id), '-')) for x in questions]
        )

    rows = [headers, *collected_answers]

    return generate_report(form.id, rows)

