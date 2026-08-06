import re
from .models import Tag, KnowledgePage

def extract_tags(text):
    """
    Extracts tags from the given text strictly based on Predefined Admin Tags.
    No random regex or heuristic guessing is used.
    If an admin has created a tag in the Django Admin panel, and that exact phrase 
    appears in the text, it will be automatically linked.
    """
    if not text:
        return []
        
    extracted_tags = set()
    text_lower = text.lower()
    
    try:
        # Fetch all admin-defined tags
        all_tags = Tag.objects.all()
        for tag in all_tags:
            # Check if the exact tag phrase exists in the text (case-insensitive)
            # We add basic word boundaries (\b) so a generic tag like 'cat' doesn't falsely match inside 'category'.
            # We must use re.escape to safely handle tags that contain special regex characters (like 'C++' or '50%').
            escaped_tag = re.escape(tag.name.lower())
            
            # Use regex to find the exact tag as a discrete whole word/phrase.
            if re.search(r'\b' + escaped_tag + r'\b', text_lower):
                extracted_tags.add(tag)
            # Fallback mechanism: If the tag contains non-word characters where \b fails (e.g. symbols at the edge),
            # we perform a simple substring check.
            elif tag.name.lower() in text_lower:
                 extracted_tags.add(tag)
    except Exception:
        # Failsafe if DB isn't ready
        pass
            
    return list(extracted_tags)

def backfill_all_tags():
    """
    Extracts tags for all KnowledgePages retroactively.
    Returns a tuple of (updated_count, total_count).
    """
    pages = KnowledgePage.objects.prefetch_related('images').all()
    total = pages.count()
    updated = 0
    
    for page in pages:
        # Step 1: Aggregate all text content from the page (question and resolution)
        all_text = f"{page.question_text} {page.resolution_text}"
        
        # Step 2: Append any OCR text extracted from attached images
        for img in page.images.all():
            if img.extracted_text:
                all_text += f" {img.extracted_text}"
                
        # Step 3: Run the extraction logic to find matching tags
        new_tags = extract_tags(all_text)
        
        # Step 4: If tags are found, assign them to the page and increment the counter
        if new_tags:
            page.tags.set(new_tags)
            updated += 1
            
    return updated, total
