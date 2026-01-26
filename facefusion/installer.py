import os
import shutil
import signal
import subprocess
import sys
from argparse import ArgumentParser, HelpFormatter
from functools import partial
from types import FrameType

from facefusion import metadata
from facefusion.common_helper import is_linux, is_windows

LOCALES =\
{
	'install_dependency': 'install the {dependency} package',
	'force_reinstall': 'force reinstall of packages',
	'skip_conda': 'skip the conda environment check',
	'conda_not_activated': 'conda is not activated'
}
ONNXRUNTIME_SET =\
{
	'default': ('onnxruntime', '1.23.2')
}
if is_windows() or is_linux():
	ONNXRUNTIME_SET['cuda'] = ('onnxruntime-gpu', '1.23.2')
	ONNXRUNTIME_SET['openvino'] = ('onnxruntime-openvino', '1.23.0')
if is_windows():
	ONNXRUNTIME_SET['directml'] = ('onnxruntime-directml', '1.23.0')
if is_linux():
	ONNXRUNTIME_SET['migraphx'] = ('onnxruntime-migraphx', '1.23.0')
	ONNXRUNTIME_SET['rocm'] = ('onnxruntime_rocm', '1.22.1', '7.0.2') #type:ignore[assignment]


def cli() -> None:
	signal.signal(signal.SIGINT, signal_exit)
	program = ArgumentParser(formatter_class = partial(HelpFormatter, max_help_position = 50))
	program.add_argument('--onnxruntime', help = LOCALES.get('install_dependency').format(dependency = 'onnxruntime'), choices = ONNXRUNTIME_SET.keys())
	program.add_argument('--force-reinstall', help = LOCALES.get('force_reinstall'), action = 'store_true')
	program.add_argument('--skip-conda', help = LOCALES.get('skip_conda'), action = 'store_true')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def signal_exit(signum : int, frame : FrameType) -> None:
	sys.exit(0)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()
	
	if args.onnxruntime is None:
		print("Choose an ONNX Runtime provider:")
		options = list(ONNXRUNTIME_SET.keys())
		for i, option in enumerate(options):
			print(f"[{i}] {option}")
		try:
			selection = int(input(f"Select an option (0-{len(options)-1}) [default: 0]: ") or 0)
			if 0 <= selection < len(options):
				args.onnxruntime = options[selection]
			else:
				print("Invalid selection, using default.")
				args.onnxruntime = 'default'
		except ValueError:
			print("Invalid input, using default.")
			args.onnxruntime = 'default'
			
	has_conda = 'CONDA_PREFIX' in os.environ
	has_venv = sys.prefix != sys.base_prefix
	commands = [ sys.executable, '-m', 'pip', 'install' ]

	if args.force_reinstall:
		commands.append('--force-reinstall')

	if not args.skip_conda and not has_conda and not has_venv:
		sys.stdout.write(LOCALES.get('conda_not_activated') + os.linesep)
		sys.exit(1)

	with open('requirements.txt') as file:

		for line in file.readlines():
			__line__ = line.strip()
			if not __line__.startswith('onnxruntime'):
				commands.append(__line__)

	if args.onnxruntime == 'rocm':
		onnxruntime_name, onnxruntime_version, rocm_version = ONNXRUNTIME_SET.get(args.onnxruntime) #type:ignore[misc]
		python_id = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)

		if python_id in [ 'cp310', 'cp312' ]:
			wheel_name = onnxruntime_name + '-' + onnxruntime_version + '-' + python_id + '-' + python_id + '-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl'
			wheel_url = 'https://repo.radeon.com/rocm/manylinux/rocm-rel-' + rocm_version + '/' + wheel_name
			commands.append(wheel_url)
	else:
		onnxruntime_name, onnxruntime_version = ONNXRUNTIME_SET.get(args.onnxruntime)
		commands.append(onnxruntime_name + '==' + onnxruntime_version)

	subprocess.call(commands)

	if args.onnxruntime == 'cuda' and has_conda:
		library_paths = []

		if is_linux():
			if os.getenv('LD_LIBRARY_PATH'):
				library_paths = os.getenv('LD_LIBRARY_PATH').split(os.pathsep)

			python_id = 'python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)
			library_paths.extend(
			[
				os.path.join(os.getenv('CONDA_PREFIX'), 'lib'),
				os.path.join(os.getenv('CONDA_PREFIX'), 'lib', python_id, 'site-packages', 'tensorrt_libs')
			])
			library_paths = list(dict.fromkeys([ library_path for library_path in library_paths if os.path.exists(library_path) ]))

			subprocess.call([ shutil.which('conda'), 'env', 'config', 'vars', 'set', 'LD_LIBRARY_PATH=' + os.pathsep.join(library_paths) ])

		if is_windows():
			if os.getenv('PATH'):
				library_paths = os.getenv('PATH').split(os.pathsep)

			library_paths.extend(
			[
				os.path.join(os.getenv('CONDA_PREFIX'), 'Lib'),
				os.path.join(os.getenv('CONDA_PREFIX'), 'Lib', 'site-packages', 'tensorrt_libs')
			])
			library_paths = list(dict.fromkeys([ library_path for library_path in library_paths if os.path.exists(library_path) ]))

			subprocess.call([ shutil.which('conda'), 'env', 'config', 'vars', 'set', 'PATH=' + os.pathsep.join(library_paths) ])

	# Frontend Installation
	web_path = os.path.join(os.getcwd(), 'web')
	if os.path.exists(web_path) and shutil.which('npm'):
		print("Installing Frontend Dependencies...")
		subprocess.call([shutil.which('npm'), 'install'], cwd=web_path)

	# Desktop Shortcuts & Config
	install_path = os.getcwd() # install.py run from root
	create_user_config(install_path)
	
	platform = get_platform()
	if platform == 'linux':
		create_linux_desktop_file(install_path)
	elif platform == 'windows':
		create_windows_launcher(install_path)


