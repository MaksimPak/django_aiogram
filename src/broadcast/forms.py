from django import forms
from broadcast import models


class BroadcastForm(forms.ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    is_feedback = forms.BooleanField(required=False, label='Фидбек')

    def __init__(self, *args, **kwargs):
        super(BroadcastForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'style': 'width: 800px;'})
        self.fields['notes'].widget.attrs.update({'style': 'width: 800px;'})
        self.fields['link'].widget.attrs.update({'style': 'width: 500px;'})

    class Meta:
        model = models.Message
        fields = ('text', 'video', 'image', 'link', 'notes')
