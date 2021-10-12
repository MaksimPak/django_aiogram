from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect

from users.forms import LeadForm
from users.models import Lead


def signup(request):
    """
    Save lead from signup page
    """
    if request.POST:
        try:
            lead = Lead.objects.create(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                language_type=request.POST['language_type'],
                phone=request.POST['phone'],
                city=request.POST['city'],
                chosen_field_id=request.POST['chosen_field'],
                application_type=Lead.ApplicationType.web,
                is_client=False
            )
            lead.refresh_from_db()
            return redirect(lead.invite_link)
        except IntegrityError:
            return HttpResponse('Invalid phone number. Number is already used')
    else:
        form = LeadForm()
        return render(request, 'users/signup.html', {'form': form})
