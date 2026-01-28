from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_masker import create_area_mask
from facefusion.face_analyser import get_one_face
from facefusion.processors.modules.face_relighter import choices as face_relighter_choices
from facefusion.processors.modules.face_relighter.types import FaceRelighterInputs
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
		group_processors.add_argument('--face-relighter-type', help = translator.get('help.face_relighter_type', __package__), default = config.get_str_value('processors', 'face_relighter_type', 'brighten'), choices = face_relighter_choices.face_relighter_types)
		group_processors.add_argument('--face-relighter-blend', help = translator.get('help.face_relighter_blend', __package__), type = int, default = config.get_int_value('processors', 'face_relighter_blend', '50'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'face_relighter_type', 'face_relighter_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_relighter_type', args.get('face_relighter_type'))
	apply_state_item('face_relighter_blend', args.get('face_relighter_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	return True


def post_process() -> None:
	pass


def process_frame(inputs : FaceRelighterInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')

	if target_vision_frame is None:
		return temp_vision_frame, None

	type = state_manager.get_item('face_relighter_type')
	blend = state_manager.get_item('face_relighter_blend') / 100.0

	if blend == 0:
		return temp_vision_frame, None

	# Approximate 3D lighting by brightening T-zone (nose, forehead) and darkening cheeks?
	# Or simple global adjustment based on mask.
	
	target_face = get_one_face(temp_vision_frame)
	if not target_face:
		return temp_vision_frame, None
	
	landmarks = target_face.landmark_set.get('68')

	# Create T-Zone mask (Forehead + Nose)
	try:
		# Areas: nose (10). Eyebrows (2,3) kinda cover forehead?
		# Let's use nose and maybe upper lip for center lighting.
		light_mask = create_area_mask(temp_vision_frame, landmarks, ['nose', 'upper-lip', 'left-eyebrow', 'right-eyebrow'])
		
		# Blur heavily for smooth lighting falloff
		light_mask = cv2.GaussianBlur(light_mask, (51, 51), 0)
		light_mask = numpy.expand_dims(light_mask, axis=2)
		
		relit_frame = temp_vision_frame.copy()
		
		if type == 'brighten':
			# Add brightness
			relit_frame = cv2.addWeighted(relit_frame, 1.2, relit_frame, 0, 0)
		elif type == 'darken':
			relit_frame = cv2.addWeighted(relit_frame, 0.8, relit_frame, 0, 0)

		# Composite: Relit center, original background/cheeks
		temp_vision_frame = (relit_frame * light_mask * blend + temp_vision_frame * (1 - (light_mask * blend))).astype(numpy.uint8)

	except:
		pass

	return temp_vision_frame, None
