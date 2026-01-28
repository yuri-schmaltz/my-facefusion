#!/usr/bin/env python3
"""
FaceFusion Orchestrator (launch.py)
-----------------------------------
Main entrypoint for end-users. Handles:
1. Starting the core backend (facefusion.py)
2. Starting the web frontend
3. Managing process lifecycle and clean cleanup.
"""
import subprocess
import time
import webbrowser
import os
import signal
import sys
import shutil
import platform

# Suppress Google API/GCM registration errors in Chromium-based browsers
# This fixes the DEPRECATED_ENDPOINT warnings in terminal
os.environ['GOOGLE_API_KEY'] = 'no'
os.environ['GOOGLE_DEFAULT_CLIENT_ID'] = 'no'
os.environ['GOOGLE_DEFAULT_CLIENT_SECRET'] = 'no'
# Also suppress some common Linux driver/browser noise
os.environ['CHROME_LOG_FILE'] = '/dev/null'

def configure_cuda_env():
    """Add all discovered nvidia library paths to LD_LIBRARY_PATH."""
    try:
        import site
        site_packages = site.getsitepackages()[0]
        nvidia_path = os.path.join(site_packages, 'nvidia')
        
        if not os.path.isdir(nvidia_path):
            return

        paths_to_add = []
        # Find all 'lib' directories under site-packages/nvidia
        for root, dirs, files in os.walk(nvidia_path):
            if 'lib' in dirs:
                lib_path = os.path.join(root, 'lib')
                if os.path.isdir(lib_path):
                    paths_to_add.append(lib_path)
        
        if paths_to_add:
            current_ld = os.environ.get('LD_LIBRARY_PATH', '')
            # Unique sorted paths to prepend
            new_paths = os.pathsep.join(sorted(list(set(paths_to_add))))
            
            if current_ld:
                os.environ['LD_LIBRARY_PATH'] = new_paths + os.pathsep + current_ld
            else:
                os.environ['LD_LIBRARY_PATH'] = new_paths
                
            print(f"Configured CUDA environment with {len(paths_to_add)} library paths.")
            
    except Exception as e:
        print(f"Warning: Could not configure CUDA environment: {e}")

# Global references for cleanup
backend = None
frontend = None

def create_popen_with_pgid(cmd, **kwargs):
    """Create Popen with new process group for clean termination on Linux."""
    if sys.platform != 'win32':
        kwargs['start_new_session'] = True
    return subprocess.Popen(cmd, **kwargs)

def terminate_process_tree(proc, name="process"):
    """Terminate process and all children reliably."""
    if proc is None or proc.poll() is not None:
        return
    
    print(f"Terminating {name}...")
    if sys.platform == 'win32':
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass  # Already terminated

def cleanup():
    """Clean up all child processes."""
    global backend, frontend
    terminate_process_tree(frontend, "frontend")
    terminate_process_tree(backend, "backend")

def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT gracefully."""
    print(f"\nReceived signal {signum}, shutting down...")
    cleanup()
    sys.exit(0)

def main():
    global backend, frontend
    
    print("Starting FaceFusion Full Stack...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure CUDA environment variables
    configure_cuda_env()

    # Pre-flight check: Kill anything on our ports to prevent conflicts
    print("Checking ports...")
    try:
        # Kill anything on 8002 (Backend) and 5173 (Frontend)
        subprocess.run("lsof -t -i:8002 -i:5173 | xargs -r kill -9", shell=True, stderr=subprocess.DEVNULL)
        time.sleep(1) # Wait for release
    except Exception as e:
        print(f"Warning during port cleanup: {e}")
    
    # 1. Start Backend
    print("Launching Backend (port 8002)...")
    backend = create_popen_with_pgid([sys.executable, "facefusion.py", "run"])

    # 2. Start Frontend  
    print("Launching Frontend (port 5173)...")
    web_dir = os.path.join(os.getcwd(), "web")
    
    frontend = None # Initialize to avoid UnboundLocalError if we exit early
    
    npm_cmd = shutil.which('npm')
    if not npm_cmd:
        print("Error: npm not found. Please install Node.js.")
        terminate_process_tree(backend, "backend")
        sys.exit(1)

    # Check Node.js version
    try:
        # Get node executable (shutil.which('node'))
        node_exec = shutil.which('node') or 'node'
        node_output = subprocess.check_output([node_exec, "-v"], text=True).strip()
        # Parse v18.19.1 -> 18
        major_ver = int(node_output.lstrip('v').split('.')[0])
        if major_ver < 20:
             print(f"\n[ERROR] Incompatible Node.js version detected: {node_output}")
             print("FaceFusion requires Node.js v20.0.0 or higher.")
             print("Please upgrade your Node.js installation.")
             terminate_process_tree(backend, "backend")
             sys.exit(1)
    except Exception as e:
        print(f"Warning: Could not check Node.js version: {e}")

    frontend = create_popen_with_pgid([npm_cmd, "run", "dev"], cwd=web_dir)

    # 3. Open Browser
    time.sleep(3) 
    print("Opening browser at http://localhost:5173")
    webbrowser.open("http://localhost:5173")

    try:
        # Keep alive and monitor
        while True:
            time.sleep(1)
            if backend.poll() is not None:
                print("Backend exited unexpectedly.")
                break
            if frontend.poll() is not None:
                print("Frontend exited unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        cleanup()
        
    print("FaceFusion stopped.")

if __name__ == "__main__":
    main()

