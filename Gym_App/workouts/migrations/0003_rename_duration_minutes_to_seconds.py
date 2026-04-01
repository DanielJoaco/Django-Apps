from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0002_remove_exerciselog_exercise_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cardioentry',
            old_name='duration_minutes',
            new_name='duration_seconds',
        ),
        migrations.RenameField(
            model_name='fullbodyentry',
            old_name='duration_minutes',
            new_name='duration_seconds',
        ),
    ]
