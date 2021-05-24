from django import template

from dashboard.models import Student

register = template.Library()


@register.filter(name='students_received')
def students(qs):  # todo qs to lesson naming
    student_lesson = qs.studentlesson_set.filter(date_received__isnull=False).values('student').distinct()
    clients = [Student.objects.get(pk=x['student']) for x in student_lesson]
    return clients


@register.filter(name='students_watched')
def students(qs):
    student_lesson = qs.studentlesson_set.filter(date_watched__isnull=False).values('student').distinct()
    clients = [Student.objects.get(pk=x['student']) for x in student_lesson]
    return clients


@register.filter(name='students_hw_submitted')
def students_hw_submitted(qs):
    student_lesson = qs.studentlesson_set.filter(homework_sent__isnull=False).values('student').distinct()
    clients = [Student.objects.get(pk=x['student']) for x in student_lesson]
    return clients

