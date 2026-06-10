import sys
import os

# Add the workspace root to sys.path to allow imports from facefusion package
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from facefusion.app_context import set_app_context
set_app_context('cli')

import uvicorn
from facefusion.api.main import app, find_free_port, write_frontend_config

if __name__ == '__main__':
    host = "127.0.0.1"
    try:
        port = find_free_port(8000)
    except Exception:
        port = 8000
        
    write_frontend_config(port)
    print(f"[API] starting uvicorn on {host}:{port}", flush=True)
    # Use app object directly instead of string import to avoid reload/import issues in PyInstaller
    uvicorn.run(app, host=host, port=port)
