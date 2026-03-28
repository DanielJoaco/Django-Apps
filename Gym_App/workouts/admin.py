# workouts/admin.py
from django.contrib import admin
from .models import Category, Exercise, Routine, RoutineItem, WorkoutSession, CardioLog, ExerciseLog, SetRecord

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name',)
    list_filter = ('user',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    # Columnas visibles en la tabla principal
    list_display = ('name', 'category', 'tracks_weight', 'is_active', 'user')
    # Filtros laterales
    list_filter = ('category', 'tracks_weight', 'is_active')
    search_fields = ('name',)

# --- Configuración de Inlines para Relaciones 1:N ---

class RoutineItemInline(admin.TabularInline):
    model = RoutineItem
    extra = 1 # Muestra por defecto 1 fila vacía para agregar rápidamente

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    inlines = [RoutineItemInline] # Incrusta la tabla de items dentro de la rutina

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