from facefusion import logger, process_manager, state_manager, translator


def is_process_stopping() -> bool:
	if not process_manager.is_stopping():
		# Check if orchestrator canceled the job
		is_canceled = state_manager.get_item('is_canceled_callback')
		if is_canceled and is_canceled():
			process_manager.stop()

	if process_manager.is_stopping():
		process_manager.end()
		logger.info(translator.get('processing_stopped'), __name__)
	return process_manager.is_pending()
