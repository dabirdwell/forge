"""
💡 NeoVak Progress Tracker v2
Real-time progress from ComfyUI websocket with accurate time estimates
"""

import json
import time
import threading
import queue
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass 
class GenerationProgress:
    """Progress state for a single generation."""
    status: str = "queued"  # queued, loading, sampling, completed, error
    current_step: int = 0
    total_steps: int = 0
    current_node: str = ""
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    error_message: str = ""
    
    # For time estimation
    _step_times: list = field(default_factory=list)
    _start_time: float = 0.0
    _last_step_time: float = 0.0
    
    def start(self):
        """Mark generation as started."""
        self._start_time = time.time()
        self._last_step_time = self._start_time
        self.status = "loading"
    
    def update_step(self, step: int, total: int):
        """Update step progress and recalculate time estimate."""
        now = time.time()
        
        # Track step timing
        if self.current_step > 0 and step > self.current_step:
            step_duration = now - self._last_step_time
            if 0.01 < step_duration < 120:  # Sanity check
                self._step_times.append(step_duration)
                # Keep recent samples for accuracy
                if len(self._step_times) > 5:
                    self._step_times = self._step_times[-5:]
        
        self._last_step_time = now
        self.current_step = step
        self.total_steps = total
        self.status = "sampling"
        
        # Update elapsed
        if self._start_time > 0:
            self.elapsed_seconds = now - self._start_time
        
        # Estimate remaining
        if self._step_times and total > step:
            avg_step_time = sum(self._step_times) / len(self._step_times)
            remaining_steps = total - step
            self.estimated_remaining_seconds = remaining_steps * avg_step_time
        elif step > 0 and self.elapsed_seconds > 0:
            # Fallback: linear estimate from elapsed
            time_per_step = self.elapsed_seconds / step
            remaining_steps = total - step
            self.estimated_remaining_seconds = remaining_steps * time_per_step
    
    def complete(self):
        """Mark as completed."""
        self.status = "completed"
        self.current_step = self.total_steps
        if self._start_time > 0:
            self.elapsed_seconds = time.time() - self._start_time
        self.estimated_remaining_seconds = 0
    
    def fail(self, message: str):
        """Mark as failed."""
        self.status = "error"
        self.error_message = message
    
    @property
    def progress_fraction(self) -> float:
        """Progress as 0.0-1.0."""
        if self.total_steps == 0:
            return 0.0
        return min(1.0, self.current_step / self.total_steps)
    
    def format_time(self, seconds: float) -> str:
        """Format seconds as human-readable."""
        if seconds < 60:
            return f"{int(seconds)}s"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    
    @property 
    def status_text(self) -> str:
        """Human-readable status for UI."""
        if self.status == "queued":
            return "⏳ Queued..."
        elif self.status == "loading":
            return "📦 Loading models..."
        elif self.status == "sampling":
            elapsed = self.format_time(self.elapsed_seconds)
            if self.total_steps > 0:
                remaining = self.format_time(self.estimated_remaining_seconds) if self.estimated_remaining_seconds > 0 else "..."
                return f"Step {self.current_step}/{self.total_steps} • {elapsed} elapsed • ~{remaining} left"
            return f"Processing... {elapsed}"
        elif self.status == "completed":
            return f"✓ Done in {self.format_time(self.elapsed_seconds)}"
        elif self.status == "error":
            return f"✗ {self.error_message[:60]}"
        return self.status


