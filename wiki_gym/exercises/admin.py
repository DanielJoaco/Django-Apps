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
	list_select_related = ("pattern", "muscle_group", "agonist")
	list_display = (
		"name",
		"exercise_type",
		"pattern",
		"muscle_group",
		"agonist",
		"tracks_weight",
		"is_active",
	)
	list_filter = ("exercise_type", "pattern", "muscle_group", "is_active")
	search_fields = ("name", "description", "pattern__name", "muscle_group__name", "agonist__name")
	autocomplete_fields = ("agonist",)

	def save_model(self, request, obj, form, change):
		if obj.agonist_id:
			obj.muscle_group = obj.agonist.muscle_group
			obj.pattern = obj.agonist.muscle_group.pattern
		if not obj.created_by_id:
			obj.created_by = request.user
		super().save_model(request, obj, form, change)
