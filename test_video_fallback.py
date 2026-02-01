import cv2
import numpy as np
import sys
import os
import glob

if __name__ != "__main__":
    import pytest
    pytest.skip("Manual video fallback script (requires local media).", allow_module_level=True)

sys.path.append(".")

from facefusion import state_manager
state_manager.init_item('face_detector_model', 'yoloface')  # Test with default (should now fallback)
state_manager.init_item('face_detector_size', '640x640')
state_manager.init_item('face_detector_score', 0.5)
state_manager.init_item('face_detector_angles', [0])
state_manager.init_item('execution_providers', ['cpu'])  # Required for inference_manager
state_manager.init_item('execution_device_ids', [0])

from facefusion.face_analyser import get_many_faces
from facefusion.vision import read_static_video_frame

def test_video(video_path):
    if not os.path.exists(video_path):
        print(f"SKIP: {video_path} (not found)")
        return None
        
    # Test first, middle, and last frame
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    if total_frames == 0:
        print(f"SKIP: {os.path.basename(video_path)} (0 frames)")
        return None
    
    test_frames = [0, total_frames // 2, total_frames - 1]
    detected = 0
    
    for frame_num in test_frames:
        frame = read_static_video_frame(video_path, frame_num)
        if frame is not None:
            faces = get_many_faces([frame])
            if len(faces) > 0:
                detected += 1
    
    rate = (detected / len(test_frames)) * 100
    status = "✅ PASS" if rate >= 66 else "❌ FAIL"
    print(f"{status} {os.path.basename(video_path)}: {rate:.0f}% ({detected}/{len(test_frames)} frames)")
    return rate

if __name__ == "__main__":
    # Test videos from user's folders
    test_videos = [
        "/home/yurix/Google/estudio/vídeos/frankie valli - can't take my eyes off you (live).mp4",
    ]
    
    # Add more videos from the folder
    folder_videos = glob.glob("/home/yurix/Google/estudio/vídeos/*.mp4")[:5]  # First 5 mp4s
    test_videos.extend([v for v in folder_videos if v not in test_videos])
    
    print(f"Testing {len(test_videos)} videos with FALLBACK enabled...")
    print("=" * 60)
    
    results = []
    for video in test_videos:
        rate = test_video(video)
        if rate is not None:
            results.append(rate)
    
    if results:
        avg = sum(results) / len(results)
        print("=" * 60)
        print(f"Average Detection Rate: {avg:.2f}%")
        print(f"Videos Tested: {len(results)}")
