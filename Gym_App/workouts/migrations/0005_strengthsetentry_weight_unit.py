from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0004_alter_exercise_image_to_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='strengthsetentry',
            name='weight_unit',
            field=models.CharField(
                choices=[('kg', 'Kilogramos'), ('lbs', 'Libras')],
                default='kg',
                max_length=5,
            ),
        ),
    ]
