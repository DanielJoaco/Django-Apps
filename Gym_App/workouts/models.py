from django.db import models
from django.contrib.auth.models import User

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
    EXERCISE_TYPE_STRENGTH = 'STRENGTH'
    EXERCISE_TYPE_CARDIO = 'CARDIO'
    EXERCISE_TYPE_FULL_BODY = 'FULL_BODY'
    EXERCISE_TYPE_CHOICES = [
        (EXERCISE_TYPE_STRENGTH, 'Fuerza'),
        (EXERCISE_TYPE_CARDIO, 'Cardiovascular'),
        (EXERCISE_TYPE_FULL_BODY, 'Cuerpo Completo'),
    ]

    # Se usa created_by como auditoría, pero no limita el acceso (todos lo ven).
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.PROTECT) # PROTECT evita borrar un músculo si tiene ejercicios
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True, help_text="Instrucciones o notas de ejecución.")
    image = models.URLField(blank=True, null=True)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES, default=EXERCISE_TYPE_STRENGTH)
    tracks_weight = models.BooleanField(default=True, help_text="¿Requiere registrar peso?")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def _normalize_text(value):
        return str(value or '').strip().lower()

    def _sync_exercise_type_from_muscle_group(self):
        normalized_group_name = self._normalize_text(self.muscle_group.name if self.muscle_group else '')

        if normalized_group_name == 'cardiovascular':
            self.exercise_type = self.EXERCISE_TYPE_CARDIO
            self.tracks_weight = False
            return

        if normalized_group_name == 'cuerpo completo':
            self.exercise_type = self.EXERCISE_TYPE_FULL_BODY
            self.tracks_weight = False
            return

        self.exercise_type = self.EXERCISE_TYPE_STRENGTH

    def save(self, *args, **kwargs):
        self._sync_exercise_type_from_muscle_group()
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Sesion de {self.user.username} ({self.started_at:%Y-%m-%d %H:%M})"


class SessionExerciseEntry(models.Model):
    PHASE_WARMUP = 'WARMUP'
    PHASE_MAIN = 'MAIN'
    PHASE_COOLDOWN = 'COOLDOWN'
    PHASE_CHOICES = [
        (PHASE_WARMUP, 'Calentamiento'),
        (PHASE_MAIN, 'Principal'),
        (PHASE_COOLDOWN, 'Cardio Final'),
    ]

    ENTRY_TYPE_STRENGTH = 'STRENGTH'
    ENTRY_TYPE_CARDIO = 'CARDIO'
    ENTRY_TYPE_FULL_BODY = 'FULL_BODY'
    ENTRY_TYPE_CHOICES = [
        (ENTRY_TYPE_STRENGTH, 'Fuerza'),
        (ENTRY_TYPE_CARDIO, 'Cardio'),
        (ENTRY_TYPE_FULL_BODY, 'Cuerpo Completo'),
    ]

    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='entries')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name='session_entries')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, default=PHASE_MAIN)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.exercise.name} - {self.get_phase_display()}"


class StrengthSetEntry(models.Model):
    entry = models.ForeignKey(SessionExerciseEntry, on_delete=models.CASCADE, related_name='strength_sets')
    set_number = models.PositiveIntegerField()
    reps_done = models.PositiveIntegerField()
    weight_lifted = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['set_number']
        constraints = [
            models.UniqueConstraint(fields=['entry', 'set_number'], name='unique_strength_set_per_entry'),
        ]


class CardioEntry(models.Model):
    UNIT_STEPS = 'steps'
    UNIT_KM = 'km'
    DISTANCE_UNIT_CHOICES = [
        (UNIT_STEPS, 'Pasos'),
        (UNIT_KM, 'Kilometros'),
    ]

    entry = models.OneToOneField(SessionExerciseEntry, on_delete=models.CASCADE, related_name='cardio_data')
    duration_seconds = models.PositiveIntegerField()
    distance_value = models.DecimalField(max_digits=10, decimal_places=2)
    distance_unit = models.CharField(max_length=10, choices=DISTANCE_UNIT_CHOICES)


class FullBodyEntry(models.Model):
    TRACK_NONE = 'NONE'
    TRACK_TIME = 'TIME'
    TRACK_SETS_REPS = 'SETS_REPS'
    TRACKING_MODE_CHOICES = [
        (TRACK_NONE, 'Solo marcar ejercicio'),
        (TRACK_TIME, 'Tiempo total'),
        (TRACK_SETS_REPS, 'Series y repeticiones'),
    ]

    entry = models.OneToOneField(SessionExerciseEntry, on_delete=models.CASCADE, related_name='full_body_data')
    tracking_mode = models.CharField(max_length=20, choices=TRACKING_MODE_CHOICES, default=TRACK_NONE)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    sets_done = models.PositiveIntegerField(null=True, blank=True)
    reps_done = models.PositiveIntegerField(null=True, blank=True)


