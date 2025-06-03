# **GPU Temperature Monitor**

A Python script to monitor GPU temperatures, offering real-time interactive console updates, structured JSON output, or a concise short-form summary. This script prioritizes NVIDIA GPU detection using pynvml for accuracy and falls back to psutil for other GPU types or if pynvml is unavailable.  
**GitHub Repository:** (Please insert your GitHub repository link here, e.g., https://github.com/yourusername/gpu-temp)

## **Features**

*   **Interactive Display:** Real-time, flicker-free (on compatible terminals) updates of GPU temperatures.
*   **Intelligent GPU Detection:**
    *   **NVIDIA (Primary):** Uses pynvml for robust and accurate temperature readings for NVIDIA GPUs.
    *   **Fallback (Secondary):** Falls back to psutil for AMD, Intel integrated, or other GPUs, or if pynvml fails.
*   **Color-Coded Temperatures:** Temperatures are displayed in green (normal), yellow (warm), or red (hot) based on general thresholds.
*   **JSON Output:** Export current GPU temperature data in a structured JSON format for scripting or integration.
*   **Short Output:** Get a quick, single-line summary of current GPU temperatures.

## **Installation**

1.  **Clone the repository (or download the script and requirements.txt):**
    ```bash
    git clone https://github.com/tugapse/gpu-temp.git 
    cd gpu-temp # Or the directory where you saved the files
    ```

2.  Install dependencies:
    This script requires psutil and pynvml. All necessary packages are listed in requirements.txt.
    ```bash
    pip install -r requirements.txt
    ```

    *Note: For NVIDIA GPUs, pynvml requires the NVIDIA display drivers and NVML library to be properly installed and accessible on your system. If you encounter issues, ensure nvidia-smi runs successfully in your terminal.*

## **How to Use**

The script offers different modes of operation via command-line arguments.

### **1\. Interactive Real-time Monitoring (Default)**

Run the script without any arguments to get a continuously updating display of your GPU temperatures. This mode attempts to be flicker-free by moving the cursor and overwriting output.
```bash
python gpu_temp_monitor.py
```

### **2\. JSON Output**

Use the `--json` flag to get a single snapshot of the GPU temperature data in JSON format. The script will print the JSON and then exit. This is useful for scripting or integrating with other tools.
```bash
python gpu_temp_monitor.py --json
```

**Example JSON Output:**
```json
{
  "timestamp": "2025-06-03T14:14:59.000000",
  "gpu_temps": [
    {
      "label": "NVIDIA GeForce RTX 4060 Laptop GPU",
      "current": 40.0,
      "high": 85.0,
      "critical": 95.0,
      "detection_source": "pynvml"
    }
  ],
  "gpu_detection_method": "pynvml"
}
```

### **3\. Short Summary Output**

Use the `--short` or `-s` flag to get a concise, single-line summary of the current GPU temperatures. The script will print this line and then exit.
```bash
python gpu_temp_monitor.py --short
# or
python gpu_temp_monitor.py -s
```

**Example Short Output:**
NV1: 40.0°C

*(Output may vary based on your GPU model and detected label)*

## **Troubleshooting**

*   **"No GPU temperature data found..."**:
    *   **NVIDIA GPUs:** This usually means pynvml could not initialize or find your NVIDIA GPU. Ensure your NVIDIA display drivers are fully installed and loaded. Run nvidia-smi in your terminal; if it fails, your driver setup needs attention.
    *   **AMD/Intel/Other GPUs:** psutil relies on lm\_sensors (Linux) or other OS-specific interfaces. Run sensors in your terminal (install lm\_sensors if needed: `sudo pacman -S lm_sensors` on Arch). If your GPU temperature isn't listed there, psutil won't be able to find it.
    *   The error message will list Available sensor keys detected by psutil. You might need to add specific keys to the `psutil_gpu_sensor_keys` list in the script if your GPU's sensor is under an unusual name.
*   **Flickering in Interactive Mode:** Ensure your terminal emulator supports ANSI escape codes. Modern terminals (Linux, macOS, Windows Terminal, VS Code terminal) should work well.
*   **Permission Denied:** On some Linux systems, accessing sensor data might require appropriate permissions or running with sudo.

## **Contributing**

Feel free to open issues or pull requests on the [GitHub repository](https://github.com/tugapse/gpu-temp) if you have suggestions, bug reports, or improvements!