from django import forms
from .models import Exercise, Agonist


class ExerciseForm(forms.ModelForm):
    agonist = forms.ModelChoiceField(
        queryset=Agonist.objects.select_related('muscle_group', 'muscle_group__pattern'),
        label="Agonista (músculo principal)",
        empty_label=None,
    )

    class Meta:
        model = Exercise
        fields = ['name', 'description', 'agonist', 'image', 'exercise_type', 'tracks_weight', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre del ejercicio',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Descripción o instrucciones',
                'rows': 5,
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
            }),
            'exercise_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'tracks_weight': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }
        labels = {
            'exercise_type': 'Tipo de ejercicio',
            'tracks_weight': 'Registra peso',
            'is_active': 'Activo',
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.cleaned_data.get('agonist'):
            self.cleaned_data['muscle_group'] = self.cleaned_data['agonist'].muscle_group
            self.cleaned_data['pattern'] = self.cleaned_data['agonist'].muscle_group.pattern
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('agonist'):
            instance.muscle_group = self.cleaned_data['agonist'].muscle_group
            instance.pattern = self.cleaned_data['agonist'].muscle_group.pattern
        if commit:
            instance.save()
        return instance
