from django import template

from dashboard.models import Student

register = template.Library()


@register.filter(name='students')
def students(qs):
    student_lesson = qs.studentlesson_set.all().values('student').distinct()
    clients = [Student.objects.get(pk=x['student']) for x in student_lesson]
    return clients


@register.filter(name='students_hw_submitted')
def students_hw_submitted(qs):
    student_lesson = qs.studentlesson_set.filter(homework_sent__isnull=False).values('student').distinct()
    clients = [Student.objects.get(pk=x['student']) for x in student_lesson]
    return clients

