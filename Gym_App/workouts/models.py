from django.db import models
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io
import sys

# ==============================================================================
# TAXONOMÍA Y CATÁLOGO GLOBAL (Público / Compartido)
# ==============================================================================

class MovementPattern(models.Model):
    """Ej: Push, Pull, Piernas, Core, Full Body"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MuscleGroup(models.Model):
    """Ej: Pecho, Espalda, Cuádriceps. Obligatoriamente pertenece a un Patrón."""
    pattern = models.ForeignKey(MovementPattern, on_delete=models.CASCADE, related_name='muscle_groups')
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} ({self.pattern.name})"

class Exercise(models.Model):
    """
    Catálogo global. Cualquier usuario puede crearlo, pero una vez creado
    pertenece al pool global de la aplicación.
    """
    # Se usa created_by como auditoría, pero no limita el acceso (todos lo ven).
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.PROTECT) # PROTECT evita borrar un músculo si tiene ejercicios
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True, help_text="Instrucciones o notas de ejecución.")
    image = models.ImageField(upload_to='exercise_images/', blank=True, null=True)
    tracks_weight = models.BooleanField(default=True, help_text="¿Requiere registrar peso?")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            img = Image.open(self.image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            self.image = InMemoryUploadedFile(
                output, 'ImageField', f"{self.image.name.split('.')[0]}.jpg", 
                'image/jpeg', sys.getsizeof(output), None
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# ==============================================================================
# PLANTILLAS DE USUARIO (Gestión de Privacidad)
# ==============================================================================

class Routine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    is_public = models.BooleanField(default=False, help_text="Si es True, otros usuarios podrán ver y clonar esta rutina.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class RoutineItem(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='items')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    recommended_sets = models.PositiveIntegerField(default=3)
    recommended_reps = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

# ==============================================================================
# DATOS TRANSACCIONALES (Estrictamente Privados)
# ==============================================================================

class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

class CardioLog(models.Model):
    PHASE_CHOICES = [('WARMUP', 'Calentamiento'), ('COOLDOWN', 'Cardio Final')]
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='cardio_logs')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES)
    duration_minutes = models.PositiveIntegerField()
    distance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    elevation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    steps = models.PositiveIntegerField(null=True, blank=True)

class ExerciseLog(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercise_logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class SetRecord(models.Model):
    exercise_log = models.ForeignKey(ExerciseLog, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveIntegerField()
    reps_done = models.PositiveIntegerField()
    weight_lifted = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)