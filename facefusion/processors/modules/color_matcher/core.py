from argparse import ArgumentParser
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, face_detector, state_manager, translator
from facefusion.common_helper import get_first
from facefusion.face_analyser import get_many_faces
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_area_mask, create_box_mask, create_occlusion_mask, create_region_mask
from facefusion.face_selector import select_faces, sort_faces_by_order
from facefusion.processors.modules.color_matcher import choices as color_matcher_choices
from facefusion.processors.modules.color_matcher.types import ColorMatcherInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, Face, InferencePool, VisionFrame
from facefusion.vision import unpack_resolution


def get_inference_pool() -> InferencePool:
	return None


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--color-matcher-type', help = translator.get('help.color_matcher_type', __package__), default = config.get_str_value('processors', 'color_matcher_type', 'mean-std'), choices = color_matcher_choices.color_matcher_types)
		group_processors.add_argument('--color-matcher-blend', help = translator.get('help.color_matcher_blend', __package__), type = int, default = config.get_int_value('processors', 'color_matcher_blend', '100'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'color_matcher_type', 'color_matcher_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('color_matcher_type', args.get('color_matcher_type'))
	apply_state_item('color_matcher_blend', args.get('color_matcher_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : ColorMatcherInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	# To save performance, we only process if there is a detected face in the TEMP frame (the result so far)
	# AND we have the original reference frame to steal colors from.
	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask
	
	target_faces = select_faces(reference_vision_frame, target_vision_frame)
	
	if target_faces:
		# Detect faces in the ALREADY SWAPPED frame to apply color matching
		# Ideally we use the same landmarks as the target_face but re-extracted from temp_frame
		# But since temp_frame is swapped, we should use the landmarks from target_faces (which are from reference)
		# and just re-warp the content from temp_vision_frame.
		
		for target_face in target_faces:
			# match colors
			temp_vision_frame = match_color(target_face, target_vision_frame, temp_vision_frame)

	return temp_vision_frame, temp_vision_mask


def match_color(target_face: Face, target_vision_frame: VisionFrame, temp_vision_frame: VisionFrame) -> VisionFrame:
	model_template = 'arcface_112_v2' 
	model_size = (256, 256)
	
	# 1. Warp the ORIGINAL target face (Reference Color)
	crop_target_frame, affine_matrix = warp_face_by_face_landmark_5(target_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	
	# 2. Warp the CURRENT temp face (Source to Colorize) using the SAME landmarks 
	# (Assuming no major geometric shift, or using target landmarks is close enough as swap keeps shape)
	crop_temp_frame, _ = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)

	# 3. Apply Color Transfer
	color_matcher_type = state_manager.get_item('color_matcher_type')
	color_matcher_blend = state_manager.get_item('color_matcher_blend') / 100.0

	crop_matched_frame = crop_temp_frame.copy()

	if color_matcher_type == 'mean-std':
		crop_matched_frame = apply_mean_std_transfer(crop_temp_frame, crop_target_frame)
	
	# Blend result
	if color_matcher_blend < 1.0:
		crop_matched_frame = cv2.addWeighted(crop_matched_frame, color_matcher_blend, crop_temp_frame, 1 - color_matcher_blend, 0)
	
	# 4. Create Mask for Paste Back
	crop_mask = create_box_mask(crop_matched_frame, 0.3, (0, 0, 0, 0)).clip(0, 1) # simple box mask for now

	# 5. Paste Back
	matched_vision_frame = paste_back(temp_vision_frame, crop_matched_frame, crop_mask, affine_matrix)
	return matched_vision_frame


def apply_mean_std_transfer(source_img, reference_img):
	s_mean, s_std = cv2.meanStdDev(source_img)
	r_mean, r_std = cv2.meanStdDev(reference_img)

	s_mean = numpy.hstack(s_mean)
	s_std = numpy.hstack(s_std)
	r_mean = numpy.hstack(r_mean)
	r_std = numpy.hstack(r_std)

	height, width, channel = source_img.shape
	result_img = source_img.astype(numpy.float32)

	for k in range(3):
		result_img[:, :, k] = (result_img[:, :, k] - s_mean[k]) * (r_std[k] / (s_std[k] + 1e-6)) + r_mean[k]

	result_img = numpy.clip(result_img, 0, 255).astype(numpy.uint8)
	return result_img
