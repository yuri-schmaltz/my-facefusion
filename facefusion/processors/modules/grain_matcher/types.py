from typing import TypedDict
from facefusion.types import VisionFrame

class GrainMatcherInputs(TypedDict):
	target_vision_frame : VisionFrame
	temp_vision_frame : VisionFrame
