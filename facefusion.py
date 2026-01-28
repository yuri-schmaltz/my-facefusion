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
import sys

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import core, logger, thread_helper

if __name__ == '__main__':
	try:
		if core.cli() or thread_helper.is_windows():
			sys.exit(0)
		sys.exit(1)
	except KeyboardInterrupt:
		sys.exit(1)
	except Exception as exception:
		print('CRITICAL ERROR OCCURRED:')
		print(exception)
		logger.error(str(exception), __name__)
		sys.exit(1)