def get_platform() -> str:
	if sys.platform.startswith('linux'):
		return 'linux'
	elif sys.platform.startswith('win'):
		return 'windows'
	return 'unknown'


def create_linux_desktop_file(install_path : str) -> None:
	desktop_file = f"""[Desktop Entry]
Name=FaceFusion
Comment=Next generation face swapper and enhancer
Exec={sys.executable} {os.path.join(install_path, 'launch.py')}
Icon={os.path.join(install_path, 'facefusion.ico')}
Terminal=true
Type=Application
Categories=Graphics;Video;
"""
	desktop_path = os.path.expanduser('~/.local/share/applications/facefusion.desktop')
	os.makedirs(os.path.dirname(desktop_path), exist_ok=True)

	with open(desktop_path, 'w') as f:
		f.write(desktop_file)

	print(f"Created Linux desktop entry at: {desktop_path}")
	print("You may need to log out and back in or run 'update-desktop-database' for it to appear.")


def create_windows_launcher(install_path : str) -> None:
	bat_content = f"""@echo off
cd /d "{install_path}"
"{sys.executable}" launch.py
pause
"""
	bat_path = os.path.join(install_path, 'run.bat')
	with open(bat_path, 'w') as f:
		f.write(bat_content)

	print(f"Created Windows batch launcher at: {bat_path}")
	print("You can right-click 'run.bat' and 'Send to Desktop (create shortcut)'")


def create_user_config(install_path : str) -> None:
	user_config_path = os.path.join(install_path, 'user.ini')
	if os.path.exists(user_config_path):
		return

	documents_path = os.path.expanduser('~/Documents')
	if sys.platform.startswith('win'):
		import ctypes.wintypes
		CSIDL_PERSONAL = 5       # My Documents
		SHGFP_TYPE_CURRENT = 0   # Get current, not default value
		buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
		ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
		documents_path = buf.value

	facefusion_docs = os.path.join(documents_path, 'FaceFusion')
	output_path = os.path.join(facefusion_docs, 'Output')

	config_content = f"""[paths]
output_path = {output_path}

[uis]
# ui_theme = ocean
"""
	with open(user_config_path, 'w') as f:
		f.write(config_content)
	
	print(f"Created standard user.ini at: {user_config_path}")
