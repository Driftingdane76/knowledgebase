import os

files_to_remove = [
    'test_vision_api.py',
    'test_comprehensive_vision.py',
    'seed_from_mock_backup.py',
    os.path.join('test_htmls', 'vision_target_comprehensive_test_redacted.png'),
    os.path.join('test_htmls', 'vision_target_comprehensive.html'),
    os.path.join('test_htmls', 'vision_target_comprehensive.png'),
]

base_dir = os.path.dirname(os.path.abspath(__file__))

for rel_path in files_to_remove:
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
            print(f"Removed: {rel_path}")
        except Exception as e:
            print(f"Failed to remove {rel_path}: {e}")
    else:
        print(f"Already absent: {rel_path}")

print("Cleanup complete.")
