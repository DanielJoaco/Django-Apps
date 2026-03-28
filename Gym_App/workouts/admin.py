from django.contrib import admin
from .models import MovementPattern, MuscleGroup, Exercise, Routine, RoutineItem, WorkoutSession, CardioLog, ExerciseLog, SetRecord

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
    list_display = ('name', 'muscle_group', 'tracks_weight', 'is_active', 'created_by')
    # Permite filtrar por patrón de movimiento a través de la relación de la llave foránea
    list_filter = ('muscle_group__pattern', 'muscle_group', 'tracks_weight', 'is_active')
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

class CardioLogInline(admin.TabularInline):
    model = CardioLog
    extra = 0

class ExerciseLogInline(admin.TabularInline):
    model = ExerciseLog
    extra = 0

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'start_time', 'end_time')
    list_filter = ('start_time', 'user')
    inlines = [CardioLogInline, ExerciseLogInline]

class SetRecordInline(admin.TabularInline):
    model = SetRecord
    extra = 1

@admin.register(ExerciseLog)
class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ('session', 'exercise', 'order')
    inlines = [SetRecordInline]