# gpu_temp_monitor.py

import psutil
import time
import os
import re
import sys
import argparse
import json
from datetime import datetime

# Attempt to import pynvml, which is needed for detailed NVIDIA GPU info
try:
    # Explicitly import all necessary functions and constants from pynvml
    from pynvml import (
        nvmlInit,
        nvmlDeviceGetCount,
        nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetName,
        nvmlDeviceGetTemperature,
        nvmlShutdown,
        NVMLError,
        NVML_ERROR_NOT_FOUND,
        NVML_TEMPERATURE_GPU
    )
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
except NVMLError_LibraryNotFound:
    PYNVML_AVAILABLE = False
except Exception as e:
    sys.stderr.write(f"Warning: Failed to import pynvml components: {e}. pynvml features will be unavailable.\n")
    PYNVML_AVAILABLE = False


# Define ANSI escape codes directly for cross-platform console coloring
ANSI_RESET = "\x1b[0m"
ANSI_RED = "\x1b[31m"
ANSI_GREEN = "\x1b[32m"
ANSI_YELLOW = "\x1b[33m"
ANSI_BLUE = "\x1b[34m"
ANSI_CYAN = "\x1b[36m"
ANSI_WHITE = "\x1b[37m"

def clear_console():
    """
    Moves the cursor to the top-left of the console and clears the screen from that point.
    This prevents flickering compared to os.system('clear/cls').
    Uses raw ANSI escape codes.
    """
    sys.stdout.write("\x1b[H\x1b[J")
    sys.stdout.flush()

def get_temp_color(temperature):
    """Returns an ANSI color code based on the temperature value."""
    if temperature < 60:
        return ANSI_GREEN
    elif temperature < 80:
        return ANSI_YELLOW
    else:
        return ANSI_RED

