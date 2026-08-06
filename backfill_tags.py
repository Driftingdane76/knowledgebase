"""
Standalone Django script to backfill tags for all KnowledgePage instances.
This script retroactively applies the tag extraction logic to existing database records.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from qa_app.utils import backfill_all_tags

def run():
    print("Starting retroactive tag extraction...")
    updated, total = backfill_all_tags()
    print(f"Finished! Successfully tagged {updated} out of {total} pages.")

if __name__ == '__main__':
    run()
