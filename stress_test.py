import os
import subprocess
import sys

# Configuration
PYTHON_EXEC = "/home/yurix/Documentos/my-facefusion/.venv/bin/python"
LAUNCH_SCRIPT = "/home/yurix/Documentos/my-facefusion/launch.py"
OUTPUT_DIR = "/home/yurix/Documentos/my-facefusion/test_outputs"

SOURCE_IMAGE = "/home/yurix/Downloads/IMG-20260124-WA0020.jpg"
TARGET_VIDEO = "/home/yurix/Google/estudio/vídeos/frankie valli - can't take my eyes off you (live).mp4"
TARGET_IMAGE = "/home/yurix/Downloads/image-1766760096697.jpg"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Providers to test (prioritizing CUDA as requested)
PROVIDERS = ["cuda"] 

def run_test(name, args, provider):
    print(f"\\n[TEST] [{provider.upper()}] Running: {name}...")
    cmd_args = args + ["--execution-providers", provider]
    cmd = [PYTHON_EXEC, LAUNCH_SCRIPT, "headless-run"] + cmd_args
    
    # Print command for debugging
    # print(f"Command: {' '.join(cmd)}")
    
    try:
        env = os.environ.copy()
        env['CUDA_MODULE_LOADING'] = 'LAZY'
        
        # Capture output to keep terminal clean, print only on error
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        print(f"[{provider.upper()}] [PASS] Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{provider.upper()}] [FAIL] Error Code: {e.returncode}")
        print(f"STDOUT:\\n{e.stdout[-500:]}") # Last 500 chars
        print(f"STDERR:\\n{e.stderr[-500:]}")
        return False

# Comprehensive list of processors to test
# Most just need source/target. Some might need specific triggering args, but defaults usually run.
all_processors_tests = [
    {"id": "age_modifier", "name": "Age Modifier", "args": ["-s", SOURCE_IMAGE, "-t", TARGET_IMAGE, "--processors", "age_modifier", "--age-modifier-direction", "10"]},
    {"id": "background_blur", "name": "Background Blur", "args": ["-t", TARGET_IMAGE, "--processors", "background_blur", "--background-blur-amount", "50"]},
    {"id": "background_remover", "name": "Background Remover", "args": ["-t", TARGET_IMAGE, "--processors", "background_remover"]},
     # color_matcher usually runs as post-processing, but is a processor? No, usually 'color_transfer' argument? 
     # Checked dir: it is a processor module.
    {"id": "color_matcher", "name": "Color Matcher", "args": ["-s", SOURCE_IMAGE, "-t", TARGET_IMAGE, "--processors", "color_matcher"]}, 
    {"id": "deep_swapper", "name": "Deep Swapper", "args": ["-s", SOURCE_IMAGE, "-t", TARGET_IMAGE, "--processors", "deep_swapper"]},
    {"id": "expression_restorer", "name": "Expression Restorer", "args": ["-t", TARGET_IMAGE, "--processors", "expression_restorer"]},
    # face_accessory_manager might typically add/remove. defaults?
    {"id": "face_accessory_manager", "name": "Face Accessory Manager", "args": ["-t", TARGET_IMAGE, "--processors", "face_accessory_manager"]}, 
    {"id": "face_debugger", "name": "Face Debugger", "args": ["-t", TARGET_IMAGE, "--processors", "face_debugger"]},
    {"id": "face_editor", "name": "Face Editor", "args": ["-t", TARGET_IMAGE, "--processors", "face_editor"]},
    {"id": "face_enhancer", "name": "Face Enhancer", "args": ["-t", TARGET_IMAGE, "--processors", "face_enhancer"]},
    {"id": "face_relighter", "name": "Face Relighter", "args": ["-t", TARGET_IMAGE, "--processors", "face_relighter"]},
    # face_stabilizer typically for video
    {"id": "face_stabilizer", "name": "Face Stabilizer", "args": ["-t", TARGET_VIDEO, "--processors", "face_stabilizer", "-o", os.path.join(OUTPUT_DIR, "stabilizer.mp4"), "--trim-frame-end", "2"]},
    {"id": "face_swapper", "name": "Face Swapper", "args": ["-s", SOURCE_IMAGE, "-t", TARGET_IMAGE, "--processors", "face_swapper"]},
    {"id": "frame_colorizer", "name": "Frame Colorizer", "args": ["-t", TARGET_IMAGE, "--processors", "frame_colorizer"]},
    {"id": "frame_enhancer", "name": "Frame Enhancer", "args": ["-t", TARGET_IMAGE, "--processors", "frame_enhancer"]},
    # frame_expander might fail if input is same size as output? defaults ok? 
    # {"id": "frame_expander", "name": "Frame Expander", "args": ["-t", TARGET_IMAGE, "--processors", "frame_expander"]}, # Skip for now, complex args?
    {"id": "gaze_corrector", "name": "Gaze Corrector", "args": ["-t", TARGET_IMAGE, "--processors", "gaze_corrector"]},
    # grain_matcher often needs source
    # {"id": "grain_matcher", "name": "Grain Matcher", "args": ["-s", SOURCE_IMAGE, "-t", TARGET_IMAGE, "--processors", "grain_matcher"]},
    {"id": "hair_colorizer", "name": "Hair Colorizer", "args": ["-t", TARGET_IMAGE, "--processors", "hair_colorizer"]},
    {"id": "lip_syncer", "name": "Lip Syncer", "args": ["-s", "/home/yurix/Downloads/test_audio.mp3", "-t", TARGET_VIDEO, "--processors", "lip_syncer", "-o", os.path.join(OUTPUT_DIR, "lipsync.mp4"), "--trim-frame-end", "2"]},
    {"id": "makeup_transfer", "name": "Makeup Transfer", "args": ["-s", SOURCE_IMAGE, "-t", TARGET_IMAGE, "--processors", "makeup_transfer"]},
    {"id": "privacy_blur", "name": "Privacy Blur", "args": ["-t", TARGET_IMAGE, "--processors", "privacy_blur", "--privacy-blur-mode", "blur"]},
    {"id": "watermark_remover", "name": "Watermark Remover", "args": ["-t", TARGET_IMAGE, "--processors", "watermark_remover", "--watermark-remover-area-start", "0", "0", "--watermark-remover-area-end", "10", "10"]}
]

failed_tests = []

print(f"Testing {len(all_processors_tests)} processors on {PROVIDERS}...")

for provider in PROVIDERS:
    print(f"\\n=== Testing Provider: {provider.upper()} ===")
    for test in all_processors_tests:
        # Determine output filename
        ext = "mp4" if "mp4" in str(test.get("args")) else "jpg"
        # Overwrite -o if specific test didn't hardcode it (some video tests did)
        if "-o" not in test["args"]:
             output_file = os.path.join(OUTPUT_DIR, f"{provider}_{test['id']}.{ext}")
             current_args = test["args"] + ["-o", output_file]
        else:
             current_args = test["args"]
        
        if not run_test(test["name"], current_args, provider):
            failed_tests.append(f"{provider} - {test['name']}")

print("\\n" + "="*30)
if failed_tests:
    print(f"FAIL: {len(failed_tests)} tests failed.")
    for t in failed_tests:
        print(f" - {t}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
