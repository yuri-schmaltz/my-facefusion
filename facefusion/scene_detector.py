from typing import List, Tuple
import cv2
import numpy
from facefusion.vision import get_video_capture, count_video_frame_total
from facefusion.thread_helper import thread_semaphore


def detect_scene_cuts(video_path: str, threshold: float = 0.3, progress_callback = None) -> List[int]:
    scene_cuts = [0]
    video_capture = get_video_capture(video_path)
    
    if video_capture and video_capture.isOpened():
        frame_total = count_video_frame_total(video_path)
        prev_hist = None
        
        # We sample frames to speed up detection, e.g., every 5 frames
        # But for robust scene detection, we might want to check every frame if performance allows
        # For the wizard, let's go with every frame for better accuracy in short clips
        for frame_number in range(frame_total):
            if progress_callback and frame_number % 5 == 0:
                progress_callback(frame_number / frame_total)

            with thread_semaphore():
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                has_frame, frame = video_capture.read()
            
            if not has_frame:
                break
            
            # Convert to HSV for better color-based histogram comparison
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            
            if prev_hist is not None:
                # Use intersection as a distance metric
                score = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if score < threshold:
                    scene_cuts.append(frame_number)
            
            prev_hist = hist
            
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
