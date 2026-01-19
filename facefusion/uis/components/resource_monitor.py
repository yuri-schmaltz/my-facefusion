from typing import Optional
import gradio
import psutil
import shutil
import subprocess

from facefusion import state_manager, translator
from facefusion.common_helper import get_first

RESOURCE_MONITOR_Label : Optional[gradio.Label] = None

def render() -> None:
    global RESOURCE_MONITOR_Label
    
    RESOURCE_MONITOR_Label = gradio.Label(
        label = "Resource Usage",
        value = "Initializing...",
        show_label = True,
        every = 2.0
    )


def listen() -> None:
    if RESOURCE_MONITOR_Label:
        RESOURCE_MONITOR_Label.change(update_resource_monitor, outputs = RESOURCE_MONITOR_Label)
        # Note: 'every' in render() handles the periodic update if this were a generator or loaded event.
        # But Gradio 3/4 'every' works on events usually. 
        # For simple polling, we might need a load event or just rely on the component's internal timer if supported.
        # Actually, best practice for 'every' is on standard event listeners like default load.
        pass

def update_resource_monitor() -> str:
    ram_usage = get_system_memory_usage()
    vram_usage = get_gpu_memory_usage()
    return f"RAM: {ram_usage} | VRAM: {vram_usage}"

def get_system_memory_usage() -> str:
    mem = psutil.virtual_memory()
    used_gb = mem.used / (1024 ** 3)
    total_gb = mem.total / (1024 ** 3)
    return f"{used_gb:.1f}/{total_gb:.1f} GB ({mem.percent}%)"

def get_gpu_memory_usage() -> str:
    nvidia_smi = shutil.which('nvidia-smi')
    if not nvidia_smi:
        return "N/A"
    
    try:
        result = subprocess.run(
            [nvidia_smi, '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
            encoding='utf-8', capture_output=True, check=False
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                # Handle multiple GPUs? Just take first line for now
                line = output.split('\n')[0]
                used, total = line.split(',')
                return f"{int(used)}/{int(total)} MB"
    except Exception:
        pass
    
    return "N/A"
