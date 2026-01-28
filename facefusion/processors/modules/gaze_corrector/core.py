from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_masker import create_area_mask
from facefusion.face_analyser import get_one_face
from facefusion.processors.modules.gaze_corrector import choices as gaze_corrector_choices
from facefusion.processors.modules.gaze_corrector.types import GazeCorrectorInputs
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
		group_processors.add_argument('--gaze-corrector-type', help = translator.get('help.gaze_corrector_type', __package__), default = config.get_str_value('processors', 'gaze_corrector_type', 'enhance'), choices = gaze_corrector_choices.gaze_corrector_types)
		group_processors.add_argument('--gaze-corrector-blend', help = translator.get('help.gaze_corrector_blend', __package__), type = int, default = config.get_int_value('processors', 'gaze_corrector_blend', '50'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'gaze_corrector_type', 'gaze_corrector_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('gaze_corrector_type', args.get('gaze_corrector_type'))
	apply_state_item('gaze_corrector_blend', args.get('gaze_corrector_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : GazeCorrectorInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_mask = inputs.get('temp_vision_mask')

	if target_vision_frame is None:
		return temp_vision_frame, temp_vision_mask

	type = state_manager.get_item('gaze_corrector_type')
	blend = state_manager.get_item('gaze_corrector_blend') / 100.0

	if blend == 0:
		return temp_vision_frame, temp_vision_mask

	# Enhance eyes
	target_face = get_one_face(temp_vision_frame)
	if not target_face:
		return temp_vision_frame, temp_vision_mask
	
	landmarks = target_face.landmark_set.get('68')
	
	try:
		eye_mask = create_area_mask(temp_vision_frame, landmarks, ['left-eye', 'right-eye'])
		# Dilate slightly
		kernel = numpy.ones((5,5), numpy.uint8)
		eye_mask = cv2.dilate(eye_mask, kernel, iterations=1)
		eye_mask = numpy.expand_dims(eye_mask, axis=2)
		
		corrected_frame = temp_vision_frame.copy()
		
		if type == 'enhance':
			# Sharpen and brighten
			# Simple unsharp mask style sharpening
			gaussian = cv2.GaussianBlur(corrected_frame, (0, 0), 2.0)
			corrected_frame = cv2.addWeighted(corrected_frame, 1.5, gaussian, -0.5, 0)
			
			# Brighten
			corrected_frame = cv2.addWeighted(corrected_frame, 1.1, corrected_frame, 0, 10)

		# Composite
		temp_vision_frame = (corrected_frame * eye_mask * blend + temp_vision_frame * (1 - (eye_mask * blend))).astype(numpy.uint8)
	
	except:
		pass

	return temp_vision_frame, temp_vision_mask
