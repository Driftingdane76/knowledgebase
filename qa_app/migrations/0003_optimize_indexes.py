from django.db import migrations, models


def convert_empty_dates_to_null(apps, schema_editor):
    """Convert empty string dates to NULL before switching to DateField."""
    KnowledgePage = apps.get_model('qa_app', 'KnowledgePage')
    KnowledgePage.objects.filter(date='').update(date=None)


class Migration(migrations.Migration):

    dependencies = [
        ('qa_app', '0002_seed_data'),
    ]

    operations = [
        # Step 1: Convert empty date strings to NULL
        migrations.RunPython(
            convert_empty_dates_to_null,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2: Change date from CharField to DateField
        migrations.AlterField(
            model_name='knowledgepage',
            name='date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),

        # Step 3: Add indexes to Category
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(db_index=True, default=None),
            preserve_default=False,
        ),

        # Step 4: Add indexes to KnowledgePage searchable fields
        migrations.AlterField(
            model_name='knowledgepage',
            name='username',
            field=models.CharField(db_index=True, default='anonymous', max_length=100),
        ),
        migrations.AlterField(
            model_name='knowledgepage',
            name='created_at',
            field=models.DateTimeField(db_index=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='knowledgepage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),

        # Step 5: Add composite indexes for common query patterns
        migrations.AddIndex(
            model_name='knowledgepage',
            index=models.Index(fields=['category', '-date'], name='idx_page_cat_date'),
        ),
        migrations.AddIndex(
            model_name='knowledgepage',
            index=models.Index(fields=['category', 'username'], name='idx_page_cat_user'),
        ),
    ]
