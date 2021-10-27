from django.shortcuts import render

from forms import models
from forms.utils.helpers import normalize_answer, stringify_bool, generate_report


def get_answers_percentage(form_id, questions):
    resp = dict()
    for question in questions:
        total_count = 0
        counts = []
        for static_ans in question.answers.all():
            # num of ppl who answered with specific ans
            count = len(models.ContactFormAnswers.objects.raw("""
            SELECT * FROM forms_contactformanswers WHERE
            form_id='%s' AND (data->'%s')::jsonb ? %s
            """, [form_id, question.id, static_ans.text]))
            total_count += count
            counts.append((static_ans.id, count))
            resp[static_ans.id] = count
        for k, v in counts:
            print(v)
            resp[k] = round((v/total_count)*100) if v else 0

    return resp


def form_statistics(request, form_id: int):
    """
    Generate HTML page for displaying statistics
    """
    form = models.Form.objects.get(pk=form_id)
    answers = models.ContactFormAnswers.objects.filter(form__pk=form_id)
    questions = form.formquestion_set.all()
    percentage = get_answers_percentage(form_id, questions)
    # print(percentage)
    context = {
        'form': form,
        'questions': questions,
        'answers': answers,
        'percentage': percentage
    }
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

