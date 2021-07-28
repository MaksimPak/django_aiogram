from django import forms

from dashboard import models
from dashboard.widgets import AdminJsonWidget


class LeadForm(forms.ModelForm):
    class Meta:
        model = models.Lead
        fields = ['first_name', 'last_name', 'language_type', 'phone', 'city', 'chosen_field']


class StudentAdmin(forms.ModelForm):
    course = forms.ModelMultipleChoiceField(
        queryset=models.Course.objects.all(),
        widget=forms.SelectMultiple,
        required=False
    )

    def get_initial_for_field(self, field, field_name):
        """
        Mark current courses of student in Admin panel
        """
        if self.instance and self.instance.id and hasattr(self.instance, 'courses'):
            courses = tuple([x.id for x in self.instance.courses.all()])
            self.fields['course'].initial = courses

            return super().get_initial_for_field(field, field_name)

    def save(self, commit=True):
        """
        Redefined save method to support Multiple Choice of courses in Admin panel
        """
        instance = super().save()
        instance.courses.set(self.cleaned_data['course'])
        # Add a method to the form to allow deferred
        # saving of m2m data.
        self.save_m2m = self._save_m2m
        return instance

    class Meta:
        model = models.Lead
        exclude = ('invite_link',)


class ContactFormAnswers(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContactFormAnswers, self).__init__(*args, **kwargs)
        self.fields['data'].widget = AdminJsonWidget(instance=self.instance)

    class Meta:
        model = models.ContactForm
        fields = '__all__'
