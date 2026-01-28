import argparse
from typing import Sequence
import numpy

def create_float_range(start : float, stop : float, step : float) -> Sequence[float]:
	return numpy.arange(start, stop + step, step).tolist()

def create_float_metavar(float_range : Sequence[float]) -> str:
	if len(float_range) == 1:
		return str(float_range[0])
	return '[' + str(float_range[0]) + '-' + str(float_range[-1]) + ':' + str(float_range[1] - float_range[0]) + ']'

face_mask_erosion_range = create_float_range(-1.0, 1.0, 0.05)

parser = argparse.ArgumentParser()
parser.add_argument('--face-mask-erosion', type=float, default=0.0, choices=face_mask_erosion_range, metavar=create_float_metavar(face_mask_erosion_range))

print("Argparse created successfully")
try:
    parser.parse_args(['--help'])
except SystemExit:
    pass
