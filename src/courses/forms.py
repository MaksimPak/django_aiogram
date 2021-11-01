from django import forms
from flat_json_widget.widgets import FlatJsonWidget

from courses import models


class CourseForm(forms.ModelForm):

    class Meta:
        model = models.Course
        fields = '__all__'
        widgets = {
            'data': FlatJsonWidget
        }
