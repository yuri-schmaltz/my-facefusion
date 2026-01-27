from typing import List, Dict
import numpy
from facefusion.types import Face, Embedding
from facefusion.face_recognizer import calculate_face_embedding

def cluster_faces(faces: List[Face], threshold: float = 0.6) -> List[List[Face]]:
    clusters = []
    
    for face in faces:
        found_cluster = False
        for cluster in clusters:
            # Compare with the average embedding of the cluster or just the first one?
            # For simplicity and efficiency in the wizard, we compare with the first one.
            # A more robust approach would be to maintain a centroid.
            reference_face = cluster[0]
            distance = numpy.linalg.norm(face.embedding_norm - reference_face.embedding_norm)
            
            # Since distance is Euclidean on normalized embeddings, it's roughly 1 - cosine similarity
            # Distance near 0 means very similar.
            if distance < threshold:
                cluster.append(face)
                found_cluster = True
                break
        
        if not found_cluster:
            clusters.append([face])
            
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
