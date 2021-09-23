from django import forms


class BroadcastForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    broadcast_text = forms.CharField(widget=forms.Textarea)
    is_feedback = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(BroadcastForm, self).__init__(*args, **kwargs)
        self.fields['broadcast_text'].label = 'Текст отправки'
        self.fields['is_feedback'].label = 'Фидбек'
        self.fields['broadcast_text'].widget.attrs.update({'style': 'display: block; margin: 8px auto '})

