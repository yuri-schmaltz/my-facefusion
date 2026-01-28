import os
import sys
import site
import onnxruntime as ort

try:
    print(f"ort version: {ort.__version__}")
    print(f"initial providers: {ort.get_available_providers()}")
    
    # Try to force CUDA initialization
    session = ort.InferenceSession(None, providers=['CUDAExecutionProvider'])
except Exception as e:
    print(f"\nCaught exception during CUDA initialization:")
    print(e)

# Manually check for specific libs if exception was vague
import ctypes
for lib in ['libnccl.so.2', 'libcusparse.so.12', 'libcublas.so.12', 'libcudnn.so.9']:
    try:
        ctypes.CDLL(lib)
        print(f"OK: {lib} found in system path")
    except Exception:
        print(f"FAIL: {lib} NOT found in system path")
