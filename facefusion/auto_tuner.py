from typing import Any, Dict, List
import psutil
from facefusion.types import Face

def suggest_settings(video_path: str, faces: List[Face]) -> Dict[str, Any]:
    """
    Analyzes video and faces to suggest optimal processing settings.
    """
    from facefusion.execution import get_available_execution_providers

    suggestions = {
        'face_swapper_model': 'inswapper_128', # Default
        'face_enhancer_model': 'gfpgan_1.4', # Default
        'execution_thread_count': psutil.cpu_count(),
        'execution_queue_count': 1,
        'system_memory_limit': 0, # Default to 0 (auto/unlimited)
        'execution_providers': ['cpu'] # Default
    }
    
    # 1. Detect best execution provider (GPU support)
    available_providers = get_available_execution_providers()
    unique_providers = []
    
    # Prioritize GPU providers: CUDA > CoreML > ROCm > DirectML > OpenVINO > CPU
    # We filter for 'cuda', 'coreml', 'rocm', 'directml' ...
    # And we just return the full list of detected capable providers, or suggest the best one.
    # The UI expects a list of providers to use.
    
    # Simpler approach: Just pass through the detected available providers, 
    # but filter out 'tensorrt' if it causes issues, or keep them.
    # Let's prefer suggesting ALL available hardware accelerators using the helper.
    # Actually, let's keep it simple: if 'cuda' is available, suggest ['cuda', 'cpu'].
    
    suggested_providers = []
    if 'CUDAExecutionProvider' in available_providers:
        suggested_providers.append('cuda')
    if 'CoreMLExecutionProvider' in available_providers:
        suggested_providers.append('coreml')
    if 'ROCMExecutionProvider' in available_providers:
        suggested_providers.append('rocm')
    if 'DmlExecutionProvider' in available_providers:
        suggested_providers.append('directml')
    if 'OpenVINOExecutionProvider' in available_providers:
        suggested_providers.append('openvino')
        
    suggested_providers.append('cpu') 
    suggestions['execution_providers'] = suggested_providers

    if not faces:
        return suggestions
        
    # Analyze face sizes
    avg_face_width = sum(f.bounding_box[2] - f.bounding_box[0] for f in faces) / len(faces)
    
    # If faces are small, lean towards enhancers with good restoration
    if avg_face_width < 64:
        suggestions['face_enhancer_model'] = 'codeformer'
        
    # Check system memory for queue count
    total_memory = psutil.virtual_memory().total / (1024 ** 3) # GB
    
    # Suggest memory limit: Leave ~2-4GB for OS if possible, or just default to 0 (all)
    # Actually, users like to see a number. Let's suggest 80% of total ram if > 8GB
    if total_memory > 8:
        suggestions['system_memory_limit'] = int(total_memory * 0.8)
    else:
        suggestions['system_memory_limit'] = int(total_memory - 1) if total_memory > 2 else 0

    if total_memory > 16:
        suggestions['execution_queue_count'] = 2
        
    return suggestions

def analyze_best_approach(scene_data: Dict[str, Any]) -> str:
    """
    Returns a description of why these settings were chosen.
    """
    # Placeholder for more complex logic
    return "Optimized based on face resolution and system performance."
