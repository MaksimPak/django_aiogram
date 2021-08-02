from django import template

register = template.Library()


@register.filter(name='int_json_key')
def int_json_key(d):
    return {int(k): v for k, v in d.items()}


@register.filter(name='dict_key')
def dict_key(d, k):
    return d.get(k)


@register.filter
def get_type(value):
    return type(value)
