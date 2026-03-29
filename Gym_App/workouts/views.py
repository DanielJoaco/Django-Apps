# workouts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
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
    )


def routines_list(request):
    """Colección reutilizable de rutinas para inyectar en distintos templates."""
    return _get_user_routines_queryset(request.user)

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