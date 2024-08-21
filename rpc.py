import psutil
from PIL import ImageGrab
import pytesseract
import pygetwindow as gw
import re
from pypresence import Presence
import time

pytesseract.pytesseract.tesseract_cmd = 'Tesseract path' # ! Tesseract path

client_id = 'app_id' # ! app id
RPC = Presence(client_id)
RPC.connect()

# Flag to check if the status has been initialized
initialized = False
start_time = None

def is_clip_studio_running():
    """Check if Clip Studio Paint is currently running."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'CLIPStudioPaint.exe':
            return True
    return False

def is_clip_studio_topmost():
    """Check if Clip Studio Paint is the topmost window."""
    try:
        window = gw.getWindowsWithTitle('CLIP STUDIO PAINT')[0]
        return window.isActive
    except IndexError:
        return False

def bring_clip_studio_to_front():
    """Bring Clip Studio Paint to the foreground."""
    window = gw.getWindowsWithTitle('CLIP STUDIO PAINT')
    if window:
        window[0].activate()

def get_clip_studio_project_name():
    """Extract the project name from Clip Studio Paint's window if it's topmost."""
    if is_clip_studio_running() and is_clip_studio_topmost():
        # Find the Clip Studio Paint window
        window = gw.getWindowsWithTitle('CLIP STUDIO PAINT')
        if window:
            # Activate the window
            window[0].activate()
            # Take a screenshot of the specific region
            screenshot = ImageGrab.grab(bbox=(0, 0, 1920, 20))
            text = pytesseract.image_to_string(screenshot)
            # Extract project name from text
            project_name = extract_project_name(text)
            return project_name
    return None

def extract_project_name(text):
    """Extract project name from the text."""
    match = re.search(r'^(.*?) \(', text)  # Extracts everything before the first parenthesis
    if match:
        return match.group(1).strip()
    return "Unrecognized project"

def update_discord_status(project_name, start_time):
    """Update Discord status with the extracted project name."""
    RPC.update(state="Drawing in Clip Studio Paint", 
      details=f"Project: {project_name}", 
      large_image="clip", 
      large_text="Clip Studio Paint",
      start=start_time)

while True:
    if not initialized:
        if is_clip_studio_running():
            bring_clip_studio_to_front()
            time.sleep(1)  # Allow time for Clip Studio Paint to come to the front
            project_name = get_clip_studio_project_name()
            if project_name:
                print(f"Project Name: {project_name}")
                start_time = time.time()
                update_discord_status(project_name, start_time)
                initialized = True
            else:
                print("Clip Studio Paint is running but project not found")
        else:
            print("Clip Studio Paint is not running")
    else:
        project_name = get_clip_studio_project_name()
        if project_name:
            print(f"Project Name: {project_name}")
            update_discord_status(project_name, start_time)
        else:
            print("Clip Studio Paint is not running, not topmost, or project not found")
    
    time.sleep(30)  # Check every 30 seconds
