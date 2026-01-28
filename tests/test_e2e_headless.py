import subprocess
import sys
import pytest
from .helper import get_test_example_file, get_test_jobs_directory, get_test_output_file, is_test_output_file

def test_erosion_argument_accepted() -> None:
    # Test if --face-mask-erosion is accepted and program runs
    commands = [
        sys.executable, 'facefusion.py', 'headless-run',
        '--jobs-path', get_test_jobs_directory(),
        '--processors', 'face_swapper',
        '-s', get_test_example_file('source.jpg'),
        '-t', get_test_example_file('target-240p.jpg'),
        '-o', get_test_output_file('test-erosion.jpg'),
        '--face-mask-erosion', '0.1',
        '--trim-frame-end', '1'
    ]
    result = subprocess.run(commands, capture_output=True, text=True)
    assert result.returncode == 0
    assert is_test_output_file('test-erosion.jpg') is True

def test_region_selector_argument_accepted() -> None:
    # Test if --face-selector-region is accepted
    commands = [
        sys.executable, 'facefusion.py', 'headless-run',
        '--jobs-path', get_test_jobs_directory(),
        '--processors', 'face_swapper',
        '-s', get_test_example_file('source.jpg'),
        '-t', get_test_example_file('target-240p.jpg'),
        '-o', get_test_output_file('test-region.jpg'),
        '--face-selector-region', '0', '0', '100', '100',
        '--trim-frame-end', '1'
    ]
    result = subprocess.run(commands, capture_output=True, text=True)
    assert result.returncode == 0
    assert is_test_output_file('test-region.jpg') is True

def test_region_selector_filtering_no_match() -> None:
    # Test with a region where no face exists (top-left 1x1 percent)
    commands = [
        sys.executable, 'facefusion.py', 'headless-run',
        '--jobs-path', get_test_jobs_directory(),
        '--processors', 'face_swapper',
        '-s', get_test_example_file('source.jpg'),
        '-t', get_test_example_file('target-240p.jpg'),
        '-o', get_test_output_file('test-region-none.jpg'),
        '--face-selector-region', '0', '0', '1', '1', # Likely no face here
        '--trim-frame-end', '1'
    ]
    result = subprocess.run(commands, capture_output=True, text=True)
    # If no face is found, the processor might still "succeed" but output unchanged frame or just exit.
    # Actually FaceFusion core usually continues if no faces are found.
    assert result.returncode == 0
