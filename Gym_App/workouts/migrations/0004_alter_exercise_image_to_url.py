from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0003_rename_duration_minutes_to_seconds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='image',
            field=models.URLField(blank=True, null=True),
        ),
    ]
