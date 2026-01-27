from typing import TypedDict
from facefusion.types import VisionFrame, Mask

class WatermarkRemoverInputs(TypedDict):
    temp_vision_frame : VisionFrame
    temp_vision_mask : Mask
