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


def refine_clusters(clusters: List[List[Face]], threshold: float = 0.35) -> List[List[Face]]:
    """
    Refine existing clusters by merging those with similar centroids.
    This helps merge split groups of the same person.
    """
    if not clusters:
        return []

    # 1. Calculate centroids for each cluster
    cluster_centroids = []
    for cluster in clusters:
        if not cluster:
            continue
            
        embeddings = [face.embedding_norm for face in cluster if face.embedding_norm is not None]
        if not embeddings:
            continue
            
        # Average the embeddings
        centroid = numpy.mean(embeddings, axis=0)
        # Re-normalize to ensure unit vector for cosine distance
        norm = numpy.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
            
        cluster_centroids.append({
            'faces': cluster,
            'centroid': centroid
        })

    # 2. Cluster the centroids
    # We use a simple greedy approach similar to cluster_faces but operating on centroids
    new_meta_clusters = []

    for item in cluster_centroids:
        item_centroid = item['centroid']
        found_cluster = False
        
        for meta_cluster in new_meta_clusters:
            # Compare with the first cluster in the meta-cluster (representative)
            reference_item = meta_cluster[0]
            reference_centroid = reference_item['centroid']
            
            cosine_distance = 1 - numpy.dot(item_centroid, reference_centroid)
            
            if cosine_distance < threshold:
                print(f"[REFINE] Merging cluster into meta_cluster (dist={cosine_distance:.4f})")
                meta_cluster.append(item)
                found_cluster = True
                break
        
        if not found_cluster:
            new_meta_clusters.append([item])

    # 3. Flatten back to List[List[Face]]
    refined_clusters = []
    for meta_cluster in new_meta_clusters:
        merged_faces = []
        for item in meta_cluster:
            merged_faces.extend(item['faces'])
        refined_clusters.append(merged_faces)

    print(f"[REFINE] Merged {len(clusters)} initial clusters into {len(refined_clusters)} final clusters (threshold={threshold})")
    return refined_clusters
