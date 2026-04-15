from django.contrib import admin
from .models import Agonist, Exercise, MovementPattern, MuscleGroup


admin.site.site_header = "Wiki Gym Admin"
admin.site.site_title = "Wiki Gym Admin"
admin.site.index_title = "Administracion de ejercicios"


@admin.register(MovementPattern)
class MovementPatternAdmin(admin.ModelAdmin):
	list_display = ("name",)
	search_fields = ("name",)


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
	list_display = ("name", "pattern")
	list_filter = ("pattern",)
	search_fields = ("name", "pattern__name")


@admin.register(Agonist)
class AgonistAdmin(admin.ModelAdmin):
	list_display = ("name", "muscle_group", "get_pattern")
	list_filter = ("muscle_group__pattern", "muscle_group")
	search_fields = ("name", "muscle_group__name", "muscle_group__pattern__name")

	@staticmethod
	def get_pattern(obj):
		return obj.muscle_group.pattern.name

	get_pattern.short_description = "Division"


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
	fields = (
		"name",
		"description",
		"agonist",
		"image",
		"exercise_type",
		"tracks_weight",
		"is_active",
	)
	list_select_related = ("agonist__muscle_group__pattern",)
	list_display = (
		"name",
		"exercise_type",
		"get_pattern",
		"get_muscle_group",
		"agonist",
		"tracks_weight",
		"is_active",
	)
	list_filter = ("exercise_type", "agonist__muscle_group__pattern", "agonist__muscle_group", "is_active")
	search_fields = (
		"name",
		"description",
		"agonist__muscle_group__pattern__name",
		"agonist__muscle_group__name",
		"agonist__name",
	)
	autocomplete_fields = ("agonist",)

	@admin.display(description="Division")
	def get_pattern(self, obj):
		return obj.agonist.muscle_group.pattern

	@admin.display(description="Grupo muscular")
	def get_muscle_group(self, obj):
		return obj.agonist.muscle_group

	def save_model(self, request, obj, form, change):
		if not obj.created_by_id:
			obj.created_by = request.user
		super().save_model(request, obj, form, change)
