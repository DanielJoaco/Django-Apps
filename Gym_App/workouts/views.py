# workouts/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Exercise, Category, Routine, RoutineItem
from .forms import RoutineForm, ExerciseAsyncForm

@login_required
def create_routine_view(request):
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
                # Extracción dinámica de los valores de series y repeticiones basados en el ID del ejercicio
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
                    continue # Mecanismo de tolerancia a fallos si un ID es manipulado en el cliente

            return redirect('dashboard') 
            
    else:
        routine_form = RoutineForm()
        exercise_form = ExerciseAsyncForm()

    return render(request, 'workouts/create_routine.html', {
        'routine_form': routine_form,
        'exercise_form': exercise_form
    })

@login_required
def search_exercises_api(request):
    query = request.GET.get('q', '')
    if query:
        exercises = Exercise.objects.filter(name__icontains=query).filter(
            user=request.user
        ) | Exercise.objects.filter(name__icontains=query, user__isnull=True)
        
        results = [{'id': ex.id, 'name': ex.name, 'category': ex.category.name if ex.category else 'General'} for ex in exercises[:10]]
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})

@login_required
def routines_view(request):
    routines = Routine.objects.filter(user=request.user).prefetch_related('items__exercise')
    return render(request, 'workouts/routines.html', {'routines': routines})

@login_required
def create_exercise_api(request):
    """
    Endpoint diseñado para recibir peticiones POST vía Fetch API con carga de archivos (Multipart).
    """
    if request.method == 'POST':
        form = ExerciseAsyncForm(request.POST, request.FILES)
        if form.is_valid():
            # Lógica para resolver la categoría
            category = form.cleaned_data.get('category')
            new_cat_name = form.cleaned_data.get('new_category')
            
            if not category and new_cat_name:
                # get_or_create evita excepciones de duplicidad si el usuario escribe una categoría que ya existe globalmente
                category, created = Category.objects.get_or_create(
                    name__iexact=new_cat_name, 
                    defaults={'name': new_cat_name, 'user': request.user}
                )

            exercise = form.save(commit=False)
            exercise.user = request.user
            exercise.category = category
            # Al invocar save(), se detona el polimorfismo definido en models.py que ejecuta Pillow
            exercise.save() 
            
            return JsonResponse({'success': True, 'id': exercise.id, 'name': exercise.name})
        else:
            # Retorno estructurado de errores de validación
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

@login_required
def list_routines_view(request):
    # Optimización: Extrae las rutinas y pre-carga la tabla intermedia, el ejercicio y la categoría en 2 consultas SQL totales.
    routines = Routine.objects.filter(user=request.user).prefetch_related(
        'items__exercise__category'
    )
    return render(request, 'workouts/routines.html', {'routines': routines})