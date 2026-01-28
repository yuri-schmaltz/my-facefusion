from typing import List, Tuple
import cv2
# import numpy
from facefusion.vision import get_video_capture, count_video_frame_total
from facefusion.thread_helper import thread_semaphore


def detect_scene_cuts(video_path: str, threshold: float = 0.3, progress_callback = None) -> List[int]:
    scene_cuts = [0]
    # Use a private capture to avoid locking/contention with the global pool
    video_capture = cv2.VideoCapture(video_path)
    
    if video_capture and video_capture.isOpened():
        frame_total = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        prev_hist = None
        
        # Optimization: Downscale frame for faster histogram calculation
        # 64x64 is sufficient for color distribution comparison
        process_size = (64, 64) 
        
        for frame_number in range(frame_total):
            if progress_callback and frame_number % 10 == 0: # Reduce callback frequency
                progress_callback(frame_number / frame_total)

            # Direct sequential read - NO SEEKING
            has_frame, frame = video_capture.read()
            
            if not has_frame:
                break
            
            # Optimization: Resize small
            small_frame = cv2.resize(frame, process_size)
            
            # Convert to HSV 
            hsv = cv2.cvtColor(small_frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            
            if prev_hist is not None:
                score = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if score < threshold:
                    scene_cuts.append(frame_number)
            
            prev_hist = hist
            
        video_capture.release()
            
    return scene_cuts

def get_scene_timeframes(video_path: str, threshold: float = 0.3, progress_callback = None) -> List[Tuple[int, int]]:
    scene_cuts = detect_scene_cuts(video_path, threshold, progress_callback)
    frame_total = count_video_frame_total(video_path)
    timeframes = []
    
    for i in range(len(scene_cuts)):
        start = scene_cuts[i]
        end = scene_cuts[i+1] if i+1 < len(scene_cuts) else frame_total
        timeframes.append((start, end))
        
    return timeframes
