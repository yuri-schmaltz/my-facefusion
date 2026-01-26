#!/usr/bin/env python3

import uvicorn
import os
import sys

# Ensure the current directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting FaceFusion API Server on port 8002...")
    uvicorn.run("facefusion.api_server:app", host="0.0.0.0", port=8002, reload=True)
