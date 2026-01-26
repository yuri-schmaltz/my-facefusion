import subprocess
import time
import webbrowser
import os
import signal
import sys
import shutil

def main():
    print("Starting FaceFusion Full Stack...")
    
    # 1. Start Backend
    print("Launching Backend (port 8002)...")
    backend = subprocess.Popen([sys.executable, "facefusion.py", "run"])

    # 2. Start Frontend
    print("Launching Frontend (port 5173)...")
    web_dir = os.path.join(os.getcwd(), "web")
    
    # Check for npm
    npm_cmd = shutil.which('npm')
    if not npm_cmd:
        print("Error: npm not found. Please install Node.js.")
        backend.terminate()
        sys.exit(1)

    # Allow custom port for frontend if needed (env var) but default to dev script
    frontend = subprocess.Popen([npm_cmd, "run", "dev"], cwd=web_dir)

    # 3. Open Browser
    # Give it a moment to spin up
    time.sleep(3) 
    print("Opening browser at http://localhost:5173")
    webbrowser.open("http://localhost:5173")

    try:
        # Keep alive
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if backend.poll() is not None:
                print("Backend exited unexpectedly.")
                break
            if frontend.poll() is not None:
                print("Frontend exited unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        # Cleanup
        if backend.poll() is None:
            backend.terminate()
        if frontend.poll() is None:
            frontend.terminate() # npm run dev spawns children, this might not kill vite server fully on windows without shell=True or taskkill, but basic termination
            
            # Additional cleanup for deep process trees if needed
            if sys.platform == 'win32':
                 subprocess.call(['taskkill', '/F', '/T', '/PID', str(frontend.pid)])
            
    print("FaceFusion stopped.")

if __name__ == "__main__":
    main()
