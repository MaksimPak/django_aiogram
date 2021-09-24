import time

from celery import group
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string

from broadcast.tasks import message_students_task, send_to_queue
from general.utils.ffmpeg import get_duration, get_resolution
from users.models import Student
from contacts import models as contact_models
from broadcast import models


def text_handler(request):

    selected = request.POST.getlist('_selected_action')
    is_feedback = request.POST.get('is_feedback')
    config = {
        'ids': selected,
        'is_feedback': is_feedback,
        'text': request.POST.get('broadcast_text'),
    }

    send_to_queue.delay(config)

    return HttpResponseRedirect(request.POST.get('referer'))


def promo_handler(request):
    promo_id = request.POST.get('promo_id')
    promotion = models.Promotion.objects.get(pk=promo_id)
    contacts = request.POST.getlist('_selected_action')
    message = render_to_string('broadcast/promo_text.html', {'promo': promotion})
    image = promotion.image.path
    video = None
    thumb = None
    duration = None
    width = None
    height = None

    if promotion.video:
        image = None
        video = promotion.video.path
        thumb = promotion.image.path
        duration = get_duration(promotion.video.path)
        width, height = get_resolution(promotion.video.path)

    report = models.SendingReport.objects.create(lang='undefined', promotion=promotion, sent=len(contacts))

    tasks = []
    for i, tg_id in enumerate(contacts):
        if i % 25 == 0:
            time.sleep(1)

        data = {
            'chat_id': tg_id,
            'message': message,
            'image': image,
            'video': video,
            'duration': duration,
            'width': width,
            'height': height,
            'thumb': thumb
        }

        student.blocked_bot or tasks.append(send_to_queue.s(data, report.id, student.id))
    result = group(tasks)().save()
    models.SendingReport.objects.filter(pk=report.id).update(celery_id=result.id)

SUBMISSION_TYPES = {
    'text': text_handler,
    'promo': 'promo_handler',
    'course': 'course_handler',
}


def send_multiple(request):
    """
    Handles message sending to students from Course in Admin panel
    """
    handler_type = request.POST['submission_type']
    return SUBMISSION_TYPES[handler_type](request)


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