# workouts/views.py
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.utils import timezone
from datetime import date, time
from .models import Exercise, Routine, RoutineItem, MuscleGroup
from .forms import RoutineForm, ExerciseAsyncForm


def _sync_routine_items_from_request(request, routine):
    """Sincroniza los items de rutina según el orden recibido del frontend."""
    exercise_ids = request.POST.getlist('exercises[]')

    # En edición, la estrategia más robusta es reconstruir la tabla intermedia.
    routine.items.all().delete()

    for index, ex_id in enumerate(exercise_ids):
        sets = request.POST.get(f'sets_{ex_id}')
        reps = request.POST.get(f'reps_{ex_id}')

        try:
            exercise_instance = Exercise.objects.get(id=ex_id)
            RoutineItem.objects.create(
                routine=routine,
                exercise=exercise_instance,
                recommended_sets=int(sets) if sets else 3,
                recommended_reps=int(reps) if reps else 10,
                order=index + 1
            )
        except Exercise.DoesNotExist:
            continue

@login_required
def create_routine_view(request):
    """Vista principal sincrónica para ensamblar la rutina."""
    exercise_form = ExerciseAsyncForm()

    if request.method == 'POST':
        routine_form = RoutineForm(request.POST)
        
        if routine_form.is_valid():
            routine = routine_form.save(commit=False)
            routine.user = request.user
            routine.save()
            _sync_routine_items_from_request(request, routine)

            return redirect('workouts:routines') 
            
    else:
        routine_form = RoutineForm()

    return render(request, 'workouts/create_routine.html', {
        'page_title': 'Crear Rutina - Gym App',
        'heading_title': 'Estructurar Nueva Rutina',
        'submit_label': 'Guardar Rutina Completa',
        'routine_form': routine_form,
        'exercise_form': exercise_form,
        'initial_exercises': []
    })


@login_required
def edit_routine_view(request, routine_id):
    """Vista para editar una rutina existente del usuario."""
    routine = get_object_or_404(
        Routine.objects.prefetch_related('items__exercise__muscle_group'),
        id=routine_id,
        user=request.user
    )
    exercise_form = ExerciseAsyncForm()

    if request.method == 'POST':
        routine_form = RoutineForm(request.POST, instance=routine)

        if routine_form.is_valid():
            routine = routine_form.save()
            _sync_routine_items_from_request(request, routine)
            return redirect('workouts:routines')
    else:
        routine_form = RoutineForm(instance=routine)

    initial_exercises = [
        {
            'id': item.exercise.id,
            'name': item.exercise.name,
            'category': item.exercise.muscle_group.name if item.exercise.muscle_group else '',
            'sets': item.recommended_sets,
            'reps': item.recommended_reps,
        }
        for item in routine.items.all()
    ]

    return render(request, 'workouts/create_routine.html', {
        'page_title': 'Editar Rutina - Gym App',
        'heading_title': 'Editar Rutina',
        'submit_label': 'Guardar Cambios',
        'routine_form': routine_form,
        'exercise_form': exercise_form,
        'initial_exercises': initial_exercises
    })

@login_required
def search_exercises_api(request):
    """Endpoint asíncrono para la búsqueda global de ejercicios."""
    query = request.GET.get('q', '')
    if query:
        # Búsqueda global: Ya no filtramos por request.user
        exercises = Exercise.objects.filter(name__icontains=query, is_active=True)
        
        # Serialización de los resultados usando el grupo muscular
        results = [
            {
                'id': ex.id, 
                'name': ex.name, 
                'category': ex.muscle_group.name if ex.muscle_group else 'General'
            } 
            for ex in exercises[:10]
        ]
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})

@login_required
def create_exercise_api(request):
    """Endpoint asíncrono para crear un nuevo ejercicio en el catálogo global."""
    if request.method == 'POST':
        form = ExerciseAsyncForm(request.POST, request.FILES)
        if form.is_valid():
            # El formulario ya valida el muscle_group obligatoriamente
            exercise = form.save(commit=False)
            # Registramos qué usuario aportó este ejercicio al sistema
            exercise.created_by = request.user 
            # Detona la compresión de Pillow y guarda en base de datos
            exercise.save() 
            
            return JsonResponse({'success': True, 'id': exercise.id, 'name': exercise.name})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def _get_user_routines_queryset(user):
    """Retorna las rutinas del usuario listas para ser renderizadas en vistas."""
    return Routine.objects.filter(user=user).prefetch_related(
        'items__exercise__muscle_group'
    ).order_by(Lower('name'))