def track_generation_progress(
    comfyui_url: str,
    prompt_id: str,
    timeout: int = 600,
    on_progress: Optional[Callable[[GenerationProgress], None]] = None
) -> tuple[str, Optional[str], GenerationProgress]:
    """
    Track a ComfyUI generation with real-time progress.
    
    Returns: (status, output_path, progress)
    """
    import urllib.request
    
    progress = GenerationProgress()
    progress.start()
    
    # Try websocket for real-time updates
    ws_progress_queue = queue.Queue()
    ws_stop = threading.Event()
    
    def ws_listener():
        try:
            import websocket
            ws_url = comfyui_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    ws_progress_queue.put(data)
                except:
                    pass
            
            def on_error(ws, error):
                pass
            
            ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error)
            
            # Run in thread with stop check
            def run_ws():
                ws.run_forever()
            
            ws_thread = threading.Thread(target=run_ws, daemon=True)
            ws_thread.start()
            
            while not ws_stop.is_set():
                time.sleep(0.1)
            
            ws.close()
        except ImportError:
            pass  # websocket not available
        except Exception as e:
            pass
    
    # Start websocket listener
    ws_thread = threading.Thread(target=ws_listener, daemon=True)
    ws_thread.start()
    
    start_time = time.time()
    output_path = None
    final_status = "timeout"
    
    while time.time() - start_time < timeout:
        # Process any websocket messages
        try:
            while True:
                msg = ws_progress_queue.get_nowait()
                msg_type = msg.get("type", "")
                msg_data = msg.get("data", {})
                
                if msg_type == "execution_start":
                    if msg_data.get("prompt_id") == prompt_id:
                        progress.status = "loading"
                        if on_progress:
                            on_progress(progress)
                
                elif msg_type == "executing":
                    if msg_data.get("prompt_id") == prompt_id:
                        node = msg_data.get("node")
                        if node:
                            progress.current_node = node
                            if on_progress:
                                on_progress(progress)
                
                elif msg_type == "progress":
                    # Real step progress from KSampler
                    value = msg_data.get("value", 0)
                    max_val = msg_data.get("max", 0)
                    if max_val > 0:
                        progress.update_step(value, max_val)
                        if on_progress:
                            on_progress(progress)
                
                elif msg_type == "execution_error":
                    if msg_data.get("prompt_id") == prompt_id:
                        progress.fail(msg_data.get("exception_message", "Unknown error"))
                        if on_progress:
                            on_progress(progress)
                        ws_stop.set()
                        return "error", None, progress
                        
        except queue.Empty:
            pass
        
        # Poll history for completion
        try:
            req = urllib.request.Request(f"{comfyui_url}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                history = json.loads(resp.read().decode())
            
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                
                if status.get("status_str") == "error":
                    messages = status.get("messages", [])
                    error_msg = "Unknown error"
                    for msg in messages:
                        if msg[0] == "execution_error":
                            error_msg = msg[1].get("exception_message", error_msg)
                    progress.fail(error_msg)
                    if on_progress:
                        on_progress(progress)
                    ws_stop.set()
                    return "error", None, progress
                
                if status.get("completed"):
                    # Find output file
                    for node_out in entry.get("outputs", {}).values():
                        # Images
                        for img in node_out.get("images", []):
                            if "filename" in img:
                                output_path = img["filename"]
                                subfolder = img.get("subfolder", "")
                                if subfolder:
                                    output_path = f"{subfolder}/{output_path}"
                                progress.complete()
                                if on_progress:
                                    on_progress(progress)
                                ws_stop.set()
                                return "completed", output_path, progress
                        
                        # Videos/GIFs
                        for vid in node_out.get("gifs", []):
                            if "filename" in vid:
                                output_path = vid["filename"]
                                subfolder = vid.get("subfolder", "")
                                if subfolder:
                                    output_path = f"{subfolder}/{output_path}"
                                progress.complete()
                                if on_progress:
                                    on_progress(progress)
                                ws_stop.set()
                                return "completed", output_path, progress
                    
                    # Completed but no output found
                    progress.complete()
                    ws_stop.set()
                    return "completed", None, progress
                    
        except Exception as e:
            pass
        
        # Update elapsed time even without step progress
        if progress._start_time > 0:
            progress.elapsed_seconds = time.time() - progress._start_time
            if on_progress and progress.status in ("loading", "sampling"):
                on_progress(progress)
        
        time.sleep(0.5)
    
    # Timeout
    ws_stop.set()
    progress.fail("Generation timed out")
    return "timeout", None, progress
