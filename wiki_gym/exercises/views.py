from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render

from .models import Exercise
from .forms import ExerciseForm


PAGE_SIZE = 9


def _build_query_string(params):
	clean_params = {key: value for key, value in params.items() if value}
	return urlencode(clean_params)


@login_required(login_url='login')
def index(request):
	exercises = Exercise.objects.select_related('pattern', 'muscle_group', 'agonist').filter(is_active=True)

	search_query = request.GET.get('q', '').strip()
	selected_type = request.GET.get('type', '').strip()

	if search_query:
		exercises = exercises.filter(
			Q(name__icontains=search_query)
			| Q(description__icontains=search_query)
			| Q(pattern__name__icontains=search_query)
			| Q(muscle_group__name__icontains=search_query)
			| Q(agonist__name__icontains=search_query)
		)

	if selected_type in dict(Exercise.EXERCISE_TYPE_CHOICES):
		exercises = exercises.filter(exercise_type=selected_type)

	exercises = exercises.order_by('name')
	paginator = Paginator(exercises, PAGE_SIZE)
	page_obj = paginator.get_page(request.GET.get('page'))

	page_query_string = _build_query_string({
		'q': search_query,
		'type': selected_type,
	})

	context = {
		'page_obj': page_obj,
		'exercises': page_obj,
		'search_query': search_query,
		'selected_type': selected_type,
		'selected_type_label': dict(Exercise.EXERCISE_TYPE_CHOICES).get(selected_type, ''),
		'type_filters': Exercise.EXERCISE_TYPE_CHOICES,
		'total_exercises': exercises.count(),
		'page_query_string': page_query_string,
	}
	return render(request, 'index.html', context)


@login_required(login_url='login')
def exercise_detail(request, id=None):
	exercise_id = id or request.GET.get('id')
	if not exercise_id:
		raise Http404('No se indico el ejercicio.')

	exercise = get_object_or_404(
		Exercise.objects.select_related('pattern', 'muscle_group', 'agonist', 'created_by'),
		pk=exercise_id,
	)
	return render(request, 'excercise/excercise.html', {'exercise': exercise})


def user_login(request):
	if request.user.is_authenticated:
		return redirect('index')

	form = AuthenticationForm(request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		auth_login(request, form.get_user())
		messages.success(request, 'Sesion iniciada correctamente.')
		next_url = request.POST.get('next') or request.GET.get('next')
		if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
			return redirect(next_url)
		return redirect('index')

	return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
	auth_logout(request)
	messages.info(request, 'Sesion cerrada.')
	return redirect('login')


@login_required(login_url='login')
def panel_list(request):
	exercises = Exercise.objects.select_related('pattern', 'muscle_group', 'agonist').all()

	search_query = request.GET.get('q', '').strip()
	selected_type = request.GET.get('type', '').strip()
	status_filter = request.GET.get('status', '').strip()

	if search_query:
		exercises = exercises.filter(
			Q(name__icontains=search_query)
			| Q(description__icontains=search_query)
			| Q(agonist__name__icontains=search_query)
		)

	if selected_type in dict(Exercise.EXERCISE_TYPE_CHOICES):
		exercises = exercises.filter(exercise_type=selected_type)

	if status_filter == 'active':
		exercises = exercises.filter(is_active=True)
	elif status_filter == 'inactive':
		exercises = exercises.filter(is_active=False)

	exercises = exercises.order_by('name')
	paginator = Paginator(exercises, PAGE_SIZE)
	page_obj = paginator.get_page(request.GET.get('page'))

	page_query_string = _build_query_string({
		'q': search_query,
		'type': selected_type,
		'status': status_filter,
	})

	context = {
		'page_obj': page_obj,
		'exercises': page_obj,
		'search_query': search_query,
		'selected_type': selected_type,
		'selected_type_label': dict(Exercise.EXERCISE_TYPE_CHOICES).get(selected_type, ''),
		'type_filters': Exercise.EXERCISE_TYPE_CHOICES,
		'status_filter': status_filter,
		'total_exercises': exercises.count(),
		'page_query_string': page_query_string,
	}
	return render(request, 'panel/panel.html', context)


@login_required(login_url='login')
def exercise_create(request):
	if request.method == 'POST':
		form = ExerciseForm(request.POST, request.FILES or None)
		if form.is_valid():
			exercise = form.save(commit=False)
			exercise.created_by = request.user
			exercise.save()
			messages.success(request, f'Ejercicio "{exercise.name}" creado exitosamente.')
			return redirect('panel_list')
	else:
		form = ExerciseForm()

	context = {'form': form, 'action': 'Crear'}
	return render(request, 'panel/exercise_form.html', context)


@login_required(login_url='login')
def exercise_edit(request, id):
	exercise = get_object_or_404(Exercise, pk=id)

	if request.method == 'POST':
		form = ExerciseForm(request.POST, request.FILES or None, instance=exercise)
		if form.is_valid():
			exercise = form.save()
			messages.success(request, f'Ejercicio "{exercise.name}" actualizado exitosamente.')
			return redirect('panel_list')
	else:
		form = ExerciseForm(instance=exercise)

	context = {'form': form, 'action': 'Editar', 'exercise': exercise}
	return render(request, 'panel/exercise_form.html', context)


@login_required(login_url='login')
def exercise_delete(request, id):
	exercise = get_object_or_404(Exercise, pk=id)
	if request.method == 'POST':
		exercise_name = exercise.name
		exercise.delete()
		messages.success(request, f'Ejercicio "{exercise_name}" eliminado exitosamente.')
		return redirect('panel_list')

	context = {'exercise': exercise}
	return render(request, 'panel/exercise_confirm_delete.html', context)
