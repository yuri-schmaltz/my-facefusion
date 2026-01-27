from typing import Any, Dict, List
import psutil
from facefusion.types import Face

def suggest_settings(video_path: str, faces: List[Face]) -> Dict[str, Any]:
    """
    Analyzes video and faces to suggest optimal processing settings.
    """
    suggestions = {
        'face_swapper_model': 'inswapper_128', # Default
        'face_enhancer_model': 'gfpgan_1.4', # Default
        'execution_thread_count': psutil.cpu_count(),
        'execution_queue_count': 1
    }
    
    if not faces:
        return suggestions
        
    # Analyze face sizes
    avg_face_width = sum(f.bounding_box[2] - f.bounding_box[0] for f in faces) / len(faces)
    
    # If faces are small, lean towards enhancers with good restoration
    if avg_face_width < 64:
        suggestions['face_enhancer_model'] = 'codeformer'
        
    # Check system memory for queue count
    total_memory = psutil.virtual_memory().total / (1024 ** 3) # GB
    if total_memory > 16:
        suggestions['execution_queue_count'] = 2
        
    return suggestions

def analyze_best_approach(scene_data: Dict[str, Any]) -> str:
    """
    Returns a description of why these settings were chosen.
    """
    # Placeholder for more complex logic
    return "Optimized based on face resolution and system performance."
