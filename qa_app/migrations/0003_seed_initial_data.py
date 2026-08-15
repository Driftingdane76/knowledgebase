from django.db import migrations

def seed_data(apps, schema_editor):
    Category = apps.get_model('qa_app', 'Category')
    KnowledgePage = apps.get_model('qa_app', 'KnowledgePage')

    # 1. Create categories without hardcoded IDs
    cat_db, _ = Category.objects.get_or_create(name='Database')
    cat_fe, _ = Category.objects.get_or_create(name='Frontend')

    # 2. Create default pages
    KnowledgePage.objects.get_or_create(
        id='page-1',
        defaults={
            'category': cat_db,
            'title': 'How to query?',
            'date': '2026-06-12',
            'username': 'user1',
            'question_text': 'Query question',
            'resolution_text': 'Query resolution',
        }
    )
    KnowledgePage.objects.get_or_create(
        id='page-2',
        defaults={
            'category': cat_fe,
            'title': 'React rendering slow',
            'date': '2026-06-02',
            'username': 'bob',
            'question_text': 'Too many updates',
            'resolution_text': 'Use memoization',
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('qa_app', '0002_alter_knowledgepage_id_alter_pageimage_id'),  # or whatever your latest migration number is
    ]

    operations = [
        migrations.RunPython(seed_data),
    ]