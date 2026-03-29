from django import forms
from .models import Routine, Exercise, MuscleGroup

class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        fields = ['name', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Día de Empuje', 'autocomplete': 'off'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class ExerciseAsyncForm(forms.ModelForm):
    """
    Formulario asíncrono. El usuario ahora debe elegir obligatoriamente 
    un grupo muscular del catálogo global existente.
    """
    class Meta:
        model = Exercise
        fields = ['muscle_group', 'name', 'image', 'tracks_weight']
        widgets = {
            'muscle_group': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del ejercicio'}),
            'image': forms.FileInput(attrs={'class': 'custom-file-input'}),
            'tracks_weight': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }