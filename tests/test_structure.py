"""Simple structure test without external dependencies."""

import unittest
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Test that we can import the main modules
class TestStructure(unittest.TestCase):
    """Test that the basic project structure is correct."""
    
    def test_config_import(self):
        """Test that config module can be imported."""
        try:
            from src.config import Config
            config = Config()
            self.assertIsNotNone(config)
        except ImportError as e:
            self.fail(f"Could not import Config: {e}")
    
    def test_src_init(self):
        """Test that src package can be imported."""
        try:
            import src
            self.assertIsNotNone(src)
        except ImportError as e:
            self.fail(f"Could not import src package: {e}")
    
    def test_main_module_exists(self):
        """Test that main.py exists and has the main class."""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        self.assertTrue(os.path.exists(main_path), "main.py should exist")
        
        # Read the file and check for AnchorInsightAI class
        with open(main_path, 'r') as f:
            content = f.read()
            self.assertIn('class AnchorInsightAI', content)
    
    def test_api_module_exists(self):
        """Test that api.py exists."""
        api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
        self.assertTrue(os.path.exists(api_path), "api.py should exist")
    
    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        self.assertTrue(os.path.exists(req_path), "requirements.txt should exist")


if __name__ == '__main__':
    unittest.main()