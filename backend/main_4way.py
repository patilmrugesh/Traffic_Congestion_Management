"""
backend/main_4way.py — FastAPI Server with 4-Way WebSocket Dashboard
"""
import asyncio
import os
import sys
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from backend.video_processor_4way import VideoProcessor4Way

app = FastAPI(title="AI Traffic 4-Way Dashboard", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

processor: VideoProcessor4Way = None
active_websockets: Set[WebSocket] = set()
main_event_loop: asyncio.AbstractEventLoop = None

def init_processor(v_north, v_south, v_east, v_west):
    global processor
    processor = VideoProcessor4Way(v_north, v_south, v_east, v_west)

@app.on_event("startup")
async def startup():
    global main_event_loop
    main_event_loop = asyncio.get_event_loop()
    def on_state(state: dict):
        if main_event_loop and main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(state), main_event_loop)
    if processor:
        processor.start(on_state=on_state)

@app.on_event("shutdown")
async def shutdown():
    if processor: processor.stop()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    active_websockets.add(ws)
    try:
        while True:
            await asyncio.sleep(0.033)
            if processor and processor.latest_metrics:
                try: await ws.send_json(processor.get_state())
                except Exception: break
    except WebSocketDisconnect: pass
    finally: active_websockets.discard(ws)

async def broadcast(state: dict):
    dead = set()
    for ws in list(active_websockets):
        try: await ws.send_json(state)
        except Exception: dead.add(ws)
    active_websockets -= dead

assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web-dashboard", "dist", "assets")
dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web-dashboard", "dist")
if os.path.exists(assets_path): app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/vite.svg")
async def serve_vite_svg():
    svg_path = os.path.join(dist_path, "vite.svg")
    if os.path.exists(svg_path): return FileResponse(svg_path)
    return HTMLResponse(status_code=404)

@app.get("/")
async def index():
    frontend_path = os.path.join(dist_path, "index.html")
    if os.path.exists(frontend_path):
        resp = FileResponse(frontend_path)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    return HTMLResponse("<h1>React Dashboard not built yet.</h1>", status_code=404)

@app.get("/api/frame")
async def api_frame():
    from fastapi.responses import Response
    if processor:
        jpg = processor.get_jpeg_frame()
        if jpg: return Response(content=jpg, media_type="image/jpeg")
    return Response(status_code=204)
@app.get("/api/incidents")
async def api_incidents():
    """Returns the latest captured incident snapshots (Crowd, Ambulance, Accident, Parking)."""
    if processor:
        if hasattr(processor, "get_incident_history"):
            return JSONResponse(processor.get_incident_history())
        elif hasattr(processor, "incident_history"):
            return JSONResponse(list(processor.incident_history))
    return JSONResponse([])

from pydantic import BaseModel
class SwapRequest(BaseModel):
    mapping: list[int]

@app.post("/api/swap-video")
async def api_swap_video(req: SwapRequest):
    if processor and hasattr(processor, "set_quadrant_mapping"):
        processor.set_quadrant_mapping(req.mapping)
    return {"status": "ok"}

class IncidentReport(BaseModel):
    type: str
    description: str
    timestamp: float
    frame_b64: str

@app.post("/api/add-incident")
async def api_add_incident(inc: IncidentReport):
    if processor:
        try:
            with processor.state_lock:
                if not hasattr(processor, "incident_history"):
                    processor.incident_history = []
                processor.incident_history.insert(0, inc.model_dump() if hasattr(inc, "model_dump") else inc.dict())
                if len(processor.incident_history) > 15:
                    processor.incident_history.pop()
        except AttributeError:
            pass  # Fallback if standard processor is lacking history
    return {"status": "ok"}

@app.post("/api/open-live-camera")
async def api_open_live_camera():
    global processor, main_event_loop
    
    LIVE_FEED_URL = config.LIVE_FEED_URL
    
    # 1. Stop the current 4-way processor safely
    if processor:
        processor.stop()
    await asyncio.sleep(0.5)  # brief wait for thread cleanup
    
    # 2. Swap to the single live video processor and bind it to our active websocket output
    from backend.video_processor import VideoProcessor
    processor = VideoProcessor(video_path=LIVE_FEED_URL)
    processor.video_path = LIVE_FEED_URL
    
    def on_state(state: dict):
        if main_event_loop and main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(state), main_event_loop)
            
    processor.start(on_state=on_state)
    return {"status": "switched_to_live"}

@app.post("/api/close-live-camera")
async def api_close_live_camera():
    global processor, main_event_loop
    
    if processor:
        processor.stop()
    await asyncio.sleep(0.5)
    
    from backend.video_processor_4way import VideoProcessor4Way
    processor = VideoProcessor4Way("north.mp4", "south.mp4", "east.mp4", "west.mp4")
    
    def on_state(state: dict):
        if main_event_loop and main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(state), main_event_loop)
            
    processor.start(on_state=on_state)
    return {"status": "switched_to_4way"}

