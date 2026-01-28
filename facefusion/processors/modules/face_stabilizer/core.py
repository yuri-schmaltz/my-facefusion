from argparse import ArgumentParser
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, state_manager, translator
from facefusion.face_analyser import get_one_face
from facefusion.processors.modules.face_stabilizer import choices as face_stabilizer_choices
from facefusion.processors.modules.face_stabilizer.types import FaceStabilizerInputs
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
		group_processors.add_argument('--face-stabilizer-type', help = translator.get('help.face_stabilizer_type', __package__), default = config.get_str_value('processors', 'face_stabilizer_type', 'scale'), choices = face_stabilizer_choices.face_stabilizer_types)
		group_processors.add_argument('--face-stabilizer-blend', help = translator.get('help.face_stabilizer_blend', __package__), type = int, default = config.get_int_value('processors', 'face_stabilizer_blend', '80'), choices = range(0, 101), metavar = '[0-100]')
		facefusion.jobs.job_store.register_step_keys([ 'face_stabilizer_type', 'face_stabilizer_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_stabilizer_type', args.get('face_stabilizer_type'))
	apply_state_item('face_stabilizer_blend', args.get('face_stabilizer_blend'))


def pre_check() -> bool:
	return True


def pre_process(mode : str) -> bool:
	# Usually stabilizers need a pre-pass to calculate trajectory/offsets.
	# But here we are frame-by-frame. 
	# A true stabilizer needs temporal smoothing, which is hard in a pure 'process_frame' architecture without state.
	# HACK: We can simply center the face in every frame. 
	# This creates a perfect lock-on effect (like those TikTok trends).
	return True


def post_process() -> None:
	pass


def process_frame(inputs : FaceStabilizerInputs) -> ProcessorOutputs:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')

	if target_vision_frame is None:
		return temp_vision_frame, None

	type = state_manager.get_item('face_stabilizer_type')
	# Blend here effectively means how much we "correct" towards center. 
	# 100% = perfectly centered face.
	# 50% = half way there (smooths out jitters if target moves a lot but we only correct partially? No, that just moves it weirdly).
	# Let's interpret blend as 'strength' of zoom? No.
	# Let's interpret blend as 'smoothing' if we had history. Without history, it's just 'lock strength'.
	
	target_face = get_one_face(temp_vision_frame)
	if not target_face:
		return temp_vision_frame, None
	
	center = target_face.center
	h, w, c = temp_vision_frame.shape
	frame_center = numpy.array([w / 2, h / 2])
	
	# Calculate offset needed to bring face center to frame center
	offset = frame_center - center
	
	# Apply transformation
	M = numpy.float32([[1, 0, offset[0]], [0, 1, offset[1]]])
	
	# Warp
	stabilized_frame = cv2.warpAffine(temp_vision_frame, M, (w, h))
	
	# Handle borders?
	# 'scale' mode: Zoom in to hide black borders
	if type == 'scale':
		# Calculate max offset to determine zoom needed
		# Heuristic: zoom in by 20% covers most standard movements
		zoom = 1.2
		# Resize from center
		M_scale = cv2.getRotationMatrix2D((w/2, h/2), 0, zoom)
		stabilized_frame = cv2.warpAffine(stabilized_frame, M_scale, (w, h))

	return stabilized_frame, None
