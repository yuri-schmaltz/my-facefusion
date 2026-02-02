#!/usr/bin/env python3
"""
Face Forge Core CLI (faceforge.py)
----------------------------------
Direct interface to the Python backend.
Usage:
	- As a library: import facefusion
	- As a CLI: python faceforge.py [command]
	- As a worker: python faceforge.py run
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
		import traceback
		traceback.print_exc()
		logger.error(str(exception), __name__)
		sys.exit(1)
