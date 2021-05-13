from django import template

register = template.Library()


@register.filter(name='homework_count')
def homework_count(qs):
    return qs.studentlesson_set.filter(homework_sent__isnull=False).count()
