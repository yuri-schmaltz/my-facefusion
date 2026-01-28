from argparse import ArgumentParser
import numpy
import cv2

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.processors.modules.grain_matcher import choices as grain_matcher_choices
from facefusion.processors.modules.grain_matcher.types import GrainMatcherInputs
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
		group_processors.add_argument('--grain-matcher-blend', help = translator.get('help.grain_matcher_blend', __package__), type = int, default = config.get_int_value('processors', 'grain_matcher_blend', '100'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'grain_matcher_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('grain_matcher_blend', args.get('grain_matcher_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : GrainMatcherInputs) -> ProcessorOutputs:
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask
	
	blend = state_manager.get_item('grain_matcher_blend') / 100.0
	
	if blend > 0:
		temp_vision_frame = apply_grain(target_vision_frame, temp_vision_frame, blend)

	return temp_vision_frame, temp_vision_mask


def apply_grain(target_frame, temp_frame, blend):
	# Estimate noise from target frame
	# Convert to gray for estimation
	gray = cv2.cvtColor(target_frame, cv2.COLOR_BGR2GRAY)
	
	# Compute standard deviation of Laplacian to estimate noise level
	# This is a heuristic
	sigma = estimate_noise(gray)
	
	if sigma < 1: # Very clean image, no need to add noise
		return temp_frame

	# Generate noise
	row, col, ch = temp_frame.shape
	mean = 0
	# Adjust sigma for generation
	noise_sigma = sigma * 0.5 # Tuning factor
	gauss = numpy.random.normal(mean, noise_sigma, (row, col, ch))
	gauss = gauss.reshape(row, col, ch)
	
	# Add noise
	noisy = temp_frame.astype(numpy.float32) + gauss
	noisy = numpy.clip(noisy, 0, 255).astype(numpy.uint8)
	
	# Blend
	return cv2.addWeighted(noisy, blend, temp_frame, 1 - blend, 0)


def estimate_noise(image):
	# Compute the standard deviation of the Laplacian
	# A simple measure of "graininess" or texture
	h, w = image.shape
	# Crop center to avoid border artifacts
	crop = image[int(h/4):int(h*3/4), int(w/4):int(w*3/4)]
	if crop.size == 0:
		crop = image
		
	laplacian = cv2.Laplacian(crop, cv2.CV_64F)
	score, mu, sigma = 0, 0, 0
	
	# Variance of Laplacian
	# Higher variance = sharper/graphier OR noisier
	# It's hard to distinguish texture from noise without complex logic
	# But for "matching", if the source is grainy, we want result grainy.
	
	sigma = numpy.std(laplacian)
	return sigma
