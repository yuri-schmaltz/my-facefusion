from typing import TypedDict
from facefusion.types import VisionFrame

class GazeCorrectorInputs(TypedDict):
	reference_vision_frame : VisionFrame
	target_vision_frame : VisionFrame
	temp_vision_frame : VisionFrame
