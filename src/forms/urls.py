from django.urls import path

from forms import views

app_name = 'forms'

urlpatterns = [
    path('form-report/<int:form_id>', views.form_report, name='form_report'),
    path('statistics/<int:form_id>', views.form_statistics, name='form_statistics'),
]
