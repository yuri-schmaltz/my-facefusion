from argparse import ArgumentParser
from typing import List, Tuple
import cv2
import numpy

import facefusion.jobs.job_store
from facefusion import config, logger, state_manager, translator, video_manager
from facefusion.filesystem import is_image, is_video, same_file_extension, in_directory
from facefusion.processors.modules.watermark_remover import choices as watermark_remover_choices
from facefusion.processors.modules.watermark_remover.types import WatermarkRemoverInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, ProcessMode
from facefusion.vision import read_static_image, read_static_video_frame

def get_inference_pool() -> None:
    pass

def clear_inference_pool() -> None:
    pass

def register_args(program : ArgumentParser) -> None:
    group_processors = find_argument_group(program, 'processors')
    if group_processors:
        group_processors.add_argument('--watermark-remover-model', help = translator.get('help.model', __package__), default = config.get_str_value('processors', 'watermark_remover_model', 'simple_inpaint'), choices = watermark_remover_choices.watermark_remover_models)
        group_processors.add_argument('--watermark-remover-area-start', help = translator.get('help.watermark_remover_area_start', __package__), type = int, nargs = '+', default = config.get_int_list('processors', 'watermark_remover_area_start', '0 0'))
        group_processors.add_argument('--watermark-remover-area-end', help = translator.get('help.watermark_remover_area_end', __package__), type = int, nargs = '+', default = config.get_int_list('processors', 'watermark_remover_area_end', '0 0'))
        facefusion.jobs.job_store.register_step_keys([ 'watermark_remover_model', 'watermark_remover_area_start', 'watermark_remover_area_end' ])

def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
    apply_state_item('watermark_remover_model', args.get('watermark_remover_model'))
    apply_state_item('watermark_remover_area_start', args.get('watermark_remover_area_start'))
    apply_state_item('watermark_remover_area_end', args.get('watermark_remover_area_end'))

def pre_check() -> bool:
    return True

def pre_process(mode : ProcessMode) -> bool:
    if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
        logger.error(translator.get('choose_image_or_video_target') + translator.get('exclamation_mark'), __name__)
        return False
    if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
        logger.error(translator.get('specify_image_or_video_output') + translator.get('exclamation_mark'), __name__)
        return False
    if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
        logger.error(translator.get('match_target_and_output_extension') + translator.get('exclamation_mark'), __name__)
        return False
    return True

def post_process() -> None:
    read_static_image.cache_clear()
    read_static_video_frame.cache_clear()
    video_manager.clear_video_pool()

def process_frame(inputs : WatermarkRemoverInputs) -> ProcessorOutputs:
    temp_vision_frame = inputs.get('temp_vision_frame')
    temp_vision_mask = inputs.get('temp_vision_mask')
    
    start = state_manager.get_item('watermark_remover_area_start')
    end = state_manager.get_item('watermark_remover_area_end')

    if start and end and len(start) == 2 and len(end) == 2:
        x1, y1 = start
        x2, y2 = end
        
        # Validate coordinates
        h, w = temp_vision_frame.shape[:2]
        x1 = max(0, min(x1, w))
        y1 = max(0, min(y1, h))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        
        if x2 > x1 and y2 > y1:
            # Create a mask for inpainting
            mask = numpy.zeros((h, w), dtype=numpy.uint8)
            mask[y1:y2, x1:x2] = 255
            
            # Simple Inpainting using Navier-Stokes
            temp_vision_frame = cv2.inpaint(temp_vision_frame, mask, 3, cv2.INPAINT_NS)

    return temp_vision_frame, temp_vision_mask
