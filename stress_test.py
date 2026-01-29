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

# Providers to test
# Reordered to try GPU first
PROVIDERS = ["cuda", "tensorrt", "cpu"]

def run_test(name, args, provider):
    print(f"\\n[TEST] [{provider.upper()}] Running: {name}...")
    # Add provider to args
    cmd_args = args + ["--execution-providers", provider]
    
    cmd = [PYTHON_EXEC, LAUNCH_SCRIPT, "headless-run"] + cmd_args
    print(f"Command: {' '.join(cmd)}")
    try:
        # Increase timeout for model downloads
        env = os.environ.copy()
        env['CUDA_MODULE_LOADING'] = 'LAZY' # Optimization for CUDA
        
        # We print output to stdout to see progress in real-time if run interactively, 
        # but here we capture to analyze. 
        # Actually, let's NOT capture output, so it streams to the main process stdout and we can see it in `command_status`.
        # But `subprocess.run` with `capture_output=False` writes to parent's stdout.
        # The agent tool `run_command` captures the parent's stdout.
        # So we should validly NOT capture it here if we want to see it in the tool output while running.
        # However, to check for success/failure string matching, capturing is useful.
        # Let's capture but print on failure OR success.
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        print(f"[{provider.upper()}] [PASS] Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{provider.upper()}] [FAIL] Error Code: {e.returncode}")
        print(f"STDOUT:\\n{e.stdout}")
        print(f"STDERR:\\n{e.stderr}")
        return False

# Base Tests
base_tests = [
    {
        "id": "swap_img",
        "name": "Face Swapper (Image -> Image)",
        "args": [
            "-s", SOURCE_IMAGE,
            "-t", TARGET_IMAGE,
            "--processors", "face_swapper"
        ],
        "ext": "jpg"
    },
    {
        "id": "swap_vid",
        "name": "Face Swapper (Image -> Video)",
        "args": [
            "-s", SOURCE_IMAGE,
            "-t", TARGET_VIDEO,
            "--processors", "face_swapper",
            "--trim-frame-end", "2" # Very short trim for speed
        ],
        "ext": "mp4"
    },
     {
        "id": "enhance_img",
        "name": "Face Enhancer (Image -> Image)",
        "args": [
            "-t", TARGET_IMAGE,
            "--processors", "face_enhancer"
        ],
        "ext": "jpg"
    }
]

failed_tests = []

for provider in PROVIDERS:
    print(f"\\n--- Testing Provider: {provider.upper()} ---")
    for test in base_tests:
        output_file = os.path.join(OUTPUT_DIR, f"{provider}_{test['id']}.{test['ext']}")
        # Copy args to avoid mutation issues if any
        current_args = test["args"].copy() + ["-o", output_file]
        
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


print("\\n" + "="*30)
if failed_tests:
    print(f"FAIL: {len(failed_tests)} tests failed.")
    for t in failed_tests:
        print(f" - {t}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
