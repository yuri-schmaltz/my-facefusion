import os
import sys
from typing import Optional
from facefusion.types import AppContext

CURRENT_CONTEXT: Optional[AppContext] = None


def set_app_context(context : AppContext) -> None:
	global CURRENT_CONTEXT
	CURRENT_CONTEXT = context


def detect_app_context() -> AppContext:
	global CURRENT_CONTEXT
	if CURRENT_CONTEXT is not None:
		return CURRENT_CONTEXT

	frame = sys._getframe(1)

	while frame:
		if os.path.join('facefusion', 'jobs') in frame.f_code.co_filename:
			return 'cli'
		if os.path.join('facefusion', 'uis') in frame.f_code.co_filename:
			return 'ui'
		frame = frame.f_back
	return 'cli'
