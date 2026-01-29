from typing import Any

from facefusion import state_manager
from facefusion.filesystem import get_file_name, is_video, resolve_file_paths
from facefusion.jobs import job_store
from facefusion.normalizer import normalize_fps, normalize_space
from facefusion.processors.core import get_processors_modules
from facefusion.types import ApplyStateItem, Args
from facefusion.vision import detect_video_fps


def reduce_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args[key] for key in args if key in job_store.get_step_keys()
	}
	return step_args


def reduce_job_args(args : Args) -> Args:
	job_args =\
	{
		key: args[key] for key in args if key in job_store.get_job_keys()
	}
	return job_args


def collect_step_args() -> Args:
	step_args =\
	{
		key: state_manager.get_item(key) for key in job_store.get_step_keys() #type:ignore[arg-type]
	}
	return step_args


def collect_job_args() -> Args:
	job_args =\
	{
		key: state_manager.get_item(key) for key in job_store.get_job_keys() #type:ignore[arg-type]
	}
	return job_args


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	def apply_if_present(key : str, value : Any) -> None:
		if key in args:
			apply_state_item(key, value)

	# general
	apply_if_present('command', args.get('command'))
	# paths
	apply_if_present('temp_path', args.get('temp_path'))
	apply_if_present('jobs_path', args.get('jobs_path'))
	apply_if_present('source_paths', args.get('source_paths'))
	apply_if_present('target_path', args.get('target_path'))
	apply_if_present('output_path', args.get('output_path'))
	# patterns
	apply_if_present('source_pattern', args.get('source_pattern'))
	apply_if_present('target_pattern', args.get('target_pattern'))
	apply_if_present('output_pattern', args.get('output_pattern'))
	# face detector
	apply_if_present('face_detector_model', args.get('face_detector_model'))
	apply_if_present('face_detector_size', args.get('face_detector_size'))
	apply_if_present('face_detector_margin', normalize_space(args.get('face_detector_margin')) if 'face_detector_margin' in args else None)
	apply_if_present('face_detector_angles', args.get('face_detector_angles'))
	apply_if_present('face_detector_score', args.get('face_detector_score'))
	# face landmarker
	apply_if_present('face_landmarker_model', args.get('face_landmarker_model'))
	apply_if_present('face_landmarker_score', args.get('face_landmarker_score'))
	# face selector
	apply_if_present('face_selector_mode', args.get('face_selector_mode'))
	apply_if_present('face_selector_order', args.get('face_selector_order'))
	apply_if_present('face_selector_age_start', args.get('face_selector_age_start'))
	apply_if_present('face_selector_age_end', args.get('face_selector_age_end'))
	apply_if_present('face_selector_gender', args.get('face_selector_gender'))
	apply_if_present('face_selector_race', args.get('face_selector_race'))
	apply_if_present('reference_face_position', args.get('reference_face_position'))
	apply_if_present('reference_face_distance', args.get('reference_face_distance'))
	apply_if_present('reference_frame_number', args.get('reference_frame_number'))
	# face masker
	apply_if_present('face_occluder_model', args.get('face_occluder_model'))
	apply_if_present('face_parser_model', args.get('face_parser_model'))
	apply_if_present('face_mask_types', args.get('face_mask_types'))
	apply_if_present('face_mask_areas', args.get('face_mask_areas'))
	apply_if_present('face_mask_regions', args.get('face_mask_regions'))
	apply_if_present('face_mask_blur', args.get('face_mask_blur'))
	apply_if_present('face_mask_padding', normalize_space(args.get('face_mask_padding')) if 'face_mask_padding' in args else None)
	# voice extractor
	apply_if_present('voice_extractor_model', args.get('voice_extractor_model'))
	# frame extraction
	apply_if_present('trim_frame_start', args.get('trim_frame_start'))
	apply_if_present('trim_frame_end', args.get('trim_frame_end'))
	apply_if_present('temp_frame_format', args.get('temp_frame_format'))
	apply_if_present('keep_temp', args.get('keep_temp'))
	# output creation
	apply_if_present('output_image_quality', args.get('output_image_quality'))
	apply_if_present('output_image_scale', args.get('output_image_scale'))
	apply_if_present('output_audio_encoder', args.get('output_audio_encoder'))
	apply_if_present('output_audio_quality', args.get('output_audio_quality'))
	apply_if_present('output_audio_volume', args.get('output_audio_volume'))
	apply_if_present('output_video_encoder', args.get('output_video_encoder'))
	apply_if_present('output_video_preset', args.get('output_video_preset'))
	apply_if_present('output_video_quality', args.get('output_video_quality'))
	apply_if_present('output_video_scale', args.get('output_video_scale'))
	
	if args.get('output_video_fps') or is_video(args.get('target_path')):
		output_video_fps = normalize_fps(args.get('output_video_fps')) or detect_video_fps(args.get('target_path'))
		apply_if_present('output_video_fps', output_video_fps)
	
	# processors
	available_processors = [ get_file_name(file_path) for file_path in resolve_file_paths('facefusion/processors/modules') ]
	apply_if_present('processors', args.get('processors'))
	for processor_module in get_processors_modules(available_processors):
		processor_module.apply_args(args, apply_state_item)
	
	# uis
	apply_if_present('open_browser', args.get('open_browser'))
	apply_if_present('ui_layouts', args.get('ui_layouts'))
	apply_if_present('ui_workflow', args.get('ui_workflow'))
	apply_if_present('ui_theme', args.get('ui_theme'))
	# execution
	apply_if_present('execution_device_ids', args.get('execution_device_ids'))
	apply_if_present('execution_providers', args.get('execution_providers'))
	apply_if_present('execution_thread_count', args.get('execution_thread_count'))
	# download
	apply_if_present('download_providers', args.get('download_providers'))
	apply_if_present('download_scope', args.get('download_scope'))
	# benchmark
	apply_if_present('benchmark_mode', args.get('benchmark_mode'))
	apply_if_present('benchmark_resolutions', args.get('benchmark_resolutions'))
	apply_if_present('benchmark_cycle_count', args.get('benchmark_cycle_count'))
	# memory
	apply_if_present('video_memory_strategy', args.get('video_memory_strategy'))
	apply_if_present('system_memory_limit', args.get('system_memory_limit'))
	# misc
	apply_if_present('log_level', args.get('log_level'))
	apply_if_present('halt_on_error', args.get('halt_on_error'))
	# jobs
	apply_if_present('job_id', args.get('job_id'))
	apply_if_present('job_status', args.get('job_status'))
	apply_if_present('step_index', args.get('step_index'))
