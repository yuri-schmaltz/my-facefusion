import pytest
import sys
import os
from unittest.mock import patch

# Mock detect_app_context to always return 'cli' during tests
# We must patch where it is IMPORTED, not where it is defined, because state_manager 
# does "from facefusion.app_context import detect_app_context"
@pytest.fixture(autouse=True, scope="session")
def mock_app_context():
    # Patch in state_manager
    with patch('facefusion.state_manager.detect_app_context', return_value='cli'):
        # Also patch in app_context just in case specific module usage
        with patch('facefusion.app_context.detect_app_context', return_value='cli'):
            yield

# Ensure correct path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure correct path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
