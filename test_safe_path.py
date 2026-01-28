import os
import sys

# Mocking filesystem.py logic
def is_safe_path(file_path):
    if file_path:
        workspace_path = os.getcwd()
        temp_path = os.path.realpath('/tmp')
        absolute_path = os.path.abspath(file_path)
        return absolute_path.startswith(workspace_path) or absolute_path.startswith(temp_path)
    return False

tests = [
    ('facefusion.log', True),
    ('facefusion.ini', True),
    ('/tmp/facefusion/test.png', True),
    ('../outside.mp4', False),
    ('/etc/passwd', False),
    ('./data/output.mp4', True)
]

for path, expected in tests:
    result = is_safe_path(path)
    print(f"Path: {path} | Expected: {expected} | Result: {result} | {'PASS' if result == expected else 'FAIL'}")
    if result != expected:
        sys.exit(1)
print("All is_safe_path tests PASSED")
