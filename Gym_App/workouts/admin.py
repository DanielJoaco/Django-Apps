from django.contrib import admin
from .models import (
    MovementPattern,
    MuscleGroup,
    Exercise,
    Routine,
    RoutineItem,
    WorkoutSession,
    SessionExerciseEntry,
    StrengthSetEntry,
    CardioEntry,
    FullBodyEntry,
)

# ==============================================================================
# TAXONOMÍA Y CATÁLOGO GLOBAL
# ==============================================================================

@admin.register(MovementPattern)
class MovementPatternAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'pattern')
    list_filter = ('pattern',)
    search_fields = ('name',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'muscle_group', 'exercise_type', 'tracks_weight', 'is_active', 'created_by')
    # Permite filtrar por patrón de movimiento a través de la relación de la llave foránea
    list_filter = ('muscle_group__pattern', 'muscle_group', 'exercise_type', 'tracks_weight', 'is_active')
    search_fields = ('name',)

# ==============================================================================
# PLANTILLAS DE USUARIO
# ==============================================================================

class RoutineItemInline(admin.TabularInline):
    model = RoutineItem
    extra = 1

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'created_at')
    list_filter = ('is_public', 'user')
    search_fields = ('name', 'user__username')
    inlines = [RoutineItemInline]

# ==============================================================================
# DATOS TRANSACCIONALES
# ==============================================================================

class SessionExerciseEntryInline(admin.TabularInline):
    model = SessionExerciseEntry
    extra = 0

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'started_at', 'ended_at')
    list_filter = ('started_at', 'user')
    inlines = [SessionExerciseEntryInline]

class StrengthSetEntryInline(admin.TabularInline):
    model = StrengthSetEntry
    extra = 1

@admin.register(SessionExerciseEntry)
class SessionExerciseEntryAdmin(admin.ModelAdmin):
    list_display = ('session', 'exercise', 'phase', 'entry_type', 'order', 'created_at')
    list_filter = ('phase', 'entry_type', 'session__user')
    inlines = [StrengthSetEntryInline]


@admin.register(CardioEntry)
class CardioEntryAdmin(admin.ModelAdmin):
    list_display = ('entry', 'duration_seconds', 'distance_value', 'distance_unit')
    list_filter = ('distance_unit',)


@admin.register(FullBodyEntry)
class FullBodyEntryAdmin(admin.ModelAdmin):
    list_display = ('entry', 'tracking_mode', 'duration_seconds', 'sets_done', 'reps_done')
    list_filter = ('tracking_mode',)