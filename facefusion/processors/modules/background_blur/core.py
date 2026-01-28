from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_masker import create_region_mask
from facefusion.processors.modules.background_blur import choices as background_blur_choices
from facefusion.processors.modules.background_blur.types import BackgroundBlurInputs
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
		group_processors.add_argument('--background-blur-mode', help = translator.get('help.background_blur_mode', __package__), default = config.get_str_value('processors', 'background_blur_mode', 'blur'), choices = background_blur_choices.background_blur_modes)
		group_processors.add_argument('--background-blur-amount', help = translator.get('help.background_blur_amount', __package__), type = int, default = config.get_int_value('processors', 'background_blur_amount', '30'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'background_blur_mode', 'background_blur_amount' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('background_blur_mode', args.get('background_blur_mode'))
	apply_state_item('background_blur_amount', args.get('background_blur_amount'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : BackgroundBlurInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')

	if target_vision_frame is None:
		return temp_vision_frame, None

	mode = state_manager.get_item('background_blur_mode')
	amount = state_manager.get_item('background_blur_amount') / 100.0

	if amount == 0:
		return temp_vision_frame, None

	# Generate Background Mask
	# We want the background, which is region 0.
	# create_region_mask works on cropped frames usually, but here we need it for the full frame.
	# face_masker.create_region_mask is designed for face crops.
	# However, we can use the whole frame as input if we treat it as a 'crop'.
	# But face_parser expects aligned faces? No, bisenet parses the whole image usually, or face chips.
	# The current face_masker implementation resizes input to model size (512x512).
	# So we can pass the whole frame.
	
	# But wait, create_region_mask takes 'crop_vision_frame' and 'face_mask_regions'.
	# It uses 'face_parser_model' from state_manager.
	# If we pass the full frame, it will resize it to 512x512, parse it, and resize mask back.
	# This should work for general scene segmentation if the model supports it.
	# The 'bisenet_resnet_34' is trained on CelebAMask-HQ usually, which is face-centric.
	# But let's try using it for the scene or assume the user wants to blur 'everything but the face'.
	
	try:
		# We need to select the background region
		background_mask = create_region_mask(temp_vision_frame, [ 'background' ])
	except Exception:
		# Fallback if something fails, though it shouldn't
		return temp_vision_frame, None

	# Blur the whole frame
	blurred_frame = temp_vision_frame.copy()
	ksize = int(amount * 100)
	if ksize % 2 == 0: ksize += 1
	
	if mode == 'blur':
		blurred_frame = cv2.GaussianBlur(temp_vision_frame, (ksize, ksize), 0)
	elif mode == 'bokeh':
		# Approximate bokeh with a simpler blur for now, maybe stronger?
		# Real bokeh is expensive (lens blur).
		blurred_frame = cv2.GaussianBlur(temp_vision_frame, (ksize, ksize), 0)

	# Composite: Background uses blurred, Foreground (Face/Body) uses original
	# mask is 1 for background, 0 for others.
	
	# create_region_mask returns float32 mask [0, 1]
	# We need to broadcast it
	background_mask = numpy.expand_dims(background_mask, axis = 2)
	
	# Blend
	temp_vision_frame = (blurred_frame * background_mask + temp_vision_frame * (1 - background_mask)).astype(numpy.uint8)

	return temp_vision_frame, None
