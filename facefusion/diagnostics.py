import platform
import sys
import os
import shutil
import json
from datetime import datetime
from typing import Dict, Any

from facefusion import metadata, logger

def collect_environment_info() -> Dict[str, Any]:
	info = \
	{
		'timestamp': datetime.now().isoformat(),
		'facefusion_version': metadata.get('version'),
		'python_version': sys.version,
		'os': platform.system(),
		'os_release': platform.release(),
		'os_version': platform.version(),
		'architecture': platform.machine(),
		'processor': platform.processor(),
		'executable': sys.executable,
		'working_directory': os.getcwd()
	}
	
	try:
		import torch
		info['torch_version'] = torch.__version__
		info['cuda_available'] = torch.cuda.is_available()
		if info['cuda_available']:
			info['cuda_version'] = torch.version.cuda
			info['gpu_name'] = torch.cuda.get_device_name(0)
	except ImportError:
		info['torch_available'] = False

	try:
		import onnxruntime
		info['onnxruntime_version'] = onnxruntime.__version__
		info['onnxruntime_providers'] = onnxruntime.get_available_providers()
	except ImportError:
		info['onnxruntime_available'] = False

	info['ffmpeg_available'] = shutil.which('ffmpeg') is not None
	return info

def collect_orchestrator_info() -> Dict[str, Any]:
	try:
		from facefusion.orchestrator import get_orchestrator, JobStatus
		orch = get_orchestrator()
		
		# Basic stats
		jobs = orch.list_jobs()
		stats = {
			'total_jobs': len(jobs),
			'by_status': {}
		}
		
		for status in JobStatus:
			count = len([j for j in jobs if j.status == status])
			stats['by_status'][status.value] = count
			
		return stats
	except Exception as e:
		return {'error': str(e)}

def create_bundle(target_path : str = None) -> bool:
	if not target_path:
		target_path = 'facefusion_diagnostics.json'
	try:
		logger.info(f'Creating diagnostic bundle: {target_path}', __name__)
		data = \
		{
			'environment': collect_environment_info(),
			'logs': [],
			'orchestrator': collect_orchestrator_info()
		}
		
		# Collect last 50 lines of logs if they exist
		for log_file in ['facefusion.log', 'facefusion.json']:
			if os.path.exists(log_file):
				with open(log_file, 'r') as f:
					data['logs'].append({
						'filename': log_file,
						'content': f.readlines()[-50:]
					})
		
		with open(target_path, 'w') as f:
			json.dump(data, f, indent = 4)
		
		logger.info(f'Diagnostic bundle created successfully at {target_path}', __name__)
		return True
	except Exception as e:
		logger.error(f'Failed to create diagnostic bundle: {str(e)}', __name__)
		return False
