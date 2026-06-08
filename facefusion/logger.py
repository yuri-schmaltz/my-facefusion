import os
import sys
import json
import datetime
from logging import Logger, basicConfig, getLogger, FileHandler, Formatter, StreamHandler
from contextvars import ContextVar

import facefusion.choices
from facefusion.common_helper import get_first, get_last
from facefusion.types import LogLevel
from facefusion.filesystem import get_default_path

# Context variables for logging correlation (job and session IDs)
log_job_id: ContextVar[str] = ContextVar('log_job_id', default='')
log_session_id: ContextVar[str] = ContextVar('log_session_id', default='')

_LOGGER_INITIALIZED = False


class JSONFormatter(Formatter):
	def format(self, record):
		log_entry = {
			"timestamp": datetime.datetime.utcnow().isoformat() + "Z",
			"level": record.levelname,
			"logger": record.name,
			"message": record.getMessage(),
			"job_id": log_job_id.get(),
			"session_id": log_session_id.get()
		}
		return json.dumps(log_entry)


class ClassicFormatter(Formatter):
	def format(self, record):
		return record.getMessage()


def init(log_level : LogLevel) -> None:
	global _LOGGER_INITIALIZED
	if _LOGGER_INITIALIZED:
		# Allow re-setting the logging level
		get_package_logger().setLevel(facefusion.choices.log_level_set.get(log_level))
		return

	logger = get_package_logger()
	logger.setLevel(facefusion.choices.log_level_set.get(log_level))
	logger.handlers.clear()

	# 1. Console Handler (paridade com CLI / JSON opcional)
	console_handler = StreamHandler(sys.stdout)
	if os.environ.get('FACEFUSION_LOG_FORMAT', '').lower() == 'json':
		console_handler.setFormatter(JSONFormatter())
	else:
		console_handler.setFormatter(ClassicFormatter())
	logger.addHandler(console_handler)

	# 2. File Handler (gravação de log estruturado local conforme SO)
	try:
		cache_dir = get_default_path('cache')
		os.makedirs(cache_dir, exist_ok=True)
		log_file = os.path.join(cache_dir, 'facefusion.log')
		file_handler = FileHandler(log_file, encoding='utf-8')
		file_handler.setFormatter(JSONFormatter())
		logger.addHandler(file_handler)
	except Exception:
		pass

	_LOGGER_INITIALIZED = True


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


def set_job_context(job_id: str) -> None:
	log_job_id.set(job_id)


def set_session_context(session_id: str) -> None:
	log_session_id.set(session_id)

