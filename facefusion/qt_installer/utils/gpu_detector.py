"""
FaceFusion Qt6 Installer - GPU Detection
=========================================
Enhanced GPU detection for NVIDIA, AMD, Intel, and Apple Silicon.
"""

import subprocess
import sys
import os
import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class GPUVendor(Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


class ExecutionProvider(Enum):
    CUDA = "cuda"
    TENSORRT = "tensorrt"
    ROCM = "rocm"
    DIRECTML = "directml"
    COREML = "coreml"
    OPENVINO = "openvino"
    CPU = "cpu"


@dataclass
class GPUInfo:
    vendor: GPUVendor
    name: str
    memory_mb: Optional[int] = None
    cuda_version: Optional[str] = None
    driver_version: Optional[str] = None


def detect_gpus() -> List[GPUInfo]:
    """Detect all available GPUs in the system."""
    gpus = []
    
    # Try NVIDIA detection
    nvidia_gpus = _detect_nvidia_gpus()
    gpus.extend(nvidia_gpus)
    
    # Try AMD detection (Linux)
    if sys.platform.startswith('linux'):
        amd_gpus = _detect_amd_gpus_linux()
        gpus.extend(amd_gpus)
    
    # Try Intel detection
    intel_gpus = _detect_intel_gpus()
    gpus.extend(intel_gpus)
    
    # Apple Silicon detection
    if sys.platform == 'darwin':
        apple_gpus = _detect_apple_silicon()
        gpus.extend(apple_gpus)
    
    return gpus


def _detect_nvidia_gpus() -> List[GPUInfo]:
    """Detect NVIDIA GPUs using nvidia-smi."""
    gpus = []
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 3:
                        name, memory, driver = parts[0], parts[1], parts[2]
                        gpus.append(GPUInfo(
                            vendor=GPUVendor.NVIDIA,
                            name=name,
                            memory_mb=int(float(memory)) if memory else None,
                            driver_version=driver
                        ))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try to get CUDA version
    if gpus:
        cuda_version = _get_cuda_version()
        for gpu in gpus:
            gpu.cuda_version = cuda_version
    
    return gpus


def _get_cuda_version() -> Optional[str]:
    """Get CUDA version from nvcc or nvidia-smi."""
    # Try nvcc first
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            match = re.search(r'release (\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try nvidia-smi
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            match = re.search(r'CUDA Version: (\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def _detect_amd_gpus_linux() -> List[GPUInfo]:
    """Detect AMD GPUs on Linux using rocm-smi."""
    gpus = []
    try:
        result = subprocess.run(['rocm-smi', '--showproductname'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'GPU' in line and ':' in line:
                    name = line.split(':')[-1].strip()
                    gpus.append(GPUInfo(vendor=GPUVendor.AMD, name=name))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fallback: check lspci
    if not gpus:
        try:
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line and ('AMD' in line or 'Radeon' in line):
                        name = line.split(':')[-1].strip() if ':' in line else 'AMD GPU'
                        gpus.append(GPUInfo(vendor=GPUVendor.AMD, name=name))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return gpus


def _detect_intel_gpus() -> List[GPUInfo]:
    """Detect Intel GPUs."""
    gpus = []
    
    if sys.platform.startswith('linux'):
        try:
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line and 'Intel' in line:
                        name = line.split(':')[-1].strip() if ':' in line else 'Intel GPU'
                        gpus.append(GPUInfo(vendor=GPUVendor.INTEL, name=name))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return gpus


def _detect_apple_silicon() -> List[GPUInfo]:
    """Detect Apple Silicon GPU."""
    gpus = []
    
    if sys.platform == 'darwin':
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Apple' in result.stdout:
                gpus.append(GPUInfo(vendor=GPUVendor.APPLE, name='Apple Silicon GPU'))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return gpus


def get_recommended_provider() -> ExecutionProvider:
    """Get the recommended execution provider based on detected hardware."""
    gpus = detect_gpus()
    
    # Check for NVIDIA GPUs first (best support)
    nvidia_gpus = [g for g in gpus if g.vendor == GPUVendor.NVIDIA]
    if nvidia_gpus:
        return ExecutionProvider.CUDA
    
    # Check for AMD GPUs (ROCm on Linux)
    amd_gpus = [g for g in gpus if g.vendor == GPUVendor.AMD]
    if amd_gpus and sys.platform.startswith('linux'):
        return ExecutionProvider.ROCM
    
    # Check for AMD/Intel on Windows (DirectML)
    if sys.platform.startswith('win') and (amd_gpus or [g for g in gpus if g.vendor == GPUVendor.INTEL]):
        return ExecutionProvider.DIRECTML
    
    # Check for Apple Silicon
    apple_gpus = [g for g in gpus if g.vendor == GPUVendor.APPLE]
    if apple_gpus:
        return ExecutionProvider.COREML
    
    # Fallback to CPU
    return ExecutionProvider.CPU


def get_available_providers() -> List[Tuple[ExecutionProvider, str, bool]]:
    """
    Get list of available execution providers with display names and recommended flag.
    Returns: List of (provider, display_name, is_recommended)
    """
    gpus = detect_gpus()
    providers = []
    
    recommended = get_recommended_provider()
    
    # NVIDIA CUDA
    nvidia_gpus = [g for g in gpus if g.vendor == GPUVendor.NVIDIA]
    if nvidia_gpus:
        gpu_name = nvidia_gpus[0].name
        providers.append((
            ExecutionProvider.CUDA,
            f"NVIDIA CUDA + TensorRT ({gpu_name})",
            recommended == ExecutionProvider.CUDA
        ))
    
    # AMD ROCm (Linux only)
    amd_gpus = [g for g in gpus if g.vendor == GPUVendor.AMD]
    if amd_gpus and sys.platform.startswith('linux'):
        gpu_name = amd_gpus[0].name
        providers.append((
            ExecutionProvider.ROCM,
            f"AMD ROCm ({gpu_name})",
            recommended == ExecutionProvider.ROCM
        ))
    
    # DirectML (Windows only)
    if sys.platform.startswith('win'):
        providers.append((
            ExecutionProvider.DIRECTML,
            "DirectML (Windows GPU)",
            recommended == ExecutionProvider.DIRECTML
        ))
    
    # OpenVINO (Intel)
    intel_gpus = [g for g in gpus if g.vendor == GPUVendor.INTEL]
    if intel_gpus:
        providers.append((
            ExecutionProvider.OPENVINO,
            "Intel OpenVINO",
            False
        ))
    
    # CoreML (macOS)
    if sys.platform == 'darwin':
        providers.append((
            ExecutionProvider.COREML,
            "Apple CoreML",
            recommended == ExecutionProvider.COREML
        ))
    
    # CPU fallback (always available)
    providers.append((
        ExecutionProvider.CPU,
        "CPU Only (Slow)",
        recommended == ExecutionProvider.CPU
    ))
    
    return providers


def get_onnxruntime_package(provider: ExecutionProvider) -> str:
    """Get the appropriate onnxruntime package name for a provider."""
    packages = {
        ExecutionProvider.CUDA: "onnxruntime-gpu",
        ExecutionProvider.TENSORRT: "onnxruntime-gpu",
        ExecutionProvider.ROCM: "onnxruntime-rocm",
        ExecutionProvider.DIRECTML: "onnxruntime-directml",
        ExecutionProvider.OPENVINO: "onnxruntime-openvino",
        ExecutionProvider.COREML: "onnxruntime",
        ExecutionProvider.CPU: "onnxruntime",
    }
    return packages.get(provider, "onnxruntime")
