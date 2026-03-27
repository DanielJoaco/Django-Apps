from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    # En iteraciones futuras, aquí se consultará la base de datos (SQLite)
    # para enviar el contexto estadístico a la plantilla.
    return render(request, 'dashboard.html')