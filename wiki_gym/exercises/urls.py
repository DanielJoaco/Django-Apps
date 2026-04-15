from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.index, name='search'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('exercise/', views.exercise_detail, name='exercise_detail'),
    path('exercise/<int:id>/', views.exercise_detail, name='exercise_detail_by_id'),
    path('excercise/', views.exercise_detail, name='excercise'),
    path('excercise/<int:id>/', views.exercise_detail, name='excercise_by_id'),
    path('panel/', views.panel_list, name='panel_list'),
    path('panel/ejercicio/crear/', views.exercise_create, name='exercise_create'),
    path('panel/ejercicio/<int:id>/editar/', views.exercise_edit, name='exercise_edit'),
    path('panel/ejercicio/<int:id>/eliminar/', views.exercise_delete, name='exercise_delete'),
]