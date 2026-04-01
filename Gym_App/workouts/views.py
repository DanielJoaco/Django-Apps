# workouts/views.py
import json
import unicodedata

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.functions import Lower
from django.utils import timezone
from datetime import date, time, datetime
from decimal import Decimal, InvalidOperation
from .models import (
    Exercise,
    Routine,
    RoutineItem,
    WorkoutSession,
    SessionExerciseEntry,
    StrengthSetEntry,
    CardioEntry,
    FullBodyEntry,
)
from .forms import RoutineForm, ExerciseAsyncForm


def _normalize_text(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return text.lower().strip()


def _exercise_search_text(exercise):
    muscle_group_name = exercise.muscle_group.name if exercise.muscle_group else ''
    pattern_name = (
        exercise.muscle_group.pattern.name
        if exercise.muscle_group and getattr(exercise.muscle_group, 'pattern', None)
        else ''
    )
    return _normalize_text(f"{exercise.name} {muscle_group_name} {pattern_name}")


def _is_cardio_exercise(exercise):
    search_text = _exercise_search_text(exercise)
    cardio_keywords = [
        'cardio', 'caminata', 'caminar', 'trote', 'correr', 'running',
        'bicicleta', 'bike', 'eliptica', 'escalera', 'steps', 'step',
        'remo', 'saltar la cuerda', 'jump rope', 'hiit', 'aerobico',
    ]
    return any(keyword in search_text for keyword in cardio_keywords)


def _is_stretching_exercise(exercise):
    search_text = _exercise_search_text(exercise)
    stretching_keywords = ['estiramiento', 'stretch', 'movilidad', 'flexibilidad']
    return any(keyword in search_text for keyword in stretching_keywords)


def _matches_muscle_group(exercise, expected_group_name):
    current_group_name = exercise.muscle_group.name if exercise.muscle_group else ''
    return _normalize_text(current_group_name) == _normalize_text(expected_group_name)


def _infer_exercise_type(exercise):
    group_name = _normalize_text(exercise.muscle_group.name if exercise.muscle_group else '')
    if group_name == 'cardiovascular':
        return Exercise.EXERCISE_TYPE_CARDIO
    if group_name == 'cuerpo completo':
        return Exercise.EXERCISE_TYPE_FULL_BODY
    return Exercise.EXERCISE_TYPE_STRENGTH


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
            if _infer_exercise_type(exercise_instance) != Exercise.EXERCISE_TYPE_STRENGTH:
                continue
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
        if _infer_exercise_type(item.exercise) == Exercise.EXERCISE_TYPE_STRENGTH
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
        # Búsqueda global filtrada a fuerza para evitar rutinas con cardio/full body.
        exercises = Exercise.objects.filter(
            name__icontains=query,
            is_active=True,
            exercise_type=Exercise.EXERCISE_TYPE_STRENGTH,
        )
        
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
        form = ExerciseAsyncForm(request.POST)
        if form.is_valid():
            # El formulario ya valida el muscle_group obligatoriamente
            exercise = form.save(commit=False)
            # Registramos qué usuario aportó este ejercicio al sistema
            exercise.created_by = request.user 
            exercise.save() 
            
            return JsonResponse({
                'success': True,
                'id': exercise.id,
                'name': exercise.name,
                'exercise_type': exercise.exercise_type,
                'muscle_group': exercise.muscle_group.name if exercise.muscle_group else 'General',
            })
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
    strength_entries = (
        SessionExerciseEntry.objects
        .filter(
            session__user=request.user,
            entry_type=SessionExerciseEntry.ENTRY_TYPE_STRENGTH,
        )
        .select_related('exercise', 'session')
        .prefetch_related('strength_sets')
        .order_by('-session__started_at', '-id')[:50]
    )

    records = []
    for entry in strength_entries:
        sets = list(entry.strength_sets.all())
        sets_count = len(sets)
        reps_total = sum(set_item.reps_done for set_item in sets)
        weights = [set_item.weight_lifted for set_item in sets if set_item.weight_lifted is not None]
        max_weight = max(weights) if weights else Decimal('0')

        records.append({
            'exercise': entry.exercise,
            'date': timezone.localtime(entry.session.started_at).date(),
            'sets': sets_count,
            'reps': reps_total,
            'weight': max_weight,
        })

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
    warmup_error = None
    cooldown_error = None

    def to_aware_datetime(base_date, base_time):
        naive_dt = datetime.combine(base_date, base_time)
        if timezone.is_naive(naive_dt):
            return timezone.make_aware(naive_dt, timezone.get_current_timezone())
        return naive_dt

    def to_positive_int(value):
        parsed = int(value)
        if parsed <= 0:
            raise ValueError
        return parsed

    def to_positive_decimal(value):
        parsed = Decimal(str(value))
        if parsed <= 0:
            raise InvalidOperation
        return parsed

    def parse_mmss_to_seconds(value):
        raw_value = str(value or '').strip()
        parts = raw_value.split(':')
        if len(parts) != 2:
            raise ValueError

        minutes_str, seconds_str = parts
        if not minutes_str.isdigit() or not seconds_str.isdigit():
            raise ValueError

        minutes_value = int(minutes_str)
        seconds_value = int(seconds_str)
        if minutes_value < 0 or seconds_value < 0 or seconds_value > 59:
            raise ValueError

        total_seconds = (minutes_value * 60) + seconds_value
        if total_seconds <= 0:
            raise ValueError
        return total_seconds

    def validate_main_selected_exercises(raw_selected_exercises):
        try:
            selected_exercises_payload = json.loads(raw_selected_exercises)
        except json.JSONDecodeError:
            return None, 'Formato invalido de ejercicios seleccionados.'

        if not isinstance(selected_exercises_payload, list) or len(selected_exercises_payload) == 0:
            return None, 'Debes agregar al menos un ejercicio al registro.'

        for exercise_payload in selected_exercises_payload:
            if not isinstance(exercise_payload, dict):
                return None, 'Formato invalido de ejercicios seleccionados.'

            exercise_id = exercise_payload.get('id')
            if exercise_id is None:
                return None, 'Formato invalido de ejercicios seleccionados.'

            try:
                exercise = exercises_by_id[int(exercise_id)]
            except (ValueError, TypeError, KeyError):
                return None, 'Uno de los ejercicios seleccionados no existe o esta inactivo.'

            if _infer_exercise_type(exercise) != Exercise.EXERCISE_TYPE_STRENGTH:
                return None, f"El ejercicio '{exercise.name}' debe registrarse en su bloque correspondiente."

            sets_payload = exercise_payload.get('sets') or []
            if not isinstance(sets_payload, list) or len(sets_payload) == 0:
                return None, f"El ejercicio '{exercise.name}' debe tener al menos una serie."

            for set_item in sets_payload:
                if not isinstance(set_item, dict):
                    return None, f"Formato invalido en las series de '{exercise.name}'."

                try:
                    reps_value = to_positive_int(set_item.get('value'))
                except (TypeError, ValueError):
                    return None, f"Las repeticiones/segundos de '{exercise.name}' deben ser mayores a cero."

                set_item['value'] = reps_value

                if not exercise.tracks_weight:
                    continue

                raw_weight = str(set_item.get('weight', '')).strip()
                if raw_weight == '':
                    return None, f"Debes ingresar el peso en todas las series de '{exercise.name}'."

                try:
                    set_item['weight'] = to_positive_decimal(raw_weight)
                except (InvalidOperation, TypeError, ValueError):
                    return None, f"El peso de '{exercise.name}' debe ser mayor a cero."

        return selected_exercises_payload, None

    def validate_phase_payload(raw_payload, phase_label):
        try:
            payload = json.loads((raw_payload or '{}').strip() or '{}')
        except json.JSONDecodeError:
            return f'Formato invalido para {phase_label}.', {}

        if not isinstance(payload, dict):
            return f'Formato invalido para {phase_label}.', {}

        enabled = bool(payload.get('enabled'))
        include_cardio = bool(payload.get('include_cardio'))
        include_stretching = bool(payload.get('include_stretching'))

        if not enabled:
            return None, payload

        if not include_cardio and not include_stretching:
            return (
                f'Debes seleccionar al menos cardio o estiramiento en {phase_label}.',
                payload,
            )

        if include_cardio:
            cardio_entries = payload.get('cardio_entries') or []
            if not isinstance(cardio_entries, list) or len(cardio_entries) == 0:
                return f'Debes seleccionar al menos un ejercicio de cardio en {phase_label}.', payload

            for cardio_entry in cardio_entries:
                if not isinstance(cardio_entry, dict):
                    return f'Formato invalido en ejercicios de cardio para {phase_label}.', payload

                exercise_id = cardio_entry.get('exercise_id')
                try:
                    exercise = exercises_by_id[int(exercise_id)]
                except (ValueError, TypeError, KeyError):
                    return f'Hay un ejercicio de cardio invalido en {phase_label}.', payload

                if _infer_exercise_type(exercise) != Exercise.EXERCISE_TYPE_CARDIO:
                    return f"El ejercicio '{exercise.name}' no pertenece a la categoria cardiovascular.", payload

                unit = str(cardio_entry.get('unit') or '').strip().lower()
                duration_mmss = cardio_entry.get('duration_mmss')
                distance_value = cardio_entry.get('distance_value')

                if unit not in ['steps', 'km']:
                    return f'Unidad invalida en cardio de {phase_label}.', payload

                try:
                    parsed_duration = parse_mmss_to_seconds(duration_mmss)
                    parsed_distance = to_positive_decimal(distance_value)
                except (TypeError, ValueError, InvalidOperation):
                    return f'Debes registrar tiempo valido (mm:ss) y distancia valida en cardio de {phase_label}.', payload

                cardio_entry['exercise_id'] = int(exercise_id)
                cardio_entry['duration_seconds'] = parsed_duration
                cardio_entry['distance_value'] = parsed_distance

        if include_stretching:
            full_body_entries = payload.get('full_body_entries') or []

            if not full_body_entries:
                # Compatibilidad con payload viejo basado en IDs simples.
                stretching_ids = payload.get('stretching_ids') or []
                full_body_entries = [
                    {
                        'exercise_id': stretching_id,
                        'tracking_mode': FullBodyEntry.TRACK_NONE,
                        'duration_seconds': None,
                        'sets_done': None,
                        'reps_done': None,
                    }
                    for stretching_id in stretching_ids
                ]

            if not isinstance(full_body_entries, list) or len(full_body_entries) == 0:
                return f'Debes seleccionar al menos un ejercicio de estiramiento en {phase_label}.', payload

            normalized_full_body_entries = []
            for full_body_entry in full_body_entries:
                if not isinstance(full_body_entry, dict):
                    return f'Formato invalido en ejercicios de estiramiento para {phase_label}.', payload

                exercise_id = full_body_entry.get('exercise_id')
                try:
                    exercise = exercises_by_id[int(exercise_id)]
                except (ValueError, TypeError, KeyError):
                    return f'Hay un ejercicio de estiramiento invalido en {phase_label}.', payload

                if _infer_exercise_type(exercise) != Exercise.EXERCISE_TYPE_FULL_BODY:
                    return f"El ejercicio '{exercise.name}' no pertenece a la categoria Cuerpo Completo.", payload

                tracking_mode = str(
                    full_body_entry.get('tracking_mode') or FullBodyEntry.TRACK_NONE,
                ).strip().upper()

                if tracking_mode not in [
                    FullBodyEntry.TRACK_NONE,
                    FullBodyEntry.TRACK_TIME,
                    FullBodyEntry.TRACK_SETS_REPS,
                ]:
                    return f'Modo de registro invalido para estiramiento en {phase_label}.', payload

                normalized_entry = {
                    'exercise_id': int(exercise_id),
                    'tracking_mode': tracking_mode,
                    'duration_seconds': None,
                    'sets_done': None,
                    'reps_done': None,
                }

                if tracking_mode == FullBodyEntry.TRACK_TIME:
                    try:
                        normalized_entry['duration_seconds'] = parse_mmss_to_seconds(
                            full_body_entry.get('duration_mmss'),
                        )
                    except (TypeError, ValueError):
                        return f'Debes registrar tiempo valido (mm:ss) en estiramiento de {phase_label}.', payload

                if tracking_mode == FullBodyEntry.TRACK_SETS_REPS:
                    try:
                        normalized_entry['sets_done'] = to_positive_int(
                            full_body_entry.get('sets_done'),
                        )
                        normalized_entry['reps_done'] = to_positive_int(
                            full_body_entry.get('reps_done'),
                        )
                    except (TypeError, ValueError):
                        return f'Debes registrar series y repeticiones validas en estiramiento de {phase_label}.', payload

                normalized_full_body_entries.append(normalized_entry)

            payload['full_body_entries'] = normalized_full_body_entries

        return None, payload

    def save_phase_entries(session, phase, payload):
        if not payload.get('enabled'):
            return

        order = 1

        if payload.get('include_cardio'):
            for cardio_entry in payload.get('cardio_entries', []):
                exercise = exercises_by_id[cardio_entry['exercise_id']]
                entry = SessionExerciseEntry.objects.create(
                    session=session,
                    exercise=exercise,
                    phase=phase,
                    entry_type=SessionExerciseEntry.ENTRY_TYPE_CARDIO,
                    order=order,
                )
                CardioEntry.objects.create(
                    entry=entry,
                    duration_seconds=cardio_entry['duration_seconds'],
                    distance_value=cardio_entry['distance_value'],
                    distance_unit=cardio_entry['unit'],
                )
                order += 1

        if payload.get('include_stretching'):
            for full_body_entry in payload.get('full_body_entries', []):
                exercise = exercises_by_id[full_body_entry['exercise_id']]
                entry = SessionExerciseEntry.objects.create(
                    session=session,
                    exercise=exercise,
                    phase=phase,
                    entry_type=SessionExerciseEntry.ENTRY_TYPE_FULL_BODY,
                    order=order,
                )
                FullBodyEntry.objects.create(
                    entry=entry,
                    tracking_mode=full_body_entry['tracking_mode'],
                    duration_seconds=full_body_entry.get('duration_seconds'),
                    sets_done=full_body_entry.get('sets_done'),
                    reps_done=full_body_entry.get('reps_done'),
                )
                order += 1

    active_exercises = Exercise.objects.filter(is_active=True).select_related(
        'muscle_group',
        'muscle_group__pattern',
    ).order_by(Lower('name'))
    exercises_by_id = {exercise.id: exercise for exercise in active_exercises}

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
        selected_exercises_payload, selected_exercises_error = validate_main_selected_exercises(
            raw_selected_exercises,
        )

        warmup_error, warmup_payload = validate_phase_payload(
            request.POST.get('warmup_details_json'),
            'calentamiento',
        )
        cooldown_error, cooldown_payload = validate_phase_payload(
            request.POST.get('cooldown_details_json'),
            'cardio final',
        )

        if not any([date_error, time_error, end_time_error, selected_exercises_error, warmup_error, cooldown_error]):
            session_start = to_aware_datetime(selected_date, selected_time_obj)
            session_end = to_aware_datetime(selected_date, selected_end_time_obj)

            with transaction.atomic():
                session = WorkoutSession.objects.create(
                    user=request.user,
                    started_at=session_start,
                    ended_at=session_end,
                )

                for order, exercise_payload in enumerate(selected_exercises_payload, start=1):
                    exercise = exercises_by_id[int(exercise_payload['id'])]
                    entry = SessionExerciseEntry.objects.create(
                        session=session,
                        exercise=exercise,
                        phase=SessionExerciseEntry.PHASE_MAIN,
                        entry_type=SessionExerciseEntry.ENTRY_TYPE_STRENGTH,
                        order=order,
                    )

                    for set_item in exercise_payload.get('sets', []):
                        weight_value = set_item.get('weight') if exercise.tracks_weight else None
                        StrengthSetEntry.objects.create(
                            entry=entry,
                            set_number=int(set_item.get('set_number') or 1),
                            reps_done=int(set_item['value']),
                            weight_lifted=weight_value,
                        )

                save_phase_entries(session, SessionExerciseEntry.PHASE_WARMUP, warmup_payload)
                save_phase_entries(session, SessionExerciseEntry.PHASE_COOLDOWN, cooldown_payload)

            return redirect('workouts:records')

    routines = _get_user_routines_queryset(request.user)
    strength_exercises = [
        exercise for exercise in active_exercises
        if _infer_exercise_type(exercise) == Exercise.EXERCISE_TYPE_STRENGTH
    ]

    cardio_exercises_data = [
        {
            'id': exercise.id,
            'name': exercise.name,
            'muscle_group': exercise.muscle_group.name if exercise.muscle_group else 'General',
        }
        for exercise in active_exercises
        if _matches_muscle_group(exercise, 'Cardiovascular')
    ]

    stretching_exercises_data = [
        {
            'id': exercise.id,
            'name': exercise.name,
            'muscle_group': exercise.muscle_group.name if exercise.muscle_group else 'General',
        }
        for exercise in active_exercises
        if _matches_muscle_group(exercise, 'Cuerpo Completo')
    ]

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
                if _infer_exercise_type(item.exercise) == Exercise.EXERCISE_TYPE_STRENGTH
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
        for exercise in strength_exercises
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
        'warmup_error': warmup_error,
        'cooldown_error': cooldown_error,
        'routines': routines,
        'active_exercises': strength_exercises,
        'routines_data': routines_data,
        'exercises_data': exercises_data,
        'cardio_exercises_data': cardio_exercises_data,
        'stretching_exercises_data': stretching_exercises_data,
    })