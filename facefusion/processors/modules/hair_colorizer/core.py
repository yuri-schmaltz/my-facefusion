from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_masker import create_region_mask
from facefusion.processors.modules.hair_colorizer import choices as hair_colorizer_choices
from facefusion.processors.modules.hair_colorizer.types import HairColorizerInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, InferencePool, VisionFrame


def get_inference_pool() -> InferencePool:
	return None


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--hair-colorizer-type', help = translator.get('help.hair_colorizer_type', __package__), default = config.get_str_value('processors', 'hair_colorizer_type', 'shift'), choices = hair_colorizer_choices.hair_colorizer_types)
		group_processors.add_argument('--hair-colorizer-blend', help = translator.get('help.hair_colorizer_blend', __package__), type = int, default = config.get_int_value('processors', 'hair_colorizer_blend', '50'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'hair_colorizer_type', 'hair_colorizer_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('hair_colorizer_type', args.get('hair_colorizer_type'))
	apply_state_item('hair_colorizer_blend', args.get('hair_colorizer_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : HairColorizerInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')
	
	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask

	type = state_manager.get_item('hair_colorizer_type')
	blend = state_manager.get_item('hair_colorizer_blend') / 100.0

	if blend == 0:
		return temp_vision_frame, temp_vision_mask

	try:
		# Use 'hair' region
		hair_mask = create_region_mask(temp_vision_frame, [ 'hair' ])
	except Exception:
		return temp_vision_frame, temp_vision_mask

	hair_mask = numpy.expand_dims(hair_mask, axis = 2)

	if type == 'shift':
		# Hue Shift
		hsv = cv2.cvtColor(temp_vision_frame, cv2.COLOR_BGR2HSV)
		h, s, v = cv2.split(hsv)
		
		# Shift hue by blend amount (mapped to 180 degrees)
		shift = int(blend * 50) # Moderate shift
		h = (h + shift) % 180
		
		# Boost saturation slightly
		s = cv2.add(s, 20)
		
		hsv_new = cv2.merge([h, s, v])
		colored_frame = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)
		
	elif type == 'recolor':
		# Apply a fixed tint (e.g., Blonde/Brown) - simplified for now
		# Let's make it sepia-ish/blonde for demo
		colored_frame = cv2.applyColorMap(temp_vision_frame, cv2.COLORMAP_PINK)
		# Blend with original luminosity to keep details
		# (Simplified for keeping it fast)

	# Composite
	temp_vision_frame = (colored_frame * hair_mask * blend + temp_vision_frame * (1 - (hair_mask * blend))).astype(numpy.uint8)

	return temp_vision_frame, temp_vision_mask
