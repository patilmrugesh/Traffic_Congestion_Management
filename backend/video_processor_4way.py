"""
backend/video_processor_4way.py — Multi-Camera Video Processing Pipeline
======================================================================
"""

import cv2
import numpy as np
import threading
import time
import base64
import json
import os
import sys
from typing import Callable, Optional, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from core.detector   import Detector
from core.tracker    import CentroidTracker
from core.lane_manager  import LaneManager
from core.traffic_analyzer import TrafficAnalyzer
from core.signal_optimizer import SignalOptimizer

LANE_POLYGONS_4WAY = {
    "North": [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)],
    "South": [(0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (0.5, 0.5)],
    "East":  [(0.0, 0.5), (0.5, 0.5), (0.5, 1.0), (0.0, 1.0)],
    "West":  [(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)],
}

class VideoProcessor4Way:
    def __init__(self, v_north="north.mp4", v_south="south.mp4", v_east="east.mp4", v_west="west.mp4", frame_width=None, frame_height=None):
        self.v_paths = [self._resolve_video(v) for v in [v_north, v_south, v_east, v_west]]
        self.frame_width  = frame_width  or config.FRAME_WIDTH
        self.frame_height = frame_height or config.FRAME_HEIGHT
        
        self.detector  = Detector()
        self.tracker   = CentroidTracker(max_disappeared=8, max_distance=100)
        self.lane_mgr  = LaneManager(self.frame_width, self.frame_height, polygons=LANE_POLYGONS_4WAY)
        self.analyzer  = TrafficAnalyzer()
        self.optimizer = SignalOptimizer()
        
        self.is_running = False
        self._capture_thread_obj: Optional[threading.Thread] = None
        self._inference_thread_obj: Optional[threading.Thread] = None
        
        self.quadrant_mapping = [0, 1, 2, 3] # Default N, S, E, W
        
        self.state_lock = threading.Lock()
        self.raw_frame: Optional[np.ndarray] = None
        self.shared_detections: List = []
        self.shared_tracks: List = []
        self.shared_lane_stats: Dict = {}
        
        self.latest_frame:   Optional[np.ndarray] = None
        self.latest_metrics: Dict = {}
        self.latest_alerts:  List = []
        self.latest_signals: Dict = {}
        self.latest_signals: Dict = {}
        self.incident_history: List[Dict] = []
        self._last_incident_time: float = 0.0
        self._on_state: Optional[Callable] = None

    def _resolve_video(self, path=None) -> str:
        candidates = [path, config.VIDEO_PATH] + config.FALLBACK_VIDEO_PATHS
        for c in candidates:
            if c is None: continue
            if c == 0: return 0
            if os.path.isfile(str(c)): return c
        return 0

    def start(self, on_state: Optional[Callable] = None):
        self._on_state = on_state
        self.is_running = True
        self._capture_thread_obj = threading.Thread(target=self._capture_thread, daemon=True)
        self._inference_thread_obj = threading.Thread(target=self._inference_thread, daemon=True)
        self._capture_thread_obj.start()
        self._inference_thread_obj.start()
        print("[4-Way Processor] Started threads.")

    def stop(self):
        self.is_running = False
        if self._capture_thread_obj: self._capture_thread_obj.join(timeout=3.0)
        if self._inference_thread_obj: self._inference_thread_obj.join(timeout=3.0)

    def draw_quadrant_signals(self, frame, optimizer_signals, qw, qh):
        positions = {"North": (20, 60), "South": (qw + 20, 60), "East": (20, qh + 40), "West": (qw + 20, qh + 40)}
        STATE_COLORS = {"green": (0,220,100), "yellow": (0,200,255), "red": (80,80,80)}
        for lane_name, pos in positions.items():
            if lane_name not in optimizer_signals: continue
            sig = optimizer_signals[lane_name]
            state_str = sig.state.value
            color = STATE_COLORS.get(state_str, (80,80,80))
            x, y = pos
            cv2.rectangle(frame, (x-10, y-20), (x+130, y+20), (20,20,20), -1)
            cv2.rectangle(frame, (x-10, y-20), (x+130, y+20), (80,80,80), 1)
            cv2.circle(frame, (x+12, y), 10, color, -1)
            time_txt = f" {sig.time_left:.0f}s" if state_str in ("green", "yellow") else ""
            cv2.putText(frame, f"{state_str.upper()}{time_txt}", (x+30, y+6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    def _capture_thread(self):
        caps = [cv2.VideoCapture(v) for v in self.v_paths]
        qw, qh = self.frame_width // 2, self.frame_height // 2
        frame_delay = 1.0 / config.TARGET_FPS

        while self.is_running:
            start_time = time.time()
            frames = []
            for c in caps:
                ret, f = c.read()
                if not ret:
                    c.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, f = c.read()
                frames.append(cv2.resize(f, (qw, qh)))

            with self.state_lock:
                q_map = list(self.quadrant_mapping)

            mapped_frames = [frames[q_map[i]] for i in range(4)]
            top_row = np.hstack((mapped_frames[0], mapped_frames[1]))
            bot_row = np.hstack((mapped_frames[2], mapped_frames[3]))
            composite = np.vstack((top_row, bot_row))

            with self.state_lock:
                self.raw_frame = composite.copy()
                current_detections = list(self.shared_detections)
                current_tracks = list(self.shared_tracks)
                current_lane_stats = dict(self.shared_lane_stats)
                self.latest_metrics = self.analyzer.metrics
                self.latest_alerts  = [a.to_dict() for a in self.analyzer.alerts[-5:]]
                self.latest_signals = self.optimizer.get_metrics()
                
            annotated = composite.copy()
            self.lane_mgr.draw_lanes(annotated)
            if current_detections: self.detector.draw(annotated, current_detections)
            if current_tracks: self.tracker.draw_tracks(annotated, current_tracks)
            
            self.optimizer.draw_signal_panel(annotated, x=10, y=10)
            self.draw_quadrant_signals(annotated, self.optimizer.signals, qw, qh)
            
            self.latest_frame = annotated
            
            # ── Incident Detection Pipeline ──
            now = time.time()
            if now - self._last_incident_time > 10.0:  # 10s cooldown between captured incidents
                detected_incidents = []
                
                person_count = sum(1 for t in current_tracks if t.is_person)
                
                # Check for critical/high alerts from the analyzer
                critical_alerts = [a for a in self.latest_alerts if a['severity'] in ('critical', 'high')]
                
                if critical_alerts:
                    for a in critical_alerts:
                        if a.get("type") == "accident" or a.get("type") == "scene" or a.get("type") == "stall":
                            # Use exact type field name 'accident'
                            pass
                        if a.get("type") == "accident" or a.get("alert_type") == "accident":
                            detected_incidents.append({
                                "type": "accident",
                                "description": a["message"]
                            })
                            break
                        elif "AMBULANCE" in a["message"]:
                            detected_incidents.append({
                                "type": "ambulance",
                                "description": f"Ambulance detected passing through {a['lane']} lane."
                            })
                            break
                
                # Check for Crowd
                if person_count > 12:
                    detected_incidents.append({
                                "type": "crowd",
                                "description": f"Large crowd of {person_count} pedestrians crossing."
                    })
                
                # Check for Suspicious Stalls
                is_accident_running = any(idx['type'] == 'accident' for idx in detected_incidents)
                if not is_accident_running:
                    for lane, stats in current_lane_stats.items():
                        if stats.max_wait_time > 120.0: # 2 minutes
                            detected_incidents.append({
                                "type": "parking",
                                "description": f"Potential stalled or illegally parked vehicle in {lane} lane."
                            })
                            break
                
                if detected_incidents:
                    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    b64_frame = base64.b64encode(buf.tobytes()).decode("utf-8")
                    with self.state_lock:
                        for inc in detected_incidents:
                            self.incident_history.insert(0, {
                                "type": inc["type"],
                                "description": inc["description"],
                                "timestamp": now,
                                "frame_b64": b64_frame
                            })
                        # Keep only the last 15 incidents in memory
                        while len(self.incident_history) > 15:
                            self.incident_history.pop()
                    self._last_incident_time = now
            # ─────────────────────────────────
            
            if self._on_state:
                try:
                    self._on_state({
                        "metrics": self.latest_metrics,
                        "alerts":  self.latest_alerts,
                        "signals": self.latest_signals,
                        "chart":   self.analyzer.get_chart_data(),
                    })
                except Exception: pass
            
            elapsed = time.time() - start_time
            time.sleep(max(0, frame_delay - elapsed))
            
        for c in caps: c.release()

    def _inference_thread(self):
        while self.is_running:
            with self.state_lock: frame_to_process = self.raw_frame
            if frame_to_process is None: time.sleep(0.01); continue
            
            detections = self.detector.detect(frame_to_process)
            tracks = self.tracker.update(detections)
            lane_stats = self.lane_mgr.update(tracks)
            
            self.optimizer.update_phase_duration(lane_stats)
            self.optimizer.update(lane_stats)
            self.analyzer.update(tracks, lane_stats, list(detections))
            
            with self.state_lock:
                self.shared_detections, self.shared_tracks, self.shared_lane_stats = detections, tracks, lane_stats
            time.sleep(0.01)

    def get_jpeg_frame(self, quality: int = None) -> Optional[bytes]:
        if self.latest_frame is None: return None
        _, buf = cv2.imencode(".jpg", self.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, quality or config.STREAM_JPEG_QUALITY])
        return buf.tobytes()
        
    def get_b64_frame(self) -> str:
        jpg = self.get_jpeg_frame()
        return base64.b64encode(jpg).decode("utf-8") if jpg else None

    def get_state(self) -> Dict:
        return {
            "metrics": self.latest_metrics, "alerts": self.latest_alerts,
            "signals": self.latest_signals, "chart": self.analyzer.get_chart_data(),
            "frame_b64": self.get_b64_frame(),
        }

    def get_incident_history(self) -> List[Dict]:
        with self.state_lock:
            return list(self.incident_history)

    def set_quadrant_mapping(self, mapping: List[int]):
        if len(mapping) == 4:
            with self.state_lock:
                self.quadrant_mapping = mapping
