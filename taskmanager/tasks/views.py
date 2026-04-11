from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import TaskForm
from .models import Task

# Create your views here.
def index(request):
    return render(request, 'index.html')

def tasks_list(request):
    tasks = Task.objects.all()
    
    return render(request, 'tasks/task_list.html', {'tasks': tasks})

def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tasks_list')
    else:
        form = TaskForm()

    return render(request, 'tasks/create.html', {'form': form, 'action': 'crear'})

def task_update(request, pk):
    task = Task.objects.get(pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('tasks_list')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/create.html', {'form': form, 'action': 'editar'})


@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.delete()
    return redirect('tasks_list')