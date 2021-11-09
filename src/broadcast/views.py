from django.http import HttpResponseRedirect
from django.shortcuts import render

from broadcast import models
from broadcast.forms import BroadcastForm
from broadcast.tasks import send_to_queue
from contacts import models as contact_models


def resend_msg(request, msg_id):
    """
    Renders sent message for resending
    """
    message = models.Message.objects.get(pk=msg_id)
    contacts = [x.contact for x in message.messagehistory_set.all()]
    form = BroadcastForm(initial={
        '_selected_action': [contact.id for contact in contacts],
        'text': message.text,
        'video': message.video,
        'image': message.image,
        'link': message.link,
        'notes': message.notes,
    })
    context = {
        'entities': contacts,
        'form': form,
        'referer': request.META['HTTP_REFERER'],
    }
    return render(request, "broadcast/send.html", context=context)


def render_send(request):
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


def send(request):
    """
    Handles POST Requests.
    Save submitted message and pass to celery for sending
    """
    message = models.Message.objects.create(
        text=request.POST.get('text'),
        video=request.FILES.get('video'),
        image=request.FILES.get('image'),
        link=request.POST.get('link'),
        notes=request.POST.get('notes'),
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
