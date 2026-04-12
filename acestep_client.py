"""
ACE-Step 1.5 REST API Client for NeoVak.
Talks to the ACE-Step API server (default: http://localhost:8001).
"""

import json
import time
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

import requests

from neovak_backend import OUTPUT_DIR


def check_acestep_backend(url: str = "http://localhost:8001") -> tuple[bool, str]:
    """Check if ACE-Step API server is running."""
    try:
        r = requests.get(f"{url}/health", timeout=5)
        r.raise_for_status()
        data = r.json().get("data", {})
        if data.get("status") == "ok":
            model = data.get("loaded_model", "unknown")
            llm = "LM ready" if data.get("llm_initialized") else "no LM"
            return True, f"Connected — {model} ({llm})"
        return False, "Server responded but status not ok"
    except requests.ConnectionError:
        return False, "ACE-Step server not running (port 8001)"
    except Exception as e:
        return False, f"ACE-Step check failed: {e}"


def get_acestep_status(url: str = "http://localhost:8001") -> dict:
    """GET /v1/stats — server load, queue depth, avg job time."""
    try:
        r = requests.get(f"{url}/v1/stats", timeout=5)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception:
        return {}


def format_input(
    url: str,
    caption: str,
    lyrics: str = ""
) -> dict:
    """POST /format_input — Use LM to expand short tags into full captions/lyrics."""
    try:
        r = requests.post(
            f"{url}/format_input",
            json={"caption": caption, "lyrics": lyrics},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        return {"caption": data.get("caption", caption), "lyrics": data.get("lyrics", lyrics)}
    except Exception as e:
        return {"caption": caption, "lyrics": lyrics, "error": str(e)}


def generate_music(
    url: str,
    caption: str,
    lyrics: str = "",
    duration: int = 120,
    seed: int = -1,
    thinking: bool = True,
    batch_size: int = 1,
    infer_step: int = 30,
    guidance_scale: float = 15.0,
    guidance_scale_text: float = 0.0,
    guidance_scale_lyric: float = 0.0,
    model: str = "",
    lm_model: str = "",
    audio_path: str = "",
    repaint_start: float = 0.0,
    repaint_end: float = 0.0,
    progress_callback=None,
) -> tuple[Optional[str], str]:
    """
    Submit a music generation task and poll for result.
    Returns: (output_path, status_message)
    """
    if progress_callback:
        progress_callback(5, "Submitting to ACE-Step...")

    payload = {
        "caption": caption,
        "lyrics": lyrics,
        "duration": duration,
        "infer_step": infer_step,
        "guidance_scale": guidance_scale,
        "guidance_scale_text": guidance_scale_text,
        "guidance_scale_lyric": guidance_scale_lyric,
        "seed": seed,
        "batch_size": batch_size,
        "thinking": thinking,
    }
    if model:
        payload["model"] = model
    if lm_model:
        payload["lm_model"] = lm_model
    if audio_path:
        payload["audio_path"] = audio_path
        payload["repaint_start"] = repaint_start
        payload["repaint_end"] = repaint_end

    # Step 1: Submit task
    try:
        r = requests.post(f"{url}/release_task", json=payload, timeout=30)
        r.raise_for_status()
        resp = r.json()
    except requests.ConnectionError:
        return None, "ACE-Step server not running"
    except Exception as e:
        return None, f"Failed to submit task: {e}"

    task_id = resp.get("data", {}).get("task_id")
    if not task_id:
        return None, f"No task_id in response: {resp}"

    if progress_callback:
        progress_callback(10, "Queued, generating...")

    # Step 2: Poll for result
    poll_interval = 2.0
    max_wait = max(duration * 4, 120)
    elapsed = 0.0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        try:
            r = requests.post(
                f"{url}/query_result",
                json={"task_id_list": [task_id]},
                timeout=15,
            )
            r.raise_for_status()
            results = r.json().get("data", [])
        except Exception:
            continue

        if not results:
            continue

        item = results[0]
        status = item.get("status", 0)
        progress_text = item.get("progress_text", "")

        if progress_callback and progress_text:
            pct = min(10 + int(elapsed / max_wait * 80), 90)
            progress_callback(pct, progress_text)

        if status == 0:
            continue
        elif status == 2:
            return None, f"Generation failed: {progress_text}"
        elif status == 1:
            # Completed — parse the double-encoded result
            result_raw = item.get("result", "")
            try:
                result_list = json.loads(result_raw) if isinstance(result_raw, str) else result_raw
            except json.JSONDecodeError:
                return None, f"Failed to parse result JSON"

            if not result_list:
                return None, "Empty result from ACE-Step"

            first = result_list[0]
            file_url = first.get("file", "")
            metas = first.get("metas", {})
            seed_val = first.get("seed_value", "")
            gen_info = first.get("generation_info", "")

            if not file_url:
                return None, "No file URL in result"

            # Step 3: Download audio
            if progress_callback:
                progress_callback(92, "Downloading audio...")

            try:
                audio_r = requests.get(f"{url}{file_url}", timeout=60)
                audio_r.raise_for_status()
            except Exception as e:
                return None, f"Failed to download audio: {e}"

            # Save to output dir
            music_dir = OUTPUT_DIR / "music"
            music_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neovak_music_{ts}_seed{seed_val}.mp3"
            output_path = music_dir / filename

            with open(output_path, "wb") as f:
                f.write(audio_r.content)

            if progress_callback:
                progress_callback(100, "Done!")

            bpm = metas.get("bpm", "?")
            key = metas.get("keyscale", "?")
            dur = metas.get("duration", duration)
            status_msg = f"Generated {dur:.0f}s | {key} | {bpm} BPM | seed {seed_val}"
            if gen_info:
                status_msg += f" | {gen_info}"

            return str(output_path), status_msg

    return None, f"Timed out after {max_wait}s"
