import sys
import os
sys.path.insert(0, os.getcwd())

print("Importing state_manager...")
try:
    from facefusion import state_manager
    from facefusion.app_context import detect_app_context
    
    print(f"detect_app_context() returns: '{detect_app_context()}'")
    
    print("Getting state...")
    state = state_manager.get_state()
    print(f"get_state() returns type: {type(state)}")
    print(f"get_state() returns: {state}")
    
    print("Getting item 'execution_providers'...")
    item = state_manager.get_item('execution_providers')
    print(f"Item: {item}")
    
    print("Checking metadata...")
    from facefusion import metadata
    print(f"Metadata type: {type(metadata)}")
    try:
        print(f"Metadata name: {metadata.get('name')}")
    except Exception as e:
        print(f"Metadata check failed: {e}")
        
except Exception as e:
    print(f"CRASHED: {e}")
    import traceback
    traceback.print_exc()
