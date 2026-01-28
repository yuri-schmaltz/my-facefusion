import os
import sys
import site
import subprocess

# Simulate launch.py configuration
site_packages = site.getsitepackages()[0]
libs = ['nvidia/cudnn/lib', 'nvidia/cublas/lib']
paths_to_add = []
for lib in libs:
    lib_path = os.path.join(site_packages, lib)
    if os.path.isdir(lib_path):
        paths_to_add.append(lib_path)

env = os.environ.copy()
if paths_to_add:
    current_ld = env.get('LD_LIBRARY_PATH', '')
    new_ld = ':'.join(paths_to_add)
    if current_ld:
        new_ld += ':' + current_ld
    env['LD_LIBRARY_PATH'] = new_ld

env['LD_DEBUG'] = 'libs'
cmd = [sys.executable, "-c", "import onnxruntime as ort; print(ort.get_available_providers())"]
result = subprocess.run(cmd, env=env, stderr=subprocess.PIPE, text=True)
print(result.stderr)
