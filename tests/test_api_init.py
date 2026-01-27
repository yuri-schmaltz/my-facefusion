from fastapi.testclient import TestClient
from facefusion.api_server import app, lifespan
from facefusion import state_manager
import pytest
import tempfile

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_lifespan_initialization():
    """
    Verifies that the lifespan context manager correctly initializes
    all critical state items needed for the application to run.
    This specifically targets the regression where temp_path was None.
    """
    # Create a mock lifespan context
    # Note: We can't easily mock the entire lifespan async context without
    # running the full app, so we'll check the side effects directly
    # after manually invoking the init logic or mimicking it if possible.
    
    # However, since lifespan runs on startup, using TestClient normally triggers it.
    # Let's inspect the state_manager directly.
    
    with TestClient(app) as client:
        # Trigger startup
        client.get("/health")
        
        # Check critical keys
        assert state_manager.get_item('temp_path') is not None
        assert state_manager.get_item('execution_thread_count') is not None
        assert state_manager.get_item('execution_queue_count') is not None
        assert state_manager.get_item('face_mask_types') is not None
        
        # Verify specific defaults
        assert state_manager.get_item('execution_thread_count') == 4
        assert state_manager.get_item('execution_queue_count') == 1
        
        # Verify temp_path valid
        temp_path = state_manager.get_item('temp_path')
        assert isinstance(temp_path, str)
        assert len(temp_path) > 0
