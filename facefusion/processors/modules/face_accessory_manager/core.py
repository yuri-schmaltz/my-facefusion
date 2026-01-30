from argparse import ArgumentParser
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_occlusion_mask, create_box_mask, create_region_mask
from facefusion.face_selector import select_faces
from facefusion.processors.modules.face_accessory_manager import choices as face_accessory_manager_choices
from facefusion.processors.modules.face_accessory_manager.types import FaceAccessoryManagerInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, InferencePool, Mask, VisionFrame
from facefusion.vision import unpack_resolution


def get_inference_pool() -> InferencePool:
	return None


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-accessory-manager-model', help = translator.get('help.face_accessory_manager_model', __package__), default = config.get_str_value('processors', 'face_accessory_manager_model', 'replicate'), choices = face_accessory_manager_choices.face_accessory_manager_models)
		group_processors.add_argument('--face-accessory-manager-items', help = translator.get('help.face_accessory_manager_items', __package__), default = config.get_str_list_value('processors', 'face_accessory_manager_items', [ 'occlusion' ]), choices = face_accessory_manager_choices.face_accessory_manager_items, nargs = '+')
		group_processors.add_argument('--face-accessory-manager-blend', help = translator.get('help.face_accessory_manager_blend', __package__), type = int, default = config.get_int_value('processors', 'face_accessory_manager_blend', '100'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'face_accessory_manager_model', 'face_accessory_manager_items', 'face_accessory_manager_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_accessory_manager_model', args.get('face_accessory_manager_model'))
	apply_state_item('face_accessory_manager_items', args.get('face_accessory_manager_items'))
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
	
	model = state_manager.get_item('face_accessory_manager_model') or 'replicate'
	items = state_manager.get_item('face_accessory_manager_items') or [ 'occlusion' ]
	blend = (state_manager.get_item('face_accessory_manager_blend') if state_manager.get_item('face_accessory_manager_blend') is not None else 100) / 100.0

	target_faces = select_faces(reference_vision_frame, target_vision_frame)

	if target_faces:
		for target_face in target_faces:
			if model == 'replicate':
				temp_vision_frame = replicate_accessories(target_face, target_vision_frame, temp_vision_frame, items, blend)
			if model == 'remove':
				temp_vision_frame = remove_accessories(target_face, target_vision_frame, temp_vision_frame, items, blend)

	return temp_vision_frame, temp_vision_mask


def replicate_accessories(target_face, target_vision_frame, temp_vision_frame, items, blend):
	model_template = 'arcface_112_v2'
	model_size = (256, 256)

	crop_target_frame, affine_matrix = warp_face_by_face_landmark_5(target_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	accessory_mask = create_accessory_mask(crop_target_frame, items)

	if blend < 1.0:
		accessory_mask = accessory_mask * blend

	accessory_mask = accessory_mask.clip(0, 1)

	if numpy.any(accessory_mask > 0):
		temp_vision_frame = paste_back(temp_vision_frame, crop_target_frame, accessory_mask, affine_matrix)
	
	return temp_vision_frame


def remove_accessories(target_face, target_vision_frame, temp_vision_frame, items, blend):
	model_template = 'arcface_112_v2'
	model_size = (256, 256)

	crop_temp_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, model_size)
	accessory_mask = create_accessory_mask(crop_temp_frame, items)

	if numpy.any(accessory_mask > 0):
		inpaint_mask = (accessory_mask * 255).astype(numpy.uint8)
		_, inpaint_mask = cv2.threshold(inpaint_mask, 1, 255, cv2.THRESH_BINARY)
		inpainted_crop = cv2.inpaint(crop_temp_frame, inpaint_mask, 3, cv2.INPAINT_TELEA)

		if blend < 1.0:
			accessory_mask = accessory_mask * blend

		temp_vision_frame = paste_back(temp_vision_frame, inpainted_crop, accessory_mask, affine_matrix)

	return temp_vision_frame


def create_accessory_mask(crop_vision_frame : VisionFrame, items : List[str]) -> Mask:
	masks = []

	if 'occlusion' in items:
		masks.append(create_occlusion_mask(crop_vision_frame))

	region_items = []

	for item in items:
		if item == 'glasses':
			region_items.append('glasses')
		if item == 'hair':
			region_items.append('hair')
		if item == 'eyebrows':
			region_items.extend([ 'left-eyebrow', 'right-eyebrow' ])
		if item == 'eyes':
			region_items.extend([ 'left-eye', 'right-eye' ])
		if item == 'nose':
			region_items.append('nose')
		if item == 'mouth':
			region_items.extend([ 'mouth', 'upper-lip', 'lower-lip' ])

	if region_items:
		masks.append(create_region_mask(crop_vision_frame, region_items))

	if masks:
		if len(masks) > 1:
			return numpy.maximum.reduce(masks)
		return masks[0]
	return numpy.zeros(crop_vision_frame.shape[:2], dtype = numpy.float32)
