from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from workouts.views import routines_list, workout_sessions_list

@login_required
def dashboard_view(request):
    routines = routines_list(request)
    workout_sessions = workout_sessions_list(request, limit=5)
    return render(request, 'dashboard.html', {
        'routines': routines,
        'workout_sessions': workout_sessions,
    })