def routines_list(request):
    """Colección reutilizable de rutinas para inyectar en distintos templates."""
    return list(_get_user_routines_queryset(request.user))

@login_required
def routines_view(request):
    """Vista para listar las rutinas del usuario reutilizando la colección común."""
    routines = routines_list(request)
    return render(request, 'workouts/routines.html', {'routines': routines})

@login_required
def delete_routine_view(request, routine_id):
    """Vista para eliminar una rutina específica del usuario."""
    try:
        routine = Routine.objects.get(id=routine_id, user=request.user)
        routine.delete()
        return redirect('workouts:routines')
    except Routine.DoesNotExist:
        return redirect('workouts:routines')

@login_required
def records_view(request):
    """Vista para mostrar el diario de ejercicios del usuario."""
    try:
        records = request.user.exercise_logs.select_related('exercise').order_by('-date')
    except Exception:
        records = []
    
    return render(request, 'workouts/records.html', {'recent_exercises': records})

@login_required
def add_record_view(request):
    """Vista para crear una nueva entrada de ejercicio en el diario."""
    now = timezone.localtime()
    today = now.date()
    current_time_obj = now.time().replace(microsecond=0)
    selected_date = today
    selected_hour = str((now.hour % 12) or 12)
    selected_minute = f"{now.minute:02d}"
    selected_period = 'AM' if now.hour < 12 else 'PM'
    selected_end_hour = str((now.hour % 12) or 12)
    selected_end_minute = f"{now.minute:02d}"
    selected_end_period = 'AM' if now.hour < 12 else 'PM'
    date_error = None
    time_error = None
    end_time_error = None
    selected_exercises_error = None

    if request.method == 'POST':
        raw_date = (request.POST.get('date') or '').strip()
        raw_hour = (request.POST.get('start_hour') or '').strip()
        raw_minute = (request.POST.get('start_minute') or '').strip()
        raw_period = (request.POST.get('start_period') or '').strip().upper()
        raw_end_hour = (request.POST.get('end_hour') or '').strip()
        raw_end_minute = (request.POST.get('end_minute') or '').strip()
        raw_end_period = (request.POST.get('end_period') or '').strip().upper()

        try:
            selected_date = date.fromisoformat(raw_date)
        except ValueError:
            selected_date = today
            date_error = 'Fecha invalida. Usa el formato correcto.'
        else:
            if selected_date > today:
                selected_date = today
                date_error = 'La fecha no puede ser posterior a hoy.'

        selected_hour = raw_hour or selected_hour
        selected_minute = raw_minute if raw_minute else selected_minute
        selected_period = raw_period if raw_period in ['AM', 'PM'] else selected_period
        selected_end_hour = raw_end_hour or selected_end_hour
        selected_end_minute = raw_end_minute if raw_end_minute else selected_end_minute
        selected_end_period = raw_end_period if raw_end_period in ['AM', 'PM'] else selected_end_period

        selected_time_obj = None
        selected_end_time_obj = None

        try:
            hour_12 = int(selected_hour)
            minute_value = int(selected_minute)

            if hour_12 < 1 or hour_12 > 12:
                raise ValueError
            if minute_value < 0 or minute_value > 59:
                raise ValueError

            hour_24 = hour_12 % 12
            if selected_period == 'PM':
                hour_24 += 12

            selected_time_obj = time(hour_24, minute_value)

            if selected_date == today and selected_time_obj > current_time_obj:
                time_error = 'La hora no puede ser posterior a la hora actual.'
        except ValueError:
            time_error = 'Hora invalida. Verifica hora, minutos y periodo AM/PM.'

        try:
            end_hour_12 = int(selected_end_hour)
            end_minute_value = int(selected_end_minute)

            if end_hour_12 < 1 or end_hour_12 > 12:
                raise ValueError
            if end_minute_value < 0 or end_minute_value > 59:
                raise ValueError

            end_hour_24 = end_hour_12 % 12
            if selected_end_period == 'PM':
                end_hour_24 += 12

            selected_end_time_obj = time(end_hour_24, end_minute_value)
        except ValueError:
            end_time_error = 'Hora de finalizacion invalida. Verifica hora, minutos y periodo AM/PM.'

        if not time_error and not end_time_error and selected_time_obj and selected_end_time_obj:
            if selected_end_time_obj <= selected_time_obj:
                end_time_error = 'La hora de finalizacion debe ser posterior a la hora de inicio.'

        raw_selected_exercises = (request.POST.get('selected_exercises_json') or '[]').strip()
        try:
            selected_exercises_payload = json.loads(raw_selected_exercises)
        except json.JSONDecodeError:
            selected_exercises_payload = []
            selected_exercises_error = 'Formato invalido de ejercicios seleccionados.'

        if not selected_exercises_error:
            if not isinstance(selected_exercises_payload, list) or len(selected_exercises_payload) == 0:
                selected_exercises_error = 'Debes agregar al menos un ejercicio al registro.'
            else:
                for exercise_payload in selected_exercises_payload:
                    if not isinstance(exercise_payload, dict):
                        selected_exercises_error = 'Formato invalido de ejercicios seleccionados.'
                        break

                    if not exercise_payload.get('tracks_weight'):
                        continue

                    sets_payload = exercise_payload.get('sets') or []
                    if not sets_payload:
                        selected_exercises_error = (
                            f"El ejercicio '{exercise_payload.get('name', 'desconocido')}' debe tener al menos una serie."
                        )
                        break

                    missing_weight = any(
                        str((set_item or {}).get('weight', '')).strip() == ''
                        for set_item in sets_payload
                    )
                    if missing_weight:
                        selected_exercises_error = (
                            f"Debes ingresar el peso en todas las series de '{exercise_payload.get('name', 'desconocido')}'."
                        )
                        break

        # TODO: Cuando se implemente el guardado del registro, usar selected_date, selected_time_obj y selected_end_time_obj.

    routines = _get_user_routines_queryset(request.user)
    active_exercises = Exercise.objects.filter(is_active=True).select_related('muscle_group').order_by(Lower('name'))

    routines_data = [
        {
            'id': routine.id,
            'name': routine.name,
            'exercises': [
                {
                    'id': item.exercise.id,
                    'name': item.exercise.name,
                    'muscle_group': item.exercise.muscle_group.name if item.exercise.muscle_group else 'General',
                    'tracks_weight': item.exercise.tracks_weight,
                    'recommended_sets': item.recommended_sets,
                    'recommended_reps': item.recommended_reps,
                }
                for item in routine.items.all()
            ]
        }
        for routine in routines
    ]

    exercises_data = [
        {
            'id': exercise.id,
            'name': exercise.name,
            'muscle_group': exercise.muscle_group.name if exercise.muscle_group else 'General',
            'tracks_weight': exercise.tracks_weight,
            'recommended_sets': 3,
            'recommended_reps': 10,
        }
        for exercise in active_exercises
    ]

    return render(request, 'workouts/add_record.html', {
        'today_date': today.isoformat(),
        'selected_date': selected_date.isoformat(),
        'selected_hour': selected_hour,
        'selected_minute': selected_minute,
        'selected_period': selected_period,
        'selected_end_hour': selected_end_hour,
        'selected_end_minute': selected_end_minute,
        'selected_end_period': selected_end_period,
        'hour_options': range(1, 13),
        'minute_options': range(0, 60),
        'current_time_display': current_time_obj.strftime('%I:%M %p'),
        'date_error': date_error,
        'time_error': time_error,
        'end_time_error': end_time_error,
        'selected_exercises_error': selected_exercises_error,
        'routines': routines,
        'active_exercises': active_exercises,
        'routines_data': routines_data,
        'exercises_data': exercises_data,
    })