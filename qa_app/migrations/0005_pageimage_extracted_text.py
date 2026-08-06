from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qa_app', '0004_optimize_image_storage'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageimage',
            name='extracted_text',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='pageimage',
            name='ocr_data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
