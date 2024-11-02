import cv2
import requests
import time
from PIL import Image
import io
import ctypes
from ctypes import wintypes
import sounddevice as sd

# Windows API constants for audio control
HWND_BROADCAST = 0xFFFF
WM_APPCOMMAND = 0x319
APPCOMMAND_VOLUME_MUTE = 0x80000
APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
APPCOMMAND_SYSTEM_AUDIO_DEVICE_CHANGE = 0x0E0000

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

def switch_to_headphones():
    """
    Switch Windows audio output to headphones
    """
    # Get the handle for the window
    hwnd = ctypes.cast(ctypes.c_void_p(HWND_BROADCAST), wintypes.HWND)
    
    # Send the command to change audio device
    ctypes.windll.user32.SendMessageW(
        hwnd,
        WM_APPCOMMAND,
        None,
        APPCOMMAND_SYSTEM_AUDIO_DEVICE_CHANGE
    )

def has_headphones(predictions):
    """
    Check if predictions contain headphones or earphones
    """
    headphone_classes = ['headphones', 'earphones', 'earbuds']
    for pred in predictions:
        if pred['class'].lower() in headphone_classes and pred['confidence'] > 0.5:
            return True
    return False

def main():
    last_capture_time = 0
    interval = 1/3  # 3 FPS
    
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