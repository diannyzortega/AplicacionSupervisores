from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('comercial', '0007_remove_categoria_mes_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='categoria',
            name='obj_profundidad',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='seguimientodiario',
            name='prof_lleva',
            field=models.FloatField(default=0.0),
        ),
    ]
