import json
from logging import FileHandler, Formatter, Logger, basicConfig, getLogger, StreamHandler

import facefusion.choices
from facefusion.common_helper import get_first, get_last
from facefusion.types import LogLevel


class JsonFormatter(Formatter):
	def format(self, record):
		data = \
		{
			'asctime': self.formatTime(record),
			'name': record.name,
			'levelname': record.levelname,
			'message': record.getMessage(),
			'module': record.module,
			'lineno': record.lineno
		}
		return json.dumps(data)


def init(log_level : LogLevel) -> None:
	get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))
	if not get_package_logger().handlers:
		# console handler
		console_handler = StreamHandler()
		console_handler.setFormatter(Formatter('%(message)s'))
		get_package_logger().addHandler(console_handler)
		# file handler (txt)
		file_handler = FileHandler('facefusion.log')
		file_handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
		get_package_logger().addHandler(file_handler)
		# structured handler (json)
		structured_handler = FileHandler('facefusion.json')
		structured_handler.setFormatter(JsonFormatter())
		get_package_logger().addHandler(structured_handler)


def get_package_logger() -> Logger:
	return getLogger('facefusion')


def debug(message : str, module_name : str) -> None:
	get_package_logger().debug(create_message(message, module_name))


def info(message : str, module_name : str) -> None:
	get_package_logger().info(create_message(message, module_name))


def warn(message : str, module_name : str) -> None:
	get_package_logger().warning(create_message(message, module_name))


def error(message : str, module_name : str) -> None:
	get_package_logger().error(create_message(message, module_name))


def create_message(message : str, module_name : str) -> str:
	module_names = module_name.split('.')
	first_module_name = get_first(module_names)
	last_module_name = get_last(module_names)

	if first_module_name and last_module_name:
		return '[' + first_module_name.upper() + '.' + last_module_name.upper() + '] ' + message
	return message


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True
