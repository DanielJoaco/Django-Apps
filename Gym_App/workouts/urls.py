from django.urls import path
from . import views

app_name = 'workouts'

urlpatterns = [
    path('routines/', views.routines_view, name='routines'),
    path('routines/create/', views.create_routine_view, name='create_routine'),
    path('routines/edit/<int:routine_id>/', views.edit_routine_view, name='edit_routine'),
    path('api/search-exercises/', views.search_exercises_api, name='api_search_exercises'),
    path('api/create-exercise/', views.create_exercise_api, name='api_create_exercise'),
    path('routines/delete/<int:routine_id>/', views.delete_routine_view, name='delete_routine')
]