from django.db import models
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io
import sys

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text="Si es nulo, es una categoría global.")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Exercise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=150)
    # upload_to define la subcarpeta dentro del directorio MEDIA_ROOT
    image = models.ImageField(upload_to='exercise_images/', blank=True, null=True)
    tracks_weight = models.BooleanField(default=True, help_text="¿Este ejercicio requiere registrar peso levantado?")
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # 1. Ejecutar compresión solo si hay una imagen y si el archivo no ha sido guardado previamente en esta instancia
        if self.image and not self.image._committed:
            # 2. Abrir la imagen subida con la librería Pillow
            img = Image.open(self.image)
            
            # 3. Convertir a RGB si es necesario (previene errores al comprimir PNGs con transparencia a formato JPEG)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 4. Redimensionar utilizando thumbnail para no distorsionar la imagen. 
            # El límite será 200x200px, respetando la proporción original.
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # 5. Guardar la imagen procesada temporalmente en la memoria RAM (BytesIO)
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85) # Quality 85 ofrece un balance óptimo peso/calidad
            output.seek(0)
            
            # 6. Reemplazar el archivo original del modelo con el nuevo archivo comprimido en memoria
            self.image = InMemoryUploadedFile(
                output, 
                'ImageField', 
                f"{self.image.name.split('.')[0]}.jpg", 
                'image/jpeg', 
                sys.getsizeof(output), 
                None
            )
            
        # 7. Ejecutar el método save() original de la clase padre para persistir en SQLite
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Routine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class RoutineItem(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='items')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    recommended_sets = models.PositiveIntegerField(default=3)
    recommended_reps = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0, help_text="Orden de ejecución en la rutina")

    class Meta:
        ordering = ['order']

class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

class CardioLog(models.Model):
    PHASE_CHOICES = [
        ('WARMUP', 'Calentamiento'),
        ('COOLDOWN', 'Cardio Final'),
    ]
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='cardio_logs')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES)
    duration_minutes = models.PositiveIntegerField(help_text="Tiempo en minutos")
    distance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Distancia en km o millas")
    elevation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Inclinación/Altura")
    steps = models.PositiveIntegerField(null=True, blank=True, help_text="Escalones/Pasos")

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