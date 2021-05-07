from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseNotFound, HttpResponse

# Create your views here.
from dashboard.models import LessonUrl, Lead
from dashboard.forms import ClientForm


def watch_video(request, uuid):
    lesson_url = get_object_or_404(LessonUrl, hash=uuid)
    context = {'lesson': lesson_url.lesson}
    if lesson_url:
        lesson_url.delete()
        return render(request, 'dashboard/watch_lesson.html', context)
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')


def signup(request):
    if request.POST:
        Lead.objects.create(
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            language_type=request.POST['language_type'],
            phone=request.POST['phone'],
            chosen_field=request.POST['chosen_field'],
            application_type=3,
            is_client=False
        )
        return HttpResponse('thank you')
    else:
        form = ClientForm()
        return render(request, 'dashboard/signup.html', {'form': form})
