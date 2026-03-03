"""
AI Traffic De-Congestion System — Configuration
================================================
Edit these values to match your camera setup and preferences.
"""

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Primary video — user-provided traffic footage
VIDEO_PATH = os.path.join(BASE_DIR, "videoplayback.mp4")
FALLBACK_VIDEO_PATHS = [
    os.path.join(BASE_DIR, "..", "yolov8-multiple-vehicle-detection", "tf.mp4"),
    os.path.join(BASE_DIR, "..", "SynchroFlow--Smart-Traffic-Management-System-main", "video3.mp4"),
    0,  # webcam
]

# YOLO model — yolov8n is fastest, yolov8s is a good balance
MODEL_NAME = "yolov8n.pt"  # Will auto-download if not present

# ─── Video Processing ─────────────────────────────────────────────────────────
FRAME_WIDTH  = 1280
FRAME_HEIGHT = 720
TARGET_FPS   = 30
PROCESS_EVERY_N_FRAMES = 2      # Skip every other frame for speed
CONFIDENCE_THRESHOLD   = 0.30  # Detection confidence minimum

# ─── COCO Class IDs (YOLOv8 default) ─────────────────────────────────────────
VEHICLE_CLASSES = {
    2:  "car",
    3:  "motorcycle",
    5:  "bus",
    7:  "truck",
    0:  "person",        # Pedestrian
}
AMBULANCE_CLASS_KEYWORDS = ["ambulance"]  # substring match in class name

# ─── Vehicle Density Weights ─────────────────────────────────────────────────
# Heavy vehicles take longer to accelerate and clear intersections.
# We multiply their geometric bbox density by these factors to ensure fairness.
VEHICLE_WEIGHTS = {
    "motorcycle": 0.5,
    "car":        1.0,
    "bus":        3.0,
    "truck":      2.5,
    "person":     1.0,  # Irrelevant, pedestrians don't trigger vehicle logic
    "ambulance":  0.0,  # Ambulances have a flat emergency override anyway
}

# ─── Lane Polygon Definitions (normalized 0–1 coordinates) ───────────────────
# These define 4 virtual lanes at a 4-way intersection.
# Format: list of (x_norm, y_norm) points for each lane quadrant.
# 2 lanes: North (top half of frame) and South (bottom half)
# Adjust x-ranges if needed based on your camera angle
LANE_POLYGONS = {
    "North": [(0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0)],
    "South": [(0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)],
}

# ─── Signal Timing ────────────────────────────────────────────────────────────
BASE_GREEN_TIME    = 10   # Minimum green time in seconds
GREEN_PER_VEHICLE  = 2    # Extra seconds per vehicle in queue
MAX_GREEN_TIME     = 45   # Cap to prevent starvation on other lanes
MIN_GREEN_TIME     = 5    # Minimum even if queue is empty
MAX_WAIT_TIME      = 60   # Force green if a lane has waited this long (fairness)
YELLOW_DURATION    = 3    # Yellow light duration in seconds

# ─── Emergency / Accident ────────────────────────────────────────────────────
AMBULANCE_OVERRIDE      = True   # Enable emergency preemption
ACCIDENT_STOP_THRESHOLD = 4.0   # Seconds a vehicle is stopped before flagged
ACCIDENT_OVERLAP_IOU    = 0.15  # IoU threshold to flag collision (lower = more sensitive)
COLLISION_CONFIRM_TIME  = 5.0   # Seconds both vehicles must stay stopped after collision to confirm accident

# ─── Backend Server ───────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000
OPEN_BROWSER_ON_START = True

# ─── Dashboard ────────────────────────────────────────────────────────────────
DASHBOARD_TITLE = "AI Traffic De-Congestion System"
STREAM_JPEG_QUALITY = 75  # JPEG compression quality for streaming (1–100)

# ─── Camera Sources ──────────────────────────────────────────────────────────
# Use the user-provided camera URLs here.
LIVE_FEED_URL = "http://10.197.135.215:8080/video"
# Alternatives:
# LIVE_FEED_URL = "https://10.197.135.215:8080/video"
# LIVE_FEED_URL = "http://[2409:4102:6017:f767:ac11:49ff:fe87:679e]:8080/video"