import datetime

from django import forms
from django.forms.utils import ErrorList
from flat_json_widget.widgets import FlatJsonWidget

from courses import models


class CourseForm(forms.ModelForm):
    is_priority = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.set_priority_date:
            self.fields['is_priority'].initial = True

    def save(self, commit=True):
        if self.cleaned_data['is_priority'] and not self.instance.set_priority_date:
            self.instance.set_priority_date = datetime.datetime.now()
        elif not self.cleaned_data['is_priority'] and self.instance.set_priority_date:
            self.instance.set_priority_date = None

        return super(CourseForm, self).save(commit)

    class Meta:
        model = models.Course
        fields = '__all__'
        widgets = {
            'data': FlatJsonWidget,
        }
