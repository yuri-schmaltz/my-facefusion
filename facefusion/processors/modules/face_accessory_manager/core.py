from argparse import ArgumentParser
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_occlusion_mask, create_box_mask
from facefusion.face_selector import select_faces
from facefusion.processors.modules.face_accessory_manager import choices as face_accessory_manager_choices
from facefusion.processors.modules.face_accessory_manager.types import FaceAccessoryManagerInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, InferencePool, VisionFrame
from facefusion.vision import unpack_resolution


def get_inference_pool() -> InferencePool:
	return None


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-accessory-manager-mode', help = translator.get('help.face_accessory_manager_mode', __package__), default = config.get_str_value('processors', 'face_accessory_manager_mode', 'replicate'), choices = face_accessory_manager_choices.face_accessory_manager_modes)
		group_processors.add_argument('--face-accessory-manager-blend', help = translator.get('help.face_accessory_manager_blend', __package__), type = int, default = config.get_int_value('processors', 'face_accessory_manager_blend', '100'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'face_accessory_manager_mode', 'face_accessory_manager_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_accessory_manager_mode', args.get('face_accessory_manager_mode'))
	apply_state_item('face_accessory_manager_blend', args.get('face_accessory_manager_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : FaceAccessoryManagerInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask
	
	mode = state_manager.get_item('face_accessory_manager_mode') or 'replicate'
	blend = (state_manager.get_item('face_accessory_manager_blend') if state_manager.get_item('face_accessory_manager_blend') is not None else 100) / 100.0

	target_faces = select_faces(reference_vision_frame, target_vision_frame)

	if target_faces:
		for target_face in target_faces:
			# If mode is 'replicate', we want to identifying occlusions in the REFERENCE
			# and bring them back onto the RESULT (temp_vision_frame)
			if mode == 'replicate':
				temp_vision_frame = replicate_accessories(target_face, target_vision_frame, temp_vision_frame, blend)
			
			# If mode is 'remove', we ideally want to inpaint. 
			# Without a complex inpainter, 'remove' might currently just mean ensure the mask
			# did NOT include them, but since this runs POST-processor, we can't undo what face_swapper did.
			# So for MVP 'remove' only works if we implement a blurring/inpainting step.
			# We'll skip implementation of 'remove' logic for this specific file iteration unless requested,
			# as it requires heavier dependencies.

	return temp_vision_frame, temp_vision_mask


def replicate_accessories(target_face, target_vision_frame, temp_vision_frame, blend):
	model_template = 'arcface_112_v2'
	model_size = (256, 256)

	# 1. Warp REFERENCE face to get clean view for masking
	crop_target_frame, affine_matrix = warp_face_by_face_landmark_5(target_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)

	# 2. Creates occlusion mask from the REFERENCE crop.
	# This mask highlights things blocking the face (glasses, hands, hair).
	occlusion_mask = create_occlusion_mask(crop_target_frame)

	# 3. Use occlusion mask to blend TARGET pixels back over TEMP pixels
	# Effectively "un-swapping" the accessories.
	
	# We want to paste 'crop_target_frame' (original) onto 'temp_vision_frame' (swapped)
	# BUT only where occlusion_mask is high.
	
	# Prepare the crop_mask for paste_back function
	# paste_back takes (temp_frame, crop_vision_frame, crop_mask, affine_matrix)
	# It pastes 'crop_vision_frame' onto 'temp_frame' using 'crop_mask'.
	
	# So we pass 'crop_target_frame' as the content to paste, and 'occlusion_mask' as the alpha.
	if blend < 1.0:
		occlusion_mask = occlusion_mask * blend

	occlusion_mask = occlusion_mask.clip(0, 1)

	# Only paste if there is something to paste
	if numpy.any(occlusion_mask > 0):
		temp_vision_frame = paste_back(temp_vision_frame, crop_target_frame, occlusion_mask, affine_matrix)
	
	return temp_vision_frame
