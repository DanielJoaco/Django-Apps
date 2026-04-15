from django.conf import settings
from django.db import models


class MovementPattern(models.Model):
    """Division muscular: Empuje, Halar, Piernas, etc."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MuscleGroup(models.Model):
    """Grupo muscular dentro de una division: Pecho, Espalda, Hombros, etc."""

    pattern = models.ForeignKey(
        MovementPattern,
        on_delete=models.CASCADE,
        related_name="muscle_groups",
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["pattern", "name"],
                name="unique_muscle_group_per_pattern",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.pattern.name})"


class Agonist(models.Model):
    """Musculo agonista principal: Biceps, Triceps, Deltoides, etc."""

    muscle_group = models.ForeignKey(
        MuscleGroup,
        on_delete=models.CASCADE,
        related_name="agonists",
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["muscle_group", "name"],
                name="unique_agonist_per_group",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.muscle_group.name})"


class Exercise(models.Model):
    EXERCISE_TYPE_STRENGTH = "STRENGTH"
    EXERCISE_TYPE_CARDIO = "CARDIO"
    EXERCISE_TYPE_FULL_BODY = "FULL_BODY"
    EXERCISE_TYPE_CHOICES = [
        (EXERCISE_TYPE_STRENGTH, "Fuerza"),
        (EXERCISE_TYPE_CARDIO, "Cardiovascular"),
        (EXERCISE_TYPE_FULL_BODY, "Cuerpo Completo"),
    ]

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    agonist = models.ForeignKey(
        Agonist,
        on_delete=models.PROTECT,
        related_name="exercises",
    )
    image = models.ImageField(upload_to="exercise_images/%Y/%m/", blank=True, null=True)
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        default=EXERCISE_TYPE_STRENGTH,
    )
    tracks_weight = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wiki_exercises_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if self.exercise_type == self.EXERCISE_TYPE_CARDIO:
            self.tracks_weight = False
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name