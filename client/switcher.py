import cv2
import requests
import time
from PIL import Image
import io
import platform
import subprocess
import sys
import os

# Initialize webcam
cap = cv2.VideoCapture(0)

def send_image_to_api(image):
    """
    Convert OpenCV image to bytes and send to API
    """
    # Convert the image to PIL format
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image_pil.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Prepare the files for the POST request
    files = {'image': ('image.jpg', img_byte_arr, 'image/jpeg')}
    
    # Send to API
    response = requests.post('http://localhost:5000/predict', files=files)
    return response.json()

def switch_to_headphones_windows(device_name="Headphones"):
    """
    Switch Windows audio output to headphones using pycaw
    """
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities
        
        devices = AudioUtilities.GetAllDevices()
        # Find and set default device
        for device in devices:
            if device_name.lower() in device.FriendlyName.lower():
                AudioUtilities.SetDefaultDevice(device)
                print(f"Switched to {device.FriendlyName}")
                break
    except ImportError:
        print("pycaw not installed. Run: pip install pycaw")
        sys.exit(1)

def switch_to_headphones_mac(device_name="Headphones"):
    """
    Switch macOS audio output to headphones using osascript
    """
    try:
        # Get list of audio devices
        cmd = ["system_profiler", "SPAudioDataType"]
        output = subprocess.check_output(cmd).decode()
        
        # Simple check for headphones being available
        if "Headphones" in output:
            # Set audio output to headphones using osascript
            apple_script = """
            tell application "System Preferences"
                activate
                set current pane to pane "Sound"
                tell application "System Events"
                    tell process "System Preferences"
                        select row 2 of table 1 of scroll area 1 of tab group 1 of window 1
                    end tell
                end tell
            end tell
            """
            subprocess.run(["osascript", "-e", apple_script])
            print("Switched to headphones on macOS")
    except Exception as e:
        print(f"Error switching audio on macOS: {str(e)}")

def switch_to_headphones_linux(device_name="headphones"):
    """
    Switch Linux audio output to headphones using pactl
    """
    try:
        # Get list of sinks (output devices)
        sinks = subprocess.check_output(["pactl", "list", "sinks"]).decode()
        
        # Find the headphone sink
        for line in sinks.split('\n'):
            if device_name.lower() in line.lower():
                sink_name = line.split('#')[-1].strip()
                # Set default sink
                subprocess.run(["pactl", "set-default-sink", sink_name])
                print(f"Switched to {sink_name}")
                break
    except Exception as e:
        print(f"Error switching audio on Linux: {str(e)}")

def switch_to_headphones():
    """
    Cross-platform audio device switching
    """
    system = platform.system()
    
    if system == "Windows":
        switch_to_headphones_windows()
    elif system == "Darwin":  # macOS
        switch_to_headphones_mac()
    elif system == "Linux":
        switch_to_headphones_linux()
    else:
        print(f"Unsupported operating system: {system}")

def has_headphones(predictions):
    """
    Check if predictions contain headphones or earphones
    """
    headphone_classes = ['headphones', 'earphones', 'earbuds']
    for pred in predictions:
        if pred['class'].lower() in headphone_classes and pred['confidence'] > 0.5:
            return True
    return False

def print_available_devices():
    """
    Print available audio devices based on the operating system
    """
    system = platform.system()
    
    if system == "Windows":
        try:
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetAllDevices()
            print("Available audio devices:")
            for device in devices:
                print(f"- {device.FriendlyName}")
        except ImportError:
            print("pycaw not installed. Run: pip install pycaw")
    
    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(["system_profiler", "SPAudioDataType"]).decode()
            print("Available audio devices:")
            print(output)
        except Exception as e:
            print(f"Error getting audio devices on macOS: {str(e)}")
    
    elif system == "Linux":
        try:
            output = subprocess.check_output(["pactl", "list", "sinks"]).decode()
            print("Available audio devices:")
            print(output)
        except Exception as e:
            print(f"Error getting audio devices on Linux: {str(e)}")

def main():
    last_capture_time = 0
    interval = 1/3  # 3 FPS
    
    # Print available audio devices at startup
    print_available_devices()
    
    try:
        while True:
            current_time = time.time()
            
            # Check if it's time to capture a new frame
            if current_time - last_capture_time >= interval:
                # Capture frame
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                    
                try:
                    # Send to API and get response
                    response = send_image_to_api(frame)
                    
                    # Check if headphones are detected
                    if has_headphones(response['predictions']):
                        print("Headphones detected! Switching audio output...")
                        switch_to_headphones()
                    
                    # Display the frame with predictions
                    if 'image_url' in response:
                        print(f"Predictions: {response['predictions']}")
                
                except Exception as e:
                    print(f"Error processing frame: {str(e)}")
                
                last_capture_time = current_time
            
            # Small delay to prevent maxing out CPU
            time.sleep(0.01)
            
            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()