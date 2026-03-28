from django import forms
from .models import Routine, Exercise, Category

class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej. Día de Empuje',
                'autocomplete': 'off'
            })
        }

class ExerciseAsyncForm(forms.ModelForm):
    """
    Formulario destinado a ser procesado de manera asíncrona (AJAX) 
    para la creación de ejercicios al vuelo.
    """
    # Campo adicional para manejar la creación de una categoría nueva si no se elige una existente
    new_category = forms.CharField(
        max_length=100, 
        required=False, 
        help_text="Escribe el nombre de una nueva categoría si no encuentras la deseada."
    )

    class Meta:
        model = Exercise
        fields = ['category', 'name', 'image', 'tracks_weight']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del ejercicio'}),
            'tracks_weight': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category_name = cleaned_data.get('new_category')

        # Regla de negocio: Debe existir una categoría existente O el nombre para una nueva
        if not category and not new_category_name:
            raise forms.ValidationError("Debes seleccionar una categoría existente o escribir una nueva.")
        
        return cleaned_data