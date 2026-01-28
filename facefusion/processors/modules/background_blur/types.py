from typing import TypedDict
from facefusion.types import VisionFrame

class BackgroundBlurInputs(TypedDict):
	reference_vision_frame : VisionFrame
	target_vision_frame : VisionFrame
	temp_vision_frame : VisionFrame
