import json
from json import JSONDecodeError
from typing import Optional

from facefusion.filesystem import is_file
from facefusion.types import Content


def read_json(json_path : str) -> Optional[Content]:
	if is_file(json_path):
		try:
			with open(json_path) as json_file:
				return json.load(json_file)
		except JSONDecodeError:
			pass
	return None


def write_json(json_path : str, content : Content) -> bool:
	import tempfile
	import os

	directory = os.path.dirname(json_path) or '.'
	try:
		with tempfile.NamedTemporaryFile('w', dir=directory, delete=False, encoding='utf-8') as temp_file:
			json.dump(content, temp_file, indent=4)
			temp_file_path = temp_file.name
		
		# Substituição atômica no mesmo sistema de arquivos
		os.replace(temp_file_path, json_path)
		return is_file(json_path)
	except Exception:
		# Fallback seguro para escrita direta caso haja restrição de caminhos
		try:
			with open(json_path, 'w', encoding='utf-8') as json_file:
				json.dump(content, json_file, indent=4)
			return is_file(json_path)
		except Exception:
			return False
