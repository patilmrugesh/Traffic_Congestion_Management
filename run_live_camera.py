import cv2
import time
import sys
import os
import requests
import base64

# Add root directory to python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.video_processor import VideoProcessor

# The live feed URL from IP Webcam
# IP Webcam typically streams raw video over port 8080 at `/video`.
LIVE_FEED_URL = "http://192.168.55.66:8080/video"
# If the above doesn't work, try uncommenting the HTTPS link:
# LIVE_FEED_URL = "https://192.168.55.66:8080/video"

def check_and_send_incidents(vp, last_time):
    now = time.time()
    if now - last_time < 10.0:  # 10 second cooldown
        return last_time

    incident_type = None
    desc = None

    alerts = getattr(vp, 'latest_alerts', [])
    # Check for critical alerts from the analyzer
    critical = [a for a in alerts if a['severity'] in ('critical', 'high')]
    if critical:
        a = critical[0]
        if a.get("type") == "accident":
            incident_type, desc = "accident", a["message"]
        elif "AMBULANCE" in a["message"].upper():
            incident_type, desc = "ambulance", f"Ambulance detected: {a['message']}"

    # Check for Crowd
    if not incident_type and hasattr(vp, 'shared_tracks'):
        persons = sum(1 for t in vp.shared_tracks if getattr(t, 'is_person', False))
        if persons > 12:
            incident_type, desc = "crowd", f"Large crowd of {persons} pedestrians detected."

    # Check for stalled vehicles (parking)
    if not incident_type and hasattr(vp, 'shared_lane_stats'):
        for lane, s in vp.shared_lane_stats.items():
            if getattr(s, 'max_wait_time', 0) > 120.0:
                incident_type, desc = "parking", f"Potential stalled vehicle in {lane} lane."

    if incident_type and vp.latest_frame is not None:
        try:
            _, buf = cv2.imencode(".jpg", vp.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
            payload = {
                "type": incident_type, "description": desc,
                "timestamp": now, "frame_b64": b64
            }
            requests.post("http://localhost:8000/api/add-incident", json=payload, timeout=2)
            print(f"[Live Camera] Sent Incident to Dashboard: {incident_type} - {desc}")
        except Exception as e:
            pass  # Fail silently if backend web dashboard is not running
        return now

    return last_time

def main():
    print(f"Connecting to live camera feed: {LIVE_FEED_URL}")
    print("Press 'q' or 'ESC' on the video window to quit.")
    
    # Initialize the video processor with the live camera URL
    # This automatically instantiates the core modules (Detector, Tracker, LaneManager, TrafficAnalyzer, SignalOptimizer)
    vp = VideoProcessor(video_path=LIVE_FEED_URL)
    
    # OVERRIDE: The VideoProcessor normally checks if the file exists using os.path.isfile()
    # For internet links, we directly assign the URL, otherwise, it forces webcam 0.
    vp.video_path = LIVE_FEED_URL
    
    # Start the processing threads
    vp.start()
    
    # Create the display window
    window_name = "Live AI Traffic Analysis - DroidCam"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    last_incident_time = time.time()
    
    try:
        while True:
            # Fetch the latest annotated frame
            frame = vp.latest_frame
            
            if frame is not None:
                cv2.imshow(window_name, frame)
                last_incident_time = check_and_send_incidents(vp, last_incident_time)
            
            # Wait 30ms and check for 'q' or 'Esc' key presses to exit
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:
                print("Exiting...")
                break
                
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        print("Stopping AI video processor and closing windows...")
        vp.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
