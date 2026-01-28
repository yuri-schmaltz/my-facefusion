import os
import sys
import site
import subprocess

def configure_cuda_env():
    """Add all discovered nvidia library paths to LD_LIBRARY_PATH."""
    try:
        import site
        site_packages = site.getsitepackages()[0]
        nvidia_path = os.path.join(site_packages, 'nvidia')
        
        if not os.path.isdir(nvidia_path):
            print("NVIDIA path not found!")
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

configure_cuda_env()

import onnxruntime as ort
print(f"Version: {ort.__version__}")
print(f"Providers: {ort.get_available_providers()}")
if 'CUDAExecutionProvider' in ort.get_available_providers():
    print("CUDA SUCCESS")
else:
    print("CUDA FAIL")
