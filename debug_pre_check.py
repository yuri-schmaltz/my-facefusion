from facefusion import core, content_analyser, hash_helper
import inspect

print("Checking common_pre_check...")
try:
	result = core.common_pre_check()
	print(f"common_pre_check result: {result}")
except Exception as e:
	import traceback
	traceback.print_exc()
	print(f"common_pre_check crashed: {e}")

content = inspect.getsource(content_analyser).encode()
calc_hash = hash_helper.create_hash(content)
print(f"Calculated content_analyser hash: {calc_hash}")
print(f"Expected hash: b14e7b92")
