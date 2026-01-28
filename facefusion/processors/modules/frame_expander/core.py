from argparse import ArgumentParser
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, logger, state_manager, translator
from facefusion.common_helper import create_int_metavar
from facefusion.filesystem import in_directory, is_image, is_video, same_file_extension
from facefusion.processors.modules.frame_expander import choices as frame_expander_choices
from facefusion.processors.modules.frame_expander.types import FrameExpanderInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, ProcessMode, VisionFrame

def get_process_mode(mode : ProcessMode) -> int:
	if mode == 'output':
		return 1
	if mode == 'preview':
		return 2
	if mode == 'stream':
		return 3
	return 0


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--frame-expander-target-ratio', help = translator.get('help.frame_expander_target_ratio', __package__), default = config.get_str_value('processors', 'frame_expander_target_ratio', '16:9'), choices = frame_expander_choices.frame_expander_target_ratios)
		group_processors.add_argument('--frame-expander-mode', help = translator.get('help.frame_expander_mode', __package__), default = config.get_str_value('processors', 'frame_expander_mode', 'span'), choices = frame_expander_choices.frame_expander_modes)
		group_processors.add_argument('--frame-expander-blur', help = translator.get('help.frame_expander_blur', __package__), type = int, default = config.get_int_value('processors', 'frame_expander_blur', '50'), choices = frame_expander_choices.frame_expander_blur_range, metavar = create_int_metavar(frame_expander_choices.frame_expander_blur_range))
		facefusion.jobs.job_store.register_step_keys([ 'frame_expander_target_ratio', 'frame_expander_mode', 'frame_expander_blur' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('frame_expander_target_ratio', args.get('frame_expander_target_ratio'))
	apply_state_item('frame_expander_mode', args.get('frame_expander_mode'))
	apply_state_item('frame_expander_blur', args.get('frame_expander_blur'))


def pre_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(translator.get('choose_image_or_video_target') + translator.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(translator.get('specify_image_or_video_output') + translator.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
		logger.error(translator.get('match_target_and_output_extension') + translator.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	return


def get_inference_pool() -> None:
	return None


def clear_inference_pool() -> None:
	return None


def calculate_target_resolution(source_resolution : Tuple[int, int], target_ratio : str) -> Tuple[int, int]:
	source_width, source_height = source_resolution
	if target_ratio == '16:9':
		target_width = int(source_height * 16 / 9)
		target_height = source_height
	elif target_ratio == '21:9':
		target_width = int(source_height * 21 / 9)
		target_height = source_height
	elif target_ratio == '4:3':
		target_width = int(source_height * 4 / 3)
		target_height = source_height
	elif target_ratio == '1:1':
		target_width = source_height
		target_height = source_height
	elif target_ratio == '9:16':
		target_width = int(source_height * 9 / 16)
		target_height = source_height
	else:
		return source_resolution
	
	# If source is wider than target, we need to pad height instead
	if source_width > target_width:
		# Recalculate based on width
		if target_ratio == '16:9':
			target_height = int(source_width * 9 / 16)
			target_width = source_width
		elif target_ratio == '21:9':
			target_height = int(source_width * 9 / 21)
			target_width = source_width
		elif target_ratio == '4:3':
			target_height = int(source_width * 3 / 4)
			target_width = source_width
		elif target_ratio == '1:1':
			target_height = source_width
			target_width = source_width
		elif target_ratio == '9:16':
			target_height = int(source_width * 16 / 9)
			target_width = source_width

	return target_width, target_height


def expand_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	frame_expander_target_ratio = state_manager.get_item('frame_expander_target_ratio')
	frame_expander_mode = state_manager.get_item('frame_expander_mode')
	frame_expander_blur = state_manager.get_item('frame_expander_blur')

	source_height, source_width = temp_vision_frame.shape[:2]
	target_width, target_height = calculate_target_resolution((source_width, source_height), frame_expander_target_ratio)
	
	if target_width == source_width and target_height == source_height:
		return temp_vision_frame

	pad_left = (target_width - source_width) // 2
	pad_right = target_width - source_width - pad_left
	pad_top = (target_height - source_height) // 2
	pad_bottom = target_height - source_height - pad_top

	if frame_expander_mode == 'span':
		# Create background by resizing source to cover target
		scale_w = target_width / source_width
		scale_h = target_height / source_height
		scale = max(scale_w, scale_h)
		
		bg_width = int(source_width * scale)
		bg_height = int(source_height * scale)
		
		background = cv2.resize(temp_vision_frame, (bg_width, bg_height), interpolation=cv2.INTER_LINEAR)
		
		# Center crop the background
		crop_x = (bg_width - target_width) // 2
		crop_y = (bg_height - target_height) // 2
		background = background[crop_y:crop_y+target_height, crop_x:crop_x+target_width]
		
		# Blur background
		if frame_expander_blur > 0:
			kernel_size = (frame_expander_blur * 2) + 1
			background = cv2.GaussianBlur(background, (kernel_size, kernel_size), 0)
			
		# Overlay source
		background[pad_top:pad_top+source_height, pad_left:pad_left+source_width] = temp_vision_frame
		return background

	elif frame_expander_mode == 'mirror':
		return cv2.copyMakeBorder(temp_vision_frame, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REFLECT_101)
	
	elif frame_expander_mode == 'reflect':
		return cv2.copyMakeBorder(temp_vision_frame, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REFLECT)
	
	elif frame_expander_mode == 'black':
		return cv2.copyMakeBorder(temp_vision_frame, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
		
	elif frame_expander_mode == 'white':
		return cv2.copyMakeBorder(temp_vision_frame, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[255, 255, 255])

	return temp_vision_frame


def process_frame(inputs : FrameExpanderInputs) -> ProcessorOutputs:
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	expanded_frame = expand_frame(temp_vision_frame)
	
	# Resize mask to match new dimensions
	# If the mask is smaller, we pad it with 0 (no mask)
	source_height, source_width = temp_vision_frame.shape[:2]
	target_height, target_width = expanded_frame.shape[:2]
	
	pad_left = (target_width - source_width) // 2
	pad_right = target_width - source_width - pad_left
	pad_top = (target_height - source_height) // 2
	pad_bottom = target_height - source_height - pad_top
	
	expanded_mask = cv2.copyMakeBorder(temp_vision_mask, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=0)

	return expanded_frame, expanded_mask
