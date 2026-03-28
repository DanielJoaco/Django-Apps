# workouts/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Exercise, Routine, RoutineItem, MuscleGroup
from .forms import RoutineForm, ExerciseAsyncForm

@login_required
def create_routine_view(request):
    """Vista principal sincrónica para ensamblar la rutina."""
    if request.method == 'POST':
        routine_form = RoutineForm(request.POST)
        
        if routine_form.is_valid():
            # 1. Guardar la entidad cabecera (Routine) pero sin hacer commit final para asignar el usuario
            routine = routine_form.save(commit=False)
            routine.user = request.user
            routine.save()
            
            # 2. Extraer el array de IDs de ejercicios generados dinámicamente en el DOM
            exercise_ids = request.POST.getlist('exercises[]')
            
            # 3. Iteración transaccional para crear los RoutineItems
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
                        order=index + 1 # Preserva el orden lógico de inserción
                    )
                except Exercise.DoesNotExist:
                    continue # Mecanismo de tolerancia a fallos

            # Redirigir a la lista de rutinas tras crearla con éxito
            return redirect('workouts:list_routines') 
            
    else:
        routine_form = RoutineForm()
        exercise_form = ExerciseAsyncForm()

    return render(request, 'workouts/create_routine.html', {
        'routine_form': routine_form,
        'exercise_form': exercise_form
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

@login_required
def list_routines_view(request):
    """Vista optimizada para listar las rutinas privadas del usuario."""
    # Pre-carga de la tabla intermedia, ejercicio y el grupo muscular para evitar el Problema N+1
    routines = Routine.objects.filter(user=request.user).prefetch_related(
        'items__exercise__muscle_group'
    )
    return render(request, 'workouts/routines.html', {'routines': routines})