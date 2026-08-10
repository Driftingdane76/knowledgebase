import os
import sys
import django

# Setup Django test environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from test_htmls.dynamic_mock_generator import generate_dynamic_html_snippet
from qa_app.models import Tag
from qa_app.utils import extract_tags

def load_tags_from_file(filepath="tags.txt"):
    """
    Parses a text file with terms/phrases (one per line).
    Strips whitespace and returns a list of non-empty unique terms.
    """
    if not os.path.exists(filepath):
        return []
    tags = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith('#') and cleaned not in tags:
                tags.append(cleaned)
    return tags

def test_tags_loading():
    print("--- 1. Testing tags.txt Loading ---")
    tags = load_tags_from_file("tags.txt")
    print(f"Loaded {len(tags)} tags from tags.txt: {tags}")
    assert len(tags) > 0, "Failed: No tags loaded from tags.txt!"
    assert "Fejl:" in tags or "Fejl" in tags, "Failed: 'Fejl' term missing!"
    print("✓ tags.txt loading passed.")
    return tags

def test_dynamic_snippet_tag_distribution(tags):
    print("\n--- 2. Testing Dynamic HTML Tag Injection ---")
    # Generate 8 layout snippets passing custom tags
    found_tags = set()
    for i in range(8):
        html = generate_dynamic_html_snippet(index=i, custom_tags=tags)
        for tag in tags:
            if tag in html:
                found_tags.add(tag)
    
    print(f"Tags found in generated HTML layouts: {found_tags}")
    assert len(found_tags) > 0, "Failed: custom_tags were not injected into generated HTML!"
    print("✓ Dynamic HTML Tag injection test passed.")

def test_tag_extraction_with_db(tags):
    print("\n--- 3. Testing Tag DB Creation & extract_tags Integration ---")
    # Ensure Tag models exist for these terms
    for tag_name in tags:
        # Strip trailing punctuation like ':' for clean tag matching if desired
        clean_name = tag_name.rstrip(':')
        Tag.objects.get_or_create(name=clean_name)
    
    sample_text = "Dette er et skærmbillede. Advarsel: Kunden har ingen inboforsikring og systemet gav Fejl."
    matched_tags = extract_tags(sample_text)
    matched_names = [t.name for t in matched_tags]
    print(f"Sample text: '{sample_text}'")
    print(f"Extracted tags: {matched_names}")
    
    assert "Advarsel" in matched_names or "Fejl" in matched_names or "Kunden har ingen inboforsikring" in matched_names, "Failed: Tags not matched!"
    print("✓ Tag extraction integration test passed.")

if __name__ == '__main__':
    print("=" * 60)
    print("RUNNING TDD VERIFICATION: tags.txt Mockup Extension")
    print("=" * 60)
    try:
        loaded_tags = test_tags_loading()
        test_dynamic_snippet_tag_distribution(loaded_tags)
        test_tag_extraction_with_db(loaded_tags)
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    except TypeError as te:
        print(f"\n[EXPECTED TDD INITIAL FAILURE]: {te}")
        print("This proves that `generate_dynamic_html_snippet` currently does not accept `custom_tags`.")
        sys.exit(1)
    except AssertionError as ae:
        print(f"\n[TDD FAILURE]: {ae}")
        sys.exit(1)
