from django.test import SimpleTestCase
import sys
import os

# Ensure the root directory is in sys.path to import seed_from_mock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from seed_from_mock import get_random_danish_qa
except ImportError:
    get_random_danish_qa = None

class DataSeederTests(SimpleTestCase):
    
    def test_get_random_danish_qa(self):
        """Test that get_random_danish_qa returns valid non-empty strings"""
        if get_random_danish_qa is None:
            self.skipTest("seed_from_mock could not be imported")
            
        title, question, answer = get_random_danish_qa()
        
        # Check that they are strings and not empty
        self.assertIsInstance(title, str)
        self.assertIsInstance(question, str)
        self.assertIsInstance(answer, str)
        
        self.assertGreater(len(title), 5)
        self.assertGreater(len(question), 10)
        self.assertGreater(len(answer), 10)
        
        # We know questions often have "nummerplade" or "skade", check for randomness indirectly
        # by generating a few and making sure they aren't all exactly the same
        results = set()
        for _ in range(10):
            t, q, a = get_random_danish_qa()
            results.add(t)
        
        # There should be at least a few unique titles if it's truly random
        self.assertGreater(len(results), 1)
