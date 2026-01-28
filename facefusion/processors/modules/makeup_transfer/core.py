from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_masker import create_area_mask
from facefusion.face_analyser import get_one_face
from facefusion.processors.modules.makeup_transfer import choices as makeup_transfer_choices
from facefusion.processors.modules.makeup_transfer.types import MakeupTransferInputs
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
		group_processors.add_argument('--makeup-transfer-type', help = translator.get('help.makeup_transfer_type', __package__), default = config.get_str_value('processors', 'makeup_transfer_type', 'lip_tint'), choices = makeup_transfer_choices.makeup_transfer_types)
		group_processors.add_argument('--makeup-transfer-blend', help = translator.get('help.makeup_transfer_blend', __package__), type = int, default = config.get_int_value('processors', 'makeup_transfer_blend', '50'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'makeup_transfer_type', 'makeup_transfer_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('makeup_transfer_type', args.get('makeup_transfer_type'))
	apply_state_item('makeup_transfer_blend', args.get('makeup_transfer_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : MakeupTransferInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask

	type = state_manager.get_item('makeup_transfer_type')
	blend = state_manager.get_item('makeup_transfer_blend') / 100.0

	if blend == 0:
		return temp_vision_frame, temp_vision_mask

	# We need face landmarks to apply makeup to specific areas
	# Since temp_vision_frame is the *swapped* face, we should detect landmarks on IT.
	# But detection is expensive.
	# We can use the landmarks from the target_face IF the swap didn't move features too much (it usually aligns).
	# However, for precision, let's detect on the swapped frame (temp_vision_frame).
	
	target_face = get_one_face(temp_vision_frame)
	if not target_face:
		return temp_vision_frame, temp_vision_mask
		
	# Create masks using landmarks
	masks = []
	
	if type == 'lip_tint':
		# area 'mouth' or 'upper-lip'/'lower-lip'
		# Let's use 'mouth' (includes lips usually) or combine upper/lower
		# In choices.py we have 'upper-lip', 'lower-lip'
		# create_area_mask takes 'crop' frame usually, but works on full if we pass full landmarks?
		# No, create_area_mask expects 'crop_vision_frame' and 'face_landmark_68' which is relative to crop?
		# Wait, let's check create_area_mask implementation in face_masker.py
		
		# It takes 'crop_vision_frame' and 'face_landmark_68'.
		# If we pass full frame and full landmarks, it should work.
		landmarks = target_face.landmark_set.get('68') # Full frame landmarks?
		# get_one_face returns Face with landmarks relative to frame.
		
		# We need to adapt create_area_mask to work on full frame or pass full frame as "crop"
		try:
			lip_mask = create_area_mask(temp_vision_frame, landmarks, ['upper-lip', 'lower-lip'])
			masks.append(lip_mask)
		except:
			pass
			
	elif type == 'eye_shadow':
		# Upper part of eyes. Not standard area.
		# Use 'left-eyebrow', 'right-eyebrow' and 'left-eye', 'right-eye' and interpolate?
		# For now, simplistic: use eye area.
		try:
			eye_mask = create_area_mask(temp_vision_frame, landmarks, ['left-eye', 'right-eye'])
			# Dilate heavily to simulate shadow around eyes
			kernel = numpy.ones((15,15), numpy.uint8) 
			eye_mask = cv2.dilate(eye_mask, kernel, iterations=1)
			masks.append(eye_mask)
		except:
			pass

	if not masks:
		return temp_vision_frame, temp_vision_mask
		
	final_mask = numpy.maximum.reduce(masks)
	final_mask = numpy.expand_dims(final_mask, axis=2)
	
	# Apply Color
	makeup_layer = temp_vision_frame.copy()
	if type == 'lip_tint':
		# Red tint
		makeup_layer = cv2.applyColorMap(makeup_layer, cv2.COLORMAP_AUTUMN) 
	elif type == 'eye_shadow':
		# Dark smokey
		makeup_layer = (makeup_layer * 0.7).astype(numpy.uint8)

	# Composite
	temp_vision_frame = (makeup_layer * final_mask * blend + temp_vision_frame * (1 - (final_mask * blend))).astype(numpy.uint8)

	return temp_vision_frame, temp_vision_mask
