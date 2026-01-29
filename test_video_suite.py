#!/usr/bin/env python3
"""
Exhaustive Video Face Detection Test Suite
Tests the fallback mechanism across all user videos
"""
import os
import subprocess
import glob
import json

VENV_PYTHON = "/home/yurix/Documentos/my-facefusion/.venv/bin/python"
LAUNCH_SCRIPT = "/home/yurix/Documentos/my-facefusion/launch.py"
OUTPUT_DIR = "/home/yurix/Documentos/my-facefusion/test_outputs/video_tests"

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Find all video files
video_folders = [
    "/home/yurix/Google/estudio/vídeos",
    "/home/yurix/Downloads"
]

test_videos = []
for folder in video_folders:
    if os.path.exists(folder):
        test_videos.extend(glob.glob(f"{folder}/*.mp4")[:3])  # 3 from each folder
        test_videos.extend(glob.glob(f"{folder}/*.avi")[:1])
        test_videos.extend(glob.glob(f"{folder}/*.mov")[:1])

# Deduplicate
test_videos = list(set(test_videos))

print(f"Testing {len(test_videos)} videos...")
print("=" * 70)

results = []

for video_path in test_videos:
    video_name = os.path.basename(video_path)
    output_path = os.path.join(OUTPUT_DIR, f"test_{video_name}")
    
    # Test with face_debugger (shows face detection)
    cmd = [
        VENV_PYTHON, LAUNCH_SCRIPT, "headless-run",
        "-t", video_path,
        "--processors", "face_debugger",
        "-o", output_path,
        "--trim-frame-end", "30",  # Only first 30 frames
        "--execution-providers", "cpu"
    ]
    
    print(f"Testing: {video_name}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Check if output was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                results.append({
                    "video": video_name,
                    "status": "✅ PASS",
                    "output_size": file_size
                })
                print(f"  ✅ Success ({file_size:,} bytes)")
            else:
                results.append({
                    "video": video_name,
                    "status": "⚠️  No output",
                    "output_size": 0
                })
                print(f"  ⚠️  Command succeeded but no output file")
        else:
            # Check stderr for specific errors
            if "choose a face for the source" in result.stderr or "No face" in result.stderr:
                results.append({
                    "video": video_name,
                    "status": "❌ No faces detected",
                    "error": "No faces found in video"
                })
                print(f"  ❌ No faces detected (fallback might still be failing)")
            else:
                results.append({
                    "video": video_name,
                    "status": "❌ FAIL",
                    "error": result.stderr[-200:] if result.stderr else ""
                })
                print(f"  ❌ Failed: {result.stderr[-100:]}")
    except subprocess.TimeoutExpired:
        results.append({
            "video": video_name,
            "status": "⏱️  Timeout",
            "error": "Exceeded 120s"
        })
        print(f"  ⏱️  Timeout")
    except Exception as e:
        results.append({
            "video": video_name,
            "status": "💥 Error",
            "error": str(e)
        })
        print(f"  💥 Error: {e}")

print("=" * 70)
print(f"\\nSummary:")
print(f"Total Tested: {len(results)}")
passed = sum(1 for r in results if r['status'] == '✅ PASS')
print(f"Passed: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")

# Save results
with open(os.path.join(OUTPUT_DIR, "test_results.json"), "w") as f:
    json.dump(results, f, indent=2)
    
print(f"\\nDetailed results saved to: {OUTPUT_DIR}/test_results.json")
