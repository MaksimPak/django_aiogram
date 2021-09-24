from django import forms
from broadcast import models


class BroadcastForm(forms.ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    is_feedback = forms.BooleanField(required=False, label='Фидбек')

    def __init__(self, *args, **kwargs):
        super(BroadcastForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'style': 'width: 100%;'})

    class Meta:
        model = models.MessageSent
        fields = '__all__'
