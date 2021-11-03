from django import template

register = template.Library()


@register.filter(name='answer_texts')
def answer_texts(qs):
    return [x.text for x in qs]
