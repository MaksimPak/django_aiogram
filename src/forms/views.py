from forms import models
from forms.utils.helpers import normalize_answer, stringify_bool, generate_report


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
            [str(answer.id), answer.contact.__str__(), date_passed, stringify_bool(answer.contact.is_registered)]
            + [normalize_answer(answer.data.get(str(x.id), '-')) for x in questions]
        )

    rows = [headers, *collected_answers]

    return generate_report(form.id, rows)

