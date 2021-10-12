from django import forms
from flat_json_widget.widgets import FlatJsonWidget

from forms import models
from forms.widgets import AdminJsonWidget
import re


class ContactFormAnswers(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContactFormAnswers, self).__init__(*args, **kwargs)
        self.fields['data'].widget = AdminJsonWidget(instance=self.instance)

    class Meta:
        model = models.ContactFormAnswers
        fields = '__all__'


class Form(forms.ModelForm):

    def clean(self):
        """
        Validate end message json of the form for key to match pattern number-number.
        Also check if value is str
        """
        key_pattern = re.compile(r'^\d+-\d+$')
        _valid_data = {}
        if self.cleaned_data.get('end_message'):
            for key, text in self.cleaned_data['end_message'].items():
                if key_pattern.match(key) and isinstance(text, str):
                    _valid_data[key] = text

            self.cleaned_data['end_message'] = _valid_data
        return super(Form, self).clean()

    class Meta:
        model = models.Form
        fields = '__all__'
        widgets = {
            'end_message': FlatJsonWidget
        }
