
import os
import sys

# Simulate launch.py environment setup
def configure_env():
    import site
    site_packages = site.getsitepackages()[0]
    paths_to_add = []
    
    # Simulate the logic we added to launch.py
    nvidia_path = os.path.join(site_packages, 'nvidia')
    if os.path.isdir(nvidia_path):
        for root, dirs, files in os.walk(nvidia_path):
            if 'lib' in dirs:
                paths_to_add.append(os.path.join(root, 'lib'))

    for entry in os.listdir(site_packages):
        if entry.startswith('tensorrt'):
            package_path = os.path.join(site_packages, entry)
            if os.path.isdir(package_path):
                paths_to_add.append(package_path)
                for root, dirs, files in os.walk(package_path):
                    if 'lib' in dirs:
                        paths_to_add.append(os.path.join(root, 'lib'))
    
    if paths_to_add:
        current_ld = os.environ.get('LD_LIBRARY_PATH', '')
        new_paths = os.pathsep.join(sorted(list(set(paths_to_add))))
        os.environ['LD_LIBRARY_PATH'] = new_paths + os.pathsep + current_ld
        print(f"Added {len(set(paths_to_add))} paths to LD_LIBRARY_PATH")

configure_env()

# Now try importing
try:
    import onnxruntime
    print("Available Providers:", onnxruntime.get_available_providers())
    
    if 'TensorrtExecutionProvider' in onnxruntime.get_available_providers():
        print("SUCCESS: TensorRT is available!")
    else:
        print("FAILURE: TensorRT provider not found.")
except Exception as e:
    print(f"Error importing onnxruntime: {e}")
