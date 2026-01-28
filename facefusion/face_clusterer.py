from typing import List, Dict
import numpy
from facefusion.types import Face, Embedding
from facefusion.face_recognizer import calculate_face_embedding

def cluster_faces(faces: List[Face], threshold: float = 0.4) -> List[List[Face]]:
    """
    Cluster faces by embedding similarity using cosine distance.
    
    A lower threshold means stricter matching (more clusters).
    A higher threshold means looser matching (fewer clusters).
    
    For cosine distance:
    - 0.0 = identical faces
    - 0.4 = similar faces (same person)
    - 1.0 = unrelated faces
    """
    if not faces:
        return []
        
    clusters = []
    
    for face in faces:
        if face.embedding_norm is None:
            # Skip faces without embeddings
            continue
            
        found_cluster = False
        for cluster in clusters:
            reference_face = cluster[0]
            
            if reference_face.embedding_norm is None:
                continue
                
            # Use cosine distance (consistent with face_selector.py)
            # For normalized vectors: cosine_distance = 1 - dot(a, b)
            cosine_distance = 1 - numpy.dot(face.embedding_norm, reference_face.embedding_norm)
            
            if cosine_distance < threshold:
                cluster.append(face)
                found_cluster = True
                break
        
        if not found_cluster:
            clusters.append([face])
            
    print(f"[CLUSTER] {len(faces)} faces -> {len(clusters)} clusters (threshold={threshold})")
    return clusters

def group_faces_by_scene(scene_faces: Dict[int, List[Face]], threshold: float = 0.6) -> Dict[int, List[List[Face]]]:
    """
    Groups faces within each scene.
    scene_faces: mapping of scene_index -> list of faces detected in that scene.
    """
    grouped_scenes = {}
    for scene_idx, faces in scene_faces.items():
        grouped_scenes[scene_idx] = cluster_faces(faces, threshold)
    return grouped_scenes
