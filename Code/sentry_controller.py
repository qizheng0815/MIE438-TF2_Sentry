import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE" 

import serial
import time
import cv2
from pynput import keyboard
from ultralytics import YOLO

ESP32_IP = "192.168.137.33"
stream_url = f"http://{ESP32_IP}:81/stream"
bt_port = 'COM6'  # Replace with your Bluetooth port

tracking = True
model = YOLO('yolov8s.pt')  # Load the YOLOv8s model for object detection
last_f_timer = 0  # Timer to track the last time 'f' was sent

try: #Initialization of Bluetooth Check
    ser = serial.Serial(bt_port, 115200, timeout=0.5)
    print("Successfully connected to Bluetooth device.")

except:
    print("Failed to connect to Bluetooth device. Please check the connection and try again.")
    exit()
    
# Clear any existing data in the buffers
ser.reset_input_buffer()
ser.reset_output_buffer()

#Initialize Video Capture
cap = None

#Track State of Key
held_keys = set()

def send_movement():
    v = 0 #Vertical Movement 
    if 'w' in held_keys: v+=1
    if 's' in held_keys: v-=1
    
    h = 0 #Horizontal Movement
    if 'd' in held_keys: h+=1
    if 'a' in held_keys: h-=1
    
    if v == 0 and h == 0:
        ser.write(b'x') # Send 'x' to stop movement
        print("No keys held, sending 'x' to stop movement.")
    elif v == 1 and h == 0:
        ser.write(b'w') # Move forward
        print("Moving forward.")
    elif v == -1 and h == 0:
        ser.write(b's') # Move backward
        print("Moving backward.")
    elif v == 0 and h == 1:
        ser.write(b'd') # Move right
        print("Moving right.")
    elif v == 0 and h == -1:
        ser.write(b'a') # Move left
        print("Moving left.")

    else:
        newest_key = list(held_keys)[-1] # Get the most recently pressed key still being held
        if newest_key in ['w', 'a', 's', 'd']:
            ser.write(newest_key.encode()) # Send the most recent key to maintain movement
            print(f"Multiple keys held, sending '{newest_key}' to maintain movement.")

def on_press(key):
    global tracking, model, cap
    try:
        k = key.char.lower()  # Convert to lowercase for uniformity
        
        if k == 'm':
            tracking = not tracking
            if tracking:
                print("Object tracking enabled.")
                if cap is None:
                    cap = cv2.VideoCapture(stream_url)  # Start video capture
                    print("Video stream started.")
            else:
                print("Object tracking disabled.")
                if cap:
                    cap.release()  # Stop video capture
                    cap = None
                    print("Video stream stopped.")
                cv2.destroyAllWindows()  # Close any OpenCV windows
        
        
            
        if k in ['w', 'a', 's', 'd', 'f'] and k not in held_keys:
            held_keys.add(k)
        
            if k == 'f':
                ser.write(k.encode()) # Send key once when pressed
            
            else:
                send_movement() # Update movement based on currently held keys
            
            print(f"Key '{k}' pressed. Sent to Bluetooth device.")
            
    except AttributeError:
        pass # Ignore other keys
    
  
def on_release(key):
    try:
        k = key.char.lower()
        if k in held_keys:
            held_keys.remove(k)
            send_movement() # Update movement based on currently held keys
            print(f"Key '{k}' released. Updated movement sent to Bluetooth device.")
            
        if k == 'q':
            print("Exiting program.")
            return False  # Stop listener
        
    except AttributeError:
        pass # Ignore other keys


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
print("Movement Controls are WASD. Press 'Q' to quit.")

#MAIN LOOP
try:
    time.sleep(2)  # Allow some time for the video stream to initialize
    
    while listener.running:
        if tracking:
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(stream_url)
                time.sleep(1)  # Allow some time for the video stream to initialize
                continue
            
            success, frame = cap.read()
        
            if success:
                results= model.predict(frame, classes=[0], device=0, conf = 0.5, verbose=False)  # Run object detection on the frame with a confidence threshold of 0.5
                if len(results) > 0 and len(results[0].boxes) > 0:
                
                    for box in results[0].boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box coordinates
                        confidence = box.conf[0]  # Get confidence score
                        if confidence > 0.5:  # Only consider detections with confidence > 0.5
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw bounding box on the frame
                            cv2.putText(frame, f'Person: {confidence:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  # Label the detection with confidence score
                
                cv2.imshow("Sentry Camera Feed", frame)  # Display the video feed with detections
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Exiting program.")
                    break
            
        
            else:
                print("Loading Stream or Object Tracking... Please wait.")
                time.sleep(0.1)  # Sleep briefly to allow time for the stream to load or tracking to initialize
        else:
            time.sleep(0.05)  # Sleep briefly to reduce CPU usage when not tracking
            
finally:
    if cap:
        cap.release()
        
    cv2.destroyAllWindows()
    ser.close()
    listener.stop()

