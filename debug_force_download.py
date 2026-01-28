import sys
import os
import traceback

# Add current directory to path
sys.path.append(os.getcwd())

from facefusion import state_manager, logger
from facefusion.core import force_download

try:
    state_manager.init_item('download_scope', 'lite')
    state_manager.init_item('log_level', 'info')
    # Default execution providers
    state_manager.init_item('execution_providers', ['cpu'])
    # Default download providers
    state_manager.init_item('download_providers', ['huggingface'])
    
    print("Running force_download()...")
    result = force_download()
    print(f"Result: {result}")
except Exception:
    traceback.print_exc()
