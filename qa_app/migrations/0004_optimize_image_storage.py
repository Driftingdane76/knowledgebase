from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qa_app', '0003_optimize_indexes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pageimage',
            name='data_url',
        ),
        migrations.AddField(
            model_name='pageimage',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='page_images/'),
        ),
    ]
