from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_analyser import get_many_faces
from facefusion.face_masker import create_box_mask
from facefusion.face_selector import select_faces
from facefusion.processors.modules.privacy_blur import choices as privacy_blur_choices
from facefusion.processors.modules.privacy_blur.types import PrivacyBlurInputs
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
		group_processors.add_argument('--privacy-blur-mode', help = translator.get('help.privacy_blur_mode', __package__), default = config.get_str_value('processors', 'privacy_blur_mode', 'blur'), choices = privacy_blur_choices.privacy_blur_modes)
		group_processors.add_argument('--privacy-blur-amount', help = translator.get('help.privacy_blur_amount', __package__), type = int, default = config.get_int_value('processors', 'privacy_blur_amount', '30'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'privacy_blur_mode', 'privacy_blur_amount' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('privacy_blur_mode', args.get('privacy_blur_mode'))
	apply_state_item('privacy_blur_amount', args.get('privacy_blur_amount'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : PrivacyBlurInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask

	mode = state_manager.get_item('privacy_blur_mode')
	amount = state_manager.get_item('privacy_blur_amount') / 100.0

	# 1. Detect ALL faces in the frame
	all_faces = get_many_faces(target_vision_frame)
	
	# 2. Identify faces involved in swap (TARGETS)
	# These are the ones we want to KEEP (or have already swapped)
	target_faces = select_faces(reference_vision_frame, target_vision_frame)
	
	# 3. Identify Bystanders (All - Targets)
	bystander_faces = []
	if all_faces:
		for face in all_faces:
			is_target = False
			if target_faces:
				for target_face in target_faces:
					# Compare using bounding box overlap using Distance
					# Simple center distance check
					dist = numpy.linalg.norm(face.center - target_face.center)
					if dist < 10: # Threshold for "same face"
						is_target = True
						break
			
			if not is_target:
				bystander_faces.append(face)
	
	# 4. Blur Bystanders
	if bystander_faces and amount > 0:
		for bystander in bystander_faces:
			temp_vision_frame = apply_privacy(temp_vision_frame, bystander, mode, amount)

	return temp_vision_frame, temp_vision_mask


def apply_privacy(temp_vision_frame, face, mode, amount):
	# Extract bounding box
	x1, y1, x2, y2 = face.bbox.astype(int)
	h, w, c = temp_vision_frame.shape
	
	# Padding
	padding = 0.2
	box_h = y2 - y1
	box_w = x2 - x1
	y1 = max(0, int(y1 - box_h * padding))
	y2 = min(h, int(y2 + box_h * padding))
	x1 = max(0, int(x1 - box_w * padding))
	x2 = min(w, int(x2 + box_w * padding))
	
	roi = temp_vision_frame[y1:y2, x1:x2]
	if roi.size == 0:
		return temp_vision_frame

	processed_roi = roi.copy()
	
	if mode == 'blur':
		# Gaussian Blur
		ksize = int(amount * 100)
		if ksize % 2 == 0: ksize += 1
		processed_roi = cv2.GaussianBlur(roi, (ksize, ksize), 0)
	
	elif mode == 'mosaic':
		# Pixelate
		mh, mw, mc = roi.shape
		# scaling factor based on amount
		ratio = max(0.01, 1.0 - amount)
		small = cv2.resize(roi, (int(mw*ratio), int(mh*ratio)), interpolation=cv2.INTER_LINEAR)
		processed_roi = cv2.resize(small, (mw, mh), interpolation=cv2.INTER_NEAREST)

	# Creating a circular mask for nicer blending? Or just box?
	# Implementation plan didn't specify, box is standard for privacy.
	# But let's use a soft mask if possible?
	# For now, hard box replacement to ensure privacy.
	temp_vision_frame[y1:y2, x1:x2] = processed_roi
	
	return temp_vision_frame
