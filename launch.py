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
import socket
from urllib.request import urlopen

# Also suppress some common Linux driver/browser noise
os.environ['CHROME_LOG_FILE'] = '/dev/null'

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8002
DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 5173

def get_env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        print(f"Warning: Invalid {name}='{value}', using default {default}.")
        return default

def is_port_available(host, port):
    if not host:
        host = DEFAULT_API_HOST
    family = socket.AF_INET6 if ':' in host else socket.AF_INET
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False

def find_free_port(host, preferred_port, max_tries=50):
    port = preferred_port
    for _ in range(max_tries):
        if is_port_available(host, port):
            return port
        port += 1
    # Fallback to ephemeral port
    family = socket.AF_INET6 if ':' in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]

def get_open_host(host):
    if host in ("0.0.0.0", "::", ""):
        return "127.0.0.1"
    return host

def wait_for_http(url, timeout=20, interval=0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2):
                return True
        except Exception:
            time.sleep(interval)
    return False

def configure_cuda_env():
    """Add all discovered nvidia and tensorrt library paths to LD_LIBRARY_PATH."""
    try:
        import site
        site_packages = site.getsitepackages()[0]
        
        paths_to_add = []
        
        # 1. Find all 'lib' directories under site-packages/nvidia
        nvidia_path = os.path.join(site_packages, 'nvidia')
        if os.path.isdir(nvidia_path):
            for root, dirs, files in os.walk(nvidia_path):
                if 'lib' in dirs:
                    paths_to_add.append(os.path.join(root, 'lib'))

        # 2. Find libraries under site-packages/tensorrt*
        # Newer pip packages (tensorrt-libs) put .so files in the package root
        for entry in os.listdir(site_packages):
            if entry.startswith('tensorrt'):
                package_path = os.path.join(site_packages, entry)
                if os.path.isdir(package_path):
                    # Add package root (where libnvinfer.so.10 often lives now)
                    paths_to_add.append(package_path)
                    
                    # Also look for 'lib' subdir recursively
                    for root, dirs, files in os.walk(package_path):
                        if 'lib' in dirs:
                            paths_to_add.append(os.path.join(root, 'lib'))
        
        if paths_to_add:
            current_ld = os.environ.get('LD_LIBRARY_PATH', '')
            # Unique sorted paths to prepend
            new_paths = os.pathsep.join(sorted(list(set(paths_to_add))))
            
            if current_ld:
                os.environ['LD_LIBRARY_PATH'] = new_paths + os.pathsep + current_ld
            else:
                os.environ['LD_LIBRARY_PATH'] = new_paths
                
            print(f"Configured CUDA/TensorRT environment with {len(set(paths_to_add))} library paths.")
            
    except Exception as e:
        print(f"Warning: Could not configure CUDA/TensorRT environment: {e}")

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

    # Handle arguments pass-through
    if len(sys.argv) > 1:
        # If user passed arguments (e.g. headless-run ...), pass them to facefusion.py
        # and do NOT start the web UI.
        print(f"Passing arguments to facefusion.py: {sys.argv[1:]}")
        try:
            cmd = [sys.executable, "facefusion.py"] + sys.argv[1:]
            # Use subprocess.run to wait for completion
            subprocess.run(cmd, check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            sys.exit(130)

    # Resolve ports (with fallback to free ports)
    api_host = os.environ.get("FACEFUSION_API_HOST", DEFAULT_API_HOST)
    ui_host = os.environ.get("FACEFUSION_UI_HOST", DEFAULT_UI_HOST)
    requested_api_port = get_env_int("FACEFUSION_API_PORT", DEFAULT_API_PORT)
    requested_ui_port = get_env_int("FACEFUSION_UI_PORT", DEFAULT_UI_PORT)
    api_port = find_free_port(api_host, requested_api_port)
    ui_port = find_free_port(ui_host, requested_ui_port)

    if api_port != requested_api_port:
        print(f"Warning: Port {requested_api_port} unavailable, using {api_port} for backend.")
    if ui_port != requested_ui_port:
        print(f"Warning: Port {requested_ui_port} unavailable, using {ui_port} for frontend.")
    
    # 1. Start Backend
    print(f"Launching Backend (host {api_host}, port {api_port})...")
    backend_env = os.environ.copy()
    backend_env["FACEFUSION_API_HOST"] = api_host
    backend_env["FACEFUSION_API_PORT"] = str(api_port)
    backend = create_popen_with_pgid([sys.executable, "facefusion.py", "run"], env=backend_env)

    # 2. Start Frontend  
    print(f"Launching Frontend (host {ui_host}, port {ui_port})...")
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

    api_open_host = get_open_host(api_host)
    ui_open_host = get_open_host(ui_host)
    frontend_env = os.environ.copy()
    frontend_env["VITE_BACKEND_ORIGIN"] = f"http://{api_open_host}:{api_port}"
    frontend = create_popen_with_pgid(
        [npm_cmd, "run", "dev", "--", "--host", ui_host, "--port", str(ui_port)],
        cwd=web_dir,
        env=frontend_env
    )

    # 3. Open Browser
    backend_health = f"http://{api_open_host}:{api_port}/health"
    if wait_for_http(backend_health, timeout=20):
        print(f"Backend healthy at {backend_health}")
    else:
        print(f"Warning: Backend not ready after timeout: {backend_health}")

    ui_url = f"http://{ui_open_host}:{ui_port}"
    if wait_for_http(ui_url, timeout=30):
        print(f"Frontend ready at {ui_url}")
    else:
        print(f"Warning: Frontend not ready after timeout: {ui_url}")

    print(f"Opening browser at {ui_url}")
    if sys.platform == 'linux':
        try:
            # Attempt to use specific browsers with noise suppression first
            # xdg-open often passes through, so we try to call it with redirected IO
            subprocess.Popen(['xdg-open', ui_url], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        except OSError:
            # Fallback if xdg-open missing
            webbrowser.open(ui_url)
    else:
        webbrowser.open(ui_url)

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
