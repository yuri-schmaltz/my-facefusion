from typing import List, Sequence

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.frame_expander.types import FrameExpanderMode, FrameExpanderTargetRatio

frame_expander_modes : List[FrameExpanderMode] = [ 'span', 'mirror', 'reflect', 'black', 'white' ]
frame_expander_target_ratios : List[FrameExpanderTargetRatio] = [ '16:9', '21:9', '4:3', '1:1', '9:16' ]
frame_expander_blur_range : Sequence[int] = create_int_range(0, 100, 1)
