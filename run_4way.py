"""
run_4way.py — Launcher for the 4-Way Split Screen Web Dashboard
================================================================
Usage:
  python run_4way.py --v_north north.mp4 --v_south south.mp4 --v_east east.mp4 --v_west west.mp4
"""

import subprocess
import sys
import os
import time
import argparse
import webbrowser
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def open_browser(port: int, delay: float = 2.5):
    def _open():
        time.sleep(delay)
        url = f"http://localhost:{port}"
        print(f"[Launcher] Opening dashboard: {url}")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

def parse_args():
    parser = argparse.ArgumentParser(description="AI Traffic 4-Way Dashboard")
    parser.add_argument("--v_north", type=str, default="north.mp4", help="Path to North video")
    parser.add_argument("--v_south", type=str, default="west1.mp4", help="Path to South video")
    parser.add_argument("--v_east", type=str, default="south.mp4", help="Path to East video")
    parser.add_argument("--v_west", type=str, default="west.mp4", help="Path to West video")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    return parser.parse_args()

def main():
    args = parse_args()
    print("\n" + "="*60 + "\n   AI Traffic De-Congestion System - 4-Way Web Dashboard\n" + "="*60)
    
    if not args.no_browser: open_browser(args.port)
    
    import uvicorn
    from backend import main_4way
    main_4way.init_processor(args.v_north, args.v_south, args.v_east, args.v_west)
    
    uvicorn.run(main_4way.app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
