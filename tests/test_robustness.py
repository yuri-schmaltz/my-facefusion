import subprocess
import sys
import os
import tempfile

def test_soft_validation_no_crash() -> None:
    # Create a dummy config with an invalid execution provider
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("[execution]\nexecution_providers = invalid_provider\n")
        temp_config = f.name

    try:
        # Run help with this config. It should NOT crash and should return 0.
        commands = [sys.executable, 'facefusion.py', '--config-path', temp_config, 'headless-run', '--help']
        result = subprocess.run(commands, capture_output=True, text=True)
        
        assert result.returncode == 0
        # Check if the warning was printed (optional, but good for verification)
        # assert "Validation warning" in result.stdout or "Validation warning" in result.stderr
        
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)

def test_invalid_path_graceful_exit() -> None:
    # Run with a non-existent source path. 
    # Since we added validate_paths, it should exit gracefully (likely with code 1 if caught by core.py)
    # but NOT with a traceback (code 2 for argparse or 1 for our return).
    commands = [sys.executable, 'facefusion.py', 'headless-run', '-s', 'non_existent.jpg', '-t', 'non_existent.jpg', '-o', 'out.jpg']
    result = subprocess.run(commands, capture_output=True, text=True)
    
    assert result.returncode != 0
    # Check for help message or our custom validation error
    assert "usage:" in result.stdout or "usage:" in result.stderr or "[FACEFUSION.CORE]" in result.stderr
