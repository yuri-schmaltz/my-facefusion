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
    
    npm_cmd = shutil.which('npm')
    if not npm_cmd:
        print("Error: npm not found. Please install Node.js.")
        terminate_process_tree(backend, "backend")
        sys.exit(1)

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

