import time

from celery import group
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.files.storage import default_storage


from broadcast.tasks import message_students_task, send_to_queue
from general.utils.ffmpeg import get_duration, get_resolution
from users.models import Student
from contacts import models as contact_models
from broadcast import models
import pickle

def send_multiple(request):
    """
    Handles message sending to students from Course in Admin panel
    """
    print(request.POST)
    print(request.FILES)
    data = request.FILES['image']
    default_storage.save(f'tmp/{data.name}', ContentFile(data.read()))

    return
    selected = request.POST.getlist('_selected_action')
    is_feedback = request.POST.get('is_feedback')
    config = {
        'ids': selected,
        'is_feedback': is_feedback,
        'text': request.POST.get('text'),
        'photo': pickle.dumps(request.FILES['image'].read()),
    }

    send_to_queue.delay(config)

    return HttpResponseRedirect(request.POST.get('referer'))


def send(request, contact_id: int):
    referer = request.META['HTTP_REFERER']
    contact = contact_models.Contact.objects.filter(pk=contact_id)
    context = {
        'entities': contact,
        'referer': referer,
    }

    if 'send' in request.POST:
        config = {
            'ids': contact_id,
            'is_feedback': request.POST.get('is_feedback'),
            'text': request.POST['message'],
        }

        send_to_queue.delay(config)

        return HttpResponseRedirect(request.POST.get('referer'))

    return render(request, 'broadcast/send.html', context=context)






















def message_to_students(request):
    """
    Handles message sending to students from Course in Admin panel
    """
    students = Student.objects.all()
    selected = getattr(request, request.method).getlist('_selected_action')
    referer = request.META['HTTP_REFERER']

    if selected:
        students = Student.objects.filter(pk__in=selected)

    course_id = getattr(request, request.method).get('course_id')
    lesson_id = getattr(request, request.method).get('lesson_id')

    if 'send' in request.POST:
        is_feedback = request.POST.get('is_feedback')

        config = {
            'is_feedback': is_feedback,
            'students': 'all' if not selected else selected,
            'message': request.POST['message'],
            'course_id': course_id,
            'lesson_id': lesson_id
        }

        message_students_task.delay(config)

        return HttpResponseRedirect(request.POST.get('referer'))

    return render(request, 'dashboard/send_intermediate.html', context={
        'entities': students,
        'course_id': course_id,
        'lesson_id': lesson_id,
        'referer': referer,
    })