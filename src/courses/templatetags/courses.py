from django import template

register = template.Library()


@register.filter(name='get_selected')
def get_selected(course):
    return ''.join(['_selected_action=' + str(x.id)
                    for x in course.studentcourse_set.all()])
