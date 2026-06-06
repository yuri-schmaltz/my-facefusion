#!/usr/bin/env python3

import os

os.environ['OMP_NUM_THREADS'] = '1'

from facefusion import conda, core

if __name__ == '__main__':
	from facefusion.app_context import set_app_context
	set_app_context('cli')
	conda.setup()
	core.cli()
