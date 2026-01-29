import cv2
import numpy as np
import sys
import os

# Setup paths
sys.path.append(".")

from facefusion import state_manager
# Configure state for detection
state_manager.init_item('face_detector_model', 'retinaface')
state_manager.init_item('face_detector_size', '640x640')
state_manager.init_item('face_detector_score', 0.5)
# Default angles usually [0]
state_manager.init_item('face_detector_angles', [0, 90, 180, 270]) 

from facefusion.face_detector import detect_faces

VIDEO_PATH = "/home/yurix/Google/estudio/vídeos/frankie valli - can't take my eyes off you (live).mp4"

def debug_video(video_path):
    if not os.path.exists(video_path):
        print(f"File not found: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing {video_path}...")
    print(f"Total Frames: {total_frames}")

    frames_with_faces = 0
    scanned_frames = 0
    
    # Check every 30th frame to be faster
    step = 30 
    
    current_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if current_frame % step == 0:
            scanned_frames += 1
            # Detect
            # detection returns (bounding_boxes, face_scores, face_landmarks_5)
            # We just care if any exist
            _, scores, _ = detect_faces(frame)
            
            if len(scores) > 0:
                frames_with_faces += 1
                # print(f"Frame {current_frame}: Found {len(scores)} faces")
            else:
                print(f"Frame {current_frame}: NO FACE FOUND")
        
        current_frame += 1
        
    cap.release()
    
    if scanned_frames > 0:
        rate = (frames_with_faces / scanned_frames) * 100
        print(f"\\nSummary:")
        print(f"Scanned Frames: {scanned_frames}")
        print(f"Frames with Faces: {frames_with_faces}")
        print(f"Detection Rate: {rate:.2f}%")
    else:
        print("No frames scanned.")

if __name__ == "__main__":
    debug_video(VIDEO_PATH)
