import os
import sys
import site

# Simulate launch.py configuration
site_packages = site.getsitepackages()[0]
libs = ['nvidia/cudnn/lib', 'nvidia/cublas/lib']
paths_to_add = []
for lib in libs:
    lib_path = os.path.join(site_packages, lib)
    if os.path.isdir(lib_path):
        paths_to_add.append(lib_path)

if paths_to_add:
    current_ld = os.environ.get('LD_LIBRARY_PATH', '')
    new_ld = ':'.join(paths_to_add)
    if current_ld:
        new_ld += ':' + current_ld
    os.environ['LD_LIBRARY_PATH'] = new_ld
    print(f"Configured library paths: {':'.join(paths_to_add)}")

import onnxruntime as ort
print(f"ONNX Runtime version: {ort.__version__}")
print(f"Available providers: {ort.get_available_providers()}")
if 'CUDAExecutionProvider' in ort.get_available_providers():
    print("CUDA is available!")
else:
    print("CUDA is NOT available.")
