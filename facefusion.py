#!/usr/bin/env python3
"""
FaceFusion Core CLI (facefusion.py)
-----------------------------------
Direct interface to the Python backend.
Usage:
    - As a library: import facefusion
    - As a CLI: python facefusion.py [command]
    - As a worker: python facefusion.py run
"""


import os

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import core

if __name__ == '__main__':
	core.cli()
