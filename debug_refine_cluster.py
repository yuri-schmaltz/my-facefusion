
import numpy
from facefusion.face_clusterer import refine_clusters
from facefusion.types import Face

def create_mock_face(embedding_value):
    embedding = numpy.array([embedding_value] * 512, dtype=numpy.float64)
    norm_val = numpy.linalg.norm(embedding)
    embedding_norm = embedding / norm_val if norm_val > 0 else embedding

    return Face(
        bounding_box=numpy.array([0, 0, 10, 10]),
        score_set={'score': 0.9},
        landmark_set={'2d_106': numpy.array([])},
        angle=0.0,
        embedding=embedding,
        embedding_norm=embedding_norm,
        gender='male',
        age=25,
        race='white'
    )

def test_refine_clusters():
    # Create two groups that are very similar (should merge)
    # Face A: mainly 1.0s
    face_a1 = create_mock_face(1.0)
    face_a2 = create_mock_face(0.95) # Very close to 1.0
    
    # Face B: mainly -1.0s (far from A)
    face_b1 = create_mock_face(-1.0)
    
    # Face C: mainly 0.0 (orthogonal to A and B)
    face_c1 = create_mock_face(0.0)
    
    # Initial clusters: [A1, A2], [B1], [C1]
    # Ideally A1 and A2 are already clustered, but let's say the initial clustering split them
    # Scenario: Cluster 1 has face_a1, Cluster 2 has face_a2.
    # Since 0.95 and 1.0 are very close, their centroids should match.
    
    clusters = [
        [face_a1],
        [face_a2],
        [face_b1],
        [face_c1]
    ]
    
    print(f"Initial clusters: {len(clusters)}")
    
    refined = refine_clusters(clusters, threshold=0.35)
    
    print(f"Refined clusters: {len(refined)}")
    
    # Verification
    # We expect A1 and A2 to merge -> 3 clusters total
    if len(refined) == 3:
        print("SUCCESS: Merged 4 clusters into 3")
        # Check sizes
        sizes = sorted([len(c) for c in refined], reverse=True)
        print(f"Cluster sizes: {sizes}") # Should be [2, 1, 1]
    else:
        print(f"FAILURE: Expected 3 clusters, got {len(refined)}")

if __name__ == "__main__":
    test_refine_clusters()
