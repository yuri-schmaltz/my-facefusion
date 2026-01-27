import subprocess
import shutil
import platform
import sys
from typing import Literal

HardwareProvider = Literal['cuda', 'rocm', 'directml', 'openvino', 'coreml', 'cpu']

def detect_hardware() -> HardwareProvider:
    if sys.platform == 'darwin':
        # Apple Silicon check
        if platform.machine() == 'arm64':
            return 'coreml'
        return 'cpu'

    if shutil.which('nvidia-smi'):
        try:
            subprocess.check_output(['nvidia-smi'], stderr=subprocess.DEVNULL)
            return 'cuda'
        except:
            pass

    if sys.platform == 'win32':
        # DirectML is usually a safe bet for modern Windows GPUs if not CUDA
        return 'directml'

    # Check for ROCm (Linux)
    if shutil.which('rocminfo') or shutil.which('clinfo'):
        return 'rocm'

    return 'cpu'

def get_onnx_package(provider: HardwareProvider) -> str:
    packages = {
        'cuda': 'onnxruntime-gpu==1.23.2',
        'rocm': 'onnxruntime-rocm==1.22.1', # Note: uses specialized wheels in installer.py
        'directml': 'onnxruntime-directml==1.23.0',
        'openvino': 'onnxruntime-openvino==1.23.0',
        'coreml': 'onnxruntime==1.23.2', # CoreML provider is often built-in to standard onnxruntime on macOS
        'cpu': 'onnxruntime==1.23.2'
    }
    return packages.get(provider, 'onnxruntime==1.23.2')
