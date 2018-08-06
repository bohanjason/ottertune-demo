
from django.core.management import call_command
from django.db import migrations


def load_initial_data(apps, schema_editor):
    initial_data_fixtures = [
        "demo/demo/fixture/knobs.json"
    ]
    for fixture in initial_data_fixtures:
        call_command("loaddata", fixture, app_label="demo")


def unload_initial_data(apps, schema_editor):
    model_names = [
        "KnobCatalog"
    ]
    for model_name in model_names:
        model = apps.get_model("demo", model_name)
        model.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, unload_initial_data)
    ]