import json
import os

from django import forms


class AdminJsonWidget(forms.Textarea):
    template_name = 'forms/widgets/json_display.html'

    def __init__(self, attrs=None, instance=None):
        super(AdminJsonWidget, self).__init__(attrs)
        self.instance = instance

    def get_context(self, name, value, attrs):
        context = super(AdminJsonWidget, self).get_context(name, value, attrs)
        if self.instance.pk:
            db_answers = json.loads(context['widget']['value'])
            questions = self.instance.form.formquestion_set.all()
            answers = dict()
            for key in questions:
                for value in db_answers:
                    if key.id == int(value):
                        answers[key.text] = db_answers[value]
            context['widget']['value'] = answers
        return context



