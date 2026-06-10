import os
import sys
from typing import List

from facefusion.common_helper import is_linux, is_windows


def setup() -> None:
	env_prefix = os.getenv('CONDA_PREFIX') or os.getenv('VIRTUAL_ENV') or sys.prefix
	env_ready = os.getenv('ENV_READY') or os.getenv('CONDA_READY')

	if env_prefix and not env_ready:
		if is_linux():
			python_id = 'python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)
			library_paths : List[str] =\
			[
				os.path.join(env_prefix, 'lib'),
				os.path.join(env_prefix, 'lib', python_id, 'site-packages', 'tensorrt_libs')
			]
			library_paths = list(filter(os.path.exists, library_paths))

			if library_paths:
				if os.getenv('LD_LIBRARY_PATH'):
					library_paths.append(os.getenv('LD_LIBRARY_PATH'))
				os.environ['LD_LIBRARY_PATH'] = os.pathsep.join(library_paths)
				os.environ['ENV_READY'] = '1'
				os.environ['CONDA_READY'] = '1'
				os.execv(sys.executable, [ sys.executable ] + sys.argv)

		if is_windows():
			library_paths =\
			[
				os.path.join(env_prefix, 'Lib'),
				os.path.join(env_prefix, 'Lib', 'site-packages', 'tensorrt_libs')
			]
			library_paths = list(filter(os.path.exists, library_paths))

			if library_paths:
				if os.getenv('PATH'):
					library_paths.append(os.getenv('PATH'))
				os.environ['PATH'] = os.pathsep.join(library_paths)
				os.environ['ENV_READY'] = '1'
				os.environ['CONDA_READY'] = '1'
