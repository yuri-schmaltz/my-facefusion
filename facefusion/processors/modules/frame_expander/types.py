from typing import TypedDict, Literal

from facefusion.types import Mask, VisionFrame

FrameExpanderMode = Literal['span', 'mirror', 'reflect', 'black', 'white']
FrameExpanderTargetRatio = Literal['16:9', '21:9', '4:3', '1:1', '9:16']

class FrameExpanderInputs(TypedDict):
    temp_vision_frame : VisionFrame
    temp_vision_mask : Mask
