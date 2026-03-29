from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from workouts.views import routines_list

@login_required
def dashboard_view(request):
    routines = routines_list(request)
    return render(request, 'dashboard.html', {
        'routines': routines,
    })