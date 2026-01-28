from argparse import ArgumentParser, _ArgumentGroup, _SubParsersAction
from typing import Optional, Any

from facefusion.common_helper import get_first
from facefusion.filesystem import is_directory, is_file


def find_argument_group(program : ArgumentParser, group_name : str) -> Optional[_ArgumentGroup]:
	for group in program._action_groups:
		if group.title == group_name:
			return group
	return None


def validate_args(program : ArgumentParser) -> bool:
	if validate_actions(program):
		for action in program._actions:
			if isinstance(action, _SubParsersAction):
				for name, sub_program in action._name_parser_map.items():
					if not validate_args(sub_program):
						return False
		return True
	return False


def validate_actions(program : ArgumentParser) -> bool:
	for action in program._actions:
		if action.default and action.choices:
			if isinstance(action.default, list):
				if any(default not in action.choices for default in action.default):
					action.default = [ default for default in action.default if default in action.choices ]
					if not action.default:
						action.default = [ get_first(action.choices) ]
			elif action.default not in action.choices:
				action.default = get_first(action.choices)
	return True


def validate_paths(args : Any) -> bool:
	if hasattr(args, 'config_path') and args.config_path and not is_file(args.config_path):
		return False
	if hasattr(args, 'jobs_path') and args.jobs_path and not is_directory(args.jobs_path):
		return False
	if hasattr(args, 'source_paths') and args.source_paths:
		if isinstance(args.source_paths, list):
			for source_path in args.source_paths:
				if not is_file(source_path):
					return False
	if hasattr(args, 'target_path') and args.target_path and not is_file(args.target_path):
		return False
	return True
