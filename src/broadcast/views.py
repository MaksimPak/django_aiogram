from django.http import HttpResponseRedirect
from django.shortcuts import render

from broadcast import models
from broadcast.forms import BroadcastForm
from broadcast.tasks import message_students_task, send_to_queue
from contacts import models as contact_models
from users.models import Student


def send_one(request):
    """
    Render send template for specific contact
    """
    selected = request.GET.getlist('_selected_action')

    if 'all' in request.GET:
        contacts = contact_models.Contact.objects.all()
    else:
        contacts = contact_models.Contact.objects.filter(pk__in=selected)

    form = BroadcastForm(initial={'_selected_action': [x.id for x in contacts]})
    context = {
        'entities': contacts,
        'form': form,
        'referer': request.META['HTTP_REFERER'],
    }

    return render(request, 'broadcast/send.html', context=context)


def send_multiple(request):
    """
    Handles POST Requests.
    Save submitted message and pass to celery for sending
    """
    message = models.Message.objects.create(
        text=request.POST.get('text'),
        video=request.FILES.get('video'),
        image=request.FILES.get('image'),
        link=request.POST.get('link')
    )

    selected = request.POST.getlist('_selected_action')
    is_feedback = request.POST.get('is_feedback')
    config = {
        'ids': selected,
        'message_id': message.id,
        'is_feedback': is_feedback,
    }

    send_to_queue.delay(config)

    return HttpResponseRedirect(request.POST.get('referer'))

























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