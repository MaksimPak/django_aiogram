from django import forms
from broadcast import models

#
# class BroadcastForm(forms.Form):
#     _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
#     broadcast_text = forms.CharField(widget=forms.Textarea, label='Текст отправки')
#     is_feedback = forms.BooleanField(required=False, label='Фидбек')
#
#     def __init__(self, *args, **kwargs):
#         super(BroadcastForm, self).__init__(*args, **kwargs)
#         self.fields['broadcast_text'].widget.attrs.update({'style': 'display: block; margin: 8px auto '})
#
#
# class PromoForm(forms.Form):
#     _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
#     promotion = forms.ModelChoiceField(queryset=models.Promotion.objects.all())
#
#     def __init__(self, *args, **kwargs):
#         super(PromoForm, self).__init__(*args, **kwargs)
#         self.fields['promotion'].widget.attrs.update({'style': 'display: block; margin: 8px auto '})
#
