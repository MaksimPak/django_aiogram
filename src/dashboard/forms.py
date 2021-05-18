from django import forms

from dashboard import models


class ClientForm(forms.ModelForm):
    class Meta:
        model = models.Client
        fields = ['first_name', 'last_name', 'language_type', 'phone', 'chosen_field']


class StudentAdmin(forms.ModelForm):
    course = forms.ModelMultipleChoiceField(
        queryset=models.Course.objects.all(),
        widget=forms.SelectMultiple
    )

    def get_initial_for_field(self, field, field_name):
        if self.instance and self.instance.id and hasattr(self.instance, 'courses'):
            courses = tuple([x.id for x in self.instance.courses.all()])
            self.fields['course'].initial = courses

            return super().get_initial_for_field(field, field_name)

    def save(self, commit=True):
        instance = super(LeadAdmin, self).save(commit=False)
        instance.courses.set(self.cleaned_data['course'])
        if commit:
            instance.save()
        return instance

    class Meta:
        model = models.Lead
        exclude = ('invite_link',)
