# Generated by Django 3.2 on 2021-05-07 10:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_student_unique_code'),
    ]

    operations = [

        migrations.AlterField(
            model_name='lessonurl',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.student'),
        ),
        migrations.AddField(
            model_name='lessonurl',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='lessonurl',
            unique_together={('student', 'lesson')},
        ),
    ]
