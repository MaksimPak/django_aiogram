from django import forms

from dashboard.models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'language_type', 'phone', 'chosen_field']
