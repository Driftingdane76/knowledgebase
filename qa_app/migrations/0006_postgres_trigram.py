from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension
from django.contrib.postgres.indexes import GinIndex


class Migration(migrations.Migration):

    dependencies = [
        ('qa_app', '0005_pageimage_extracted_text'),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name='knowledgepage',
            index=GinIndex(fields=['title'], name='page_title_trigm_gin', opclasses=['gin_trgm_ops']),
        ),
        migrations.AddIndex(
            model_name='knowledgepage',
            index=GinIndex(fields=['question_text'], name='page_quest_trigm_gin', opclasses=['gin_trgm_ops']),
        ),
        migrations.AddIndex(
            model_name='knowledgepage',
            index=GinIndex(fields=['resolution_text'], name='page_resol_trigm_gin', opclasses=['gin_trgm_ops']),
        ),
        migrations.AddIndex(
            model_name='pageimage',
            index=GinIndex(fields=['extracted_text'], name='img_ocr_trigm_gin', opclasses=['gin_trgm_ops']),
        ),
    ]