def get_gpu_data_structured():
    """
    Fetches and structures GPU temperature data into a Python dictionary.
    Prioritizes pynvml for NVIDIA GPUs, then falls back to psutil.
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "gpu_temps": [],
        "gpu_detection_method": "None"
    }

    try:
        # --- Attempt to get NVIDIA GPU data using pynvml ---
        if PYNVML_AVAILABLE:
            try:
                nvmlInit()
                device_count = nvmlDeviceGetCount()
                if device_count > 0:
                    data["gpu_detection_method"] = "pynvml"
                    for i in range(device_count):
                        handle = nvmlDeviceGetHandleByIndex(i)
                        
                        gpu_name_bytes = nvmlDeviceGetName(handle)
                        if isinstance(gpu_name_bytes, bytes):
                            gpu_name = gpu_name_bytes.decode('utf-8')
                        else:
                            gpu_name = gpu_name_bytes
                        
                        temp_c = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
                        
                        high_temp = 85.0
                        critical_temp = 95.0

                        data["gpu_temps"].append({
                            "label": gpu_name,
                            "current": float(temp_c),
                            "high": high_temp,
                            "critical": critical_temp,
                            "detection_source": "pynvml"
                        })
                nvmlShutdown()
            except NVMLError as error:
                data["error"] = f"pynvml error: {error}. Falling back to psutil."
                data["gpu_detection_method"] = "pynvml_failed_fallback_psutil"
                if error.value == NVML_ERROR_NOT_FOUND:
                    data["error"] += " (NVIDIA driver not loaded or no NVIDIA GPUs found)"
            except Exception as e:
                data["error"] = f"Unexpected pynvml issue: {e}. Falling back to psutil."
                data["gpu_detection_method"] = "pynvml_exception_fallback_psutil"

        # --- Fallback to psutil.sensors_temperatures() if pynvml failed or not available ---
        if not data["gpu_temps"] or data["gpu_detection_method"] in ["pynvml_failed_fallback_psutil", "pynvml_exception_fallback_psutil"]:
            raw_temps = psutil.sensors_temperatures()
            
            psutil_gpu_sensor_keys = ['amdgpu', 'nouveau', 'gpu', 'radeon'] 
            
            psutil_gpu_counter = 1
            psutil_found_gpu_data = False

            for key, sensors_list in raw_temps.items():
                for sensor in sensors_list:
                    is_gpu_sensor = False
                    if hasattr(sensor, 'current') and sensor.current is not None:
                        if key in psutil_gpu_sensor_keys:
                            is_gpu_sensor = True
                        elif 'gpu' in key.lower() or 'video' in key.lower():
                            is_gpu_sensor = True
                        elif 'temp' in key.lower() and hasattr(sensor, 'label') and 'gpu' in sensor.label.lower():
                            is_gpu_sensor = True

                    if is_gpu_sensor:
                        gpu_label = sensor.label.strip() if sensor.label else f"GPU {psutil_gpu_counter}"
                        data["gpu_temps"].append({
                            "label": gpu_label,
                            "current": float(sensor.current),
                            "high": float(sensor.high) if sensor.high is not None else 85.0,
                            "critical": float(sensor.critical) if sensor.critical is not None else 95.0,
                            "detection_source": f"psutil ({key})"
                        })
                        psutil_gpu_counter += 1
                        psutil_found_gpu_data = True
            
            if psutil_found_gpu_data and data["gpu_detection_method"] not in ["pynvml"]:
                data["gpu_detection_method"] = "psutil"
            elif not psutil_found_gpu_data and data["gpu_detection_method"] not in ["pynvml"]:
                data["gpu_detection_method"] = "None"
                if "error" not in data or "Falling back to psutil" in data["error"]:
                    data["error"] = data.get("error", "") + " No GPU temperature data found via psutil either."
                data["available_sensor_keys"] = list(raw_temps.keys())

    except Exception as e:
        data["error"] = f"General error during GPU data collection: {e}"
        data["gpu_detection_method"] = "error"
        try:
            data["available_sensor_keys"] = list(psutil.sensors_temperatures().keys())
        except Exception:
            data["available_sensor_keys"] = []
    
    return data


def display_gpu_temperatures(gpu_data):
    """
    Displays GPU temperature data in a formatted console output.
    Takes structured data from get_gpu_data_structured().
    """
    sys.stdout.write(f"{ANSI_CYAN}--- GPU Temperature Monitor ---{ANSI_RESET}\n")

    gpu_sensors_data = gpu_data.get("gpu_temps", [])

    if gpu_sensors_data:
        # Define widths for display
        GPU_LABEL_WIDTH = 35 # <--- FIX: Increased width for long GPU names
        TEMP_VALUE_WIDTH = 7 # for X.X°C
        
        # Recalculate LINE_LENGTH based on the new GPU_LABEL_WIDTH
        LINE_LENGTH = GPU_LABEL_WIDTH + 3 * (TEMP_VALUE_WIDTH + 1) + 5 # Label + 3 temps + spacing

        sys.stdout.write("-" * LINE_LENGTH + "\n")
        # Header for GPU section
        sys.stdout.write(f"{ANSI_BLUE}{'GPU':<{GPU_LABEL_WIDTH}}{'Current':<{TEMP_VALUE_WIDTH+1}}{'High':<{TEMP_VALUE_WIDTH+1}}{'Critical':<{TEMP_VALUE_WIDTH+1}}{ANSI_RESET}\n")
        sys.stdout.write("-" * LINE_LENGTH + "\n")

        for gpu_info in gpu_sensors_data:
            gpu_color = get_temp_color(gpu_info["current"])
            current_gpu_str = f"{gpu_info['current']:.1f}°C"
            high_gpu_str = f"{gpu_info['high']:.1f}°C"
            critical_gpu_str = f"{gpu_info['critical']:.1f}°C"

            sys.stdout.write(f"{ANSI_WHITE}{gpu_info['label']:<{GPU_LABEL_WIDTH}}{ANSI_RESET}"
                             f"{gpu_color}{current_gpu_str:<{TEMP_VALUE_WIDTH+1}}{ANSI_RESET}"
                             f"{high_gpu_str:<{TEMP_VALUE_WIDTH+1}}{ANSI_RESET}"
                             f"{critical_gpu_str:<{TEMP_VALUE_WIDTH+1}}{ANSI_RESET}\n")
        sys.stdout.write("-" * LINE_LENGTH + "\n")
    elif "error" in gpu_data:
        sys.stdout.write(f"{ANSI_YELLOW}{gpu_data['error']}{ANSI_RESET}\n")
        if "available_sensor_keys" in gpu_data:
            sys.stdout.write(f"{ANSI_YELLOW}Available sensor keys: {', '.join(gpu_data['available_sensor_keys'])}{ANSI_RESET}\n")
        sys.stdout.write("-" * 55 + "\n")
    else:
        sys.stdout.write(f"{ANSI_YELLOW}No GPU temperature data available.{ANSI_RESET}\n")
        sys.stdout.write("-" * 55 + "\n")

    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Monitor GPU temperatures.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output temperature data in JSON format and exit."
    )
    parser.add_argument(
        "--short", "-s",
        action="store_true",
        help="Output a short, single-line version of current temperatures and exit."
    )
    args = parser.parse_args()

    if args.json and args.short:
        sys.stderr.write("Error: --json and --short arguments are mutually exclusive.\n")
        sys.exit(1)

    if args.json or args.short:
        gpu_data = get_gpu_data_structured()

        if "error" in gpu_data and not gpu_data.get("gpu_temps"):
            sys.stderr.write(f"{ANSI_RED}Error fetching GPU data: {gpu_data['error']}{ANSI_RESET}\n")
            if "available_sensor_keys" in gpu_data:
                sys.stderr.write(f"{ANSI_YELLOW}Available sensor keys: {', '.join(gpu_data['available_sensor_keys'])}{ANSI_RESET}\n")
            sys.exit(1)

        if args.json:
            try:
                json_output = json.dumps(gpu_data, indent=2)
                sys.stdout.write(json_output + "\n")
                sys.stdout.flush()
            except Exception as e:
                sys.stderr.write(f"Error generating JSON output: {e}\n")
                sys.exit(1)
            sys.exit(0)
        elif args.short:
            short_output_parts = []

            if not gpu_data.get("gpu_temps"):
                short_output_parts.append("GPU: N/A")
            else:
                for i, gpu in enumerate(gpu_data["gpu_temps"]):
                    display_label = gpu['label'].replace('GPU ', 'G') if gpu['label'].startswith('GPU ') else f"G{i+1}"
                    if 'nvidia' in gpu['label'].lower():
                        display_label = f"NV{i+1}"
                    elif 'amd' in gpu['label'].lower() or 'radeon' in gpu['label'].lower():
                        display_label = f"AMD{i+1}"
                    
                    short_output_parts.append(f"{display_label}: {gpu['current']:.1f}°C")

            sys.stdout.write(" | ".join(short_output_parts) + "\n")
            sys.stdout.flush()
            sys.exit(0)
    else:
        try:
            while True:
                clear_console()
                try:
                    gpu_data_live = get_gpu_data_structured()
                    display_gpu_temperatures(gpu_data_live)
                except Exception as e:
                    sys.stdout.write(f"{ANSI_RED}An error occurred: {e}{ANSI_RESET}\n")
                    sys.stdout.flush()
                time.sleep(2)
        except KeyboardInterrupt:
            sys.stdout.write(f"\n{ANSI_CYAN}Monitoring stopped.{ANSI_RESET}\n")
            sys.stdout.flush()
            sys.exit(0)

if __name__ == "__main__":
    main()