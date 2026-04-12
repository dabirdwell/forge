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
    task_type: str = "text2music",
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
    if task_type != "text2music":
        payload["task_type"] = task_type
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

            bpm = metas.get("bpm", "?")
            key = metas.get("keyscale", "?")
            dur = metas.get("duration", duration)

            try:
                embed_metadata(
                    str(output_path), caption, lyrics,
                    str(seed_val), str(bpm), str(key), float(dur),
                    model=model, lm_model=lm_model,
                )
            except Exception:
                pass

            if progress_callback:
                progress_callback(100, "Done!")

            status_msg = f"Generated {dur:.0f}s | {key} | {bpm} BPM | seed {seed_val}"
            if gen_info:
                status_msg += f" | {gen_info}"

            return str(output_path), status_msg

    return None, f"Timed out after {max_wait}s"


def get_random_sample(url: str = "http://localhost:8001") -> dict:
    """POST /create_random_sample — get random song params for UI form filling."""
    r = requests.post(f"{url}/create_random_sample", timeout=30)
    r.raise_for_status()
    return r.json().get("data", {})


def generate_music_batch(
    url: str,
    caption: str,
    lyrics: str = "",
    duration: int = 120,
    batch_size: int = 4,
    thinking: bool = True,
    infer_step: int = 30,
    guidance_scale: float = 15.0,
    guidance_scale_text: float = 0.0,
    guidance_scale_lyric: float = 0.0,
    model: str = "",
    lm_model: str = "",
    progress_callback=None,
) -> list[dict]:
    """Generate multiple variations with different seeds (batch_size>1).
    Returns list of dicts: {path, seed, status, metas}.
    """
    if progress_callback:
        progress_callback(5, "Submitting batch to ACE-Step...")

    payload = {
        "caption": caption,
        "lyrics": lyrics,
        "duration": duration,
        "infer_step": infer_step,
        "guidance_scale": guidance_scale,
        "guidance_scale_text": guidance_scale_text,
        "guidance_scale_lyric": guidance_scale_lyric,
        "seed": -1,
        "batch_size": batch_size,
        "thinking": thinking,
    }
    if model:
        payload["model"] = model
    if lm_model:
        payload["lm_model"] = lm_model

    try:
        r = requests.post(f"{url}/release_task", json=payload, timeout=30)
        r.raise_for_status()
        resp = r.json()
    except Exception as e:
        return [{"path": None, "seed": "", "status": f"Failed: {e}", "metas": {}}]

    task_id = resp.get("data", {}).get("task_id")
    if not task_id:
        return [{"path": None, "seed": "", "status": "No task_id", "metas": {}}]

    if progress_callback:
        progress_callback(10, "Batch queued, generating...")

    poll_interval = 3.0
    max_wait = max(duration * 6, 180)
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
            return [{"path": None, "seed": "", "status": f"Failed: {progress_text}", "metas": {}}]
        elif status == 1:
            result_raw = item.get("result", "")
            try:
                result_list = json.loads(result_raw) if isinstance(result_raw, str) else result_raw
            except json.JSONDecodeError:
                return [{"path": None, "seed": "", "status": "Failed to parse result", "metas": {}}]

            if not result_list:
                return [{"path": None, "seed": "", "status": "Empty result", "metas": {}}]

            if progress_callback:
                progress_callback(92, "Downloading batch audio...")

            music_dir = OUTPUT_DIR / "music"
            music_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            outputs = []

            for i, entry in enumerate(result_list):
                file_url = entry.get("file", "")
                seed_val = entry.get("seed_value", "")
                metas = entry.get("metas", {})

                if not file_url:
                    outputs.append({"path": None, "seed": seed_val, "status": "No file URL", "metas": metas})
                    continue

                try:
                    audio_r = requests.get(f"{url}{file_url}", timeout=60)
                    audio_r.raise_for_status()
                except Exception as e:
                    outputs.append({"path": None, "seed": seed_val, "status": f"Download failed: {e}", "metas": metas})
                    continue

                filename = f"neovak_music_{ts}_batch{i}_seed{seed_val}.mp3"
                output_path = music_dir / filename
                with open(output_path, "wb") as f:
                    f.write(audio_r.content)

                bpm = metas.get("bpm", "?")
                key = metas.get("keyscale", "?")
                outputs.append({
                    "path": str(output_path),
                    "seed": str(seed_val),
                    "status": f"{key} | {bpm} BPM | seed {seed_val}",
                    "metas": metas,
                })

            if progress_callback:
                progress_callback(100, f"Done! {len(outputs)} variations")
            return outputs

    return [{"path": None, "seed": "", "status": f"Timed out after {max_wait}s", "metas": {}}]


def get_model_inventory(url: str = "http://localhost:8001") -> dict:
    """GET /v1/model_inventory — available DiT and LM models."""
    r = requests.get(f"{url}/v1/model_inventory", timeout=10)
    r.raise_for_status()
    return r.json().get("data", {})


def embed_metadata(filepath: str, caption: str, lyrics: str,
                   seed: str, bpm: str, key: str, duration: float,
                   model: str = "", lm_model: str = ""):
    """Embed generation metadata into MP3 ID3 tags."""
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TALB, TPE1, COMM, TKEY, TBPM, USLT
    except ImportError:
        return
    audio = MP3(filepath, ID3=ID3)
    try:
        audio.add_tags()
    except Exception:
        pass
    audio.tags.add(TIT2(encoding=3, text=caption[:60]))
    audio.tags.add(TALB(encoding=3, text="NeoVak Generated"))
    audio.tags.add(TPE1(encoding=3, text="NeoVak + ACE-Step 1.5"))
    if str(bpm).isdigit():
        audio.tags.add(TBPM(encoding=3, text=str(bpm)))
    if key and key != "?":
        audio.tags.add(TKEY(encoding=3, text=key))
    if lyrics:
        audio.tags.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=lyrics))
    audio.tags.add(COMM(encoding=3, lang='eng', desc='NeoVak',
        text=f"seed={seed} model={model} lm={lm_model} duration={duration}s"))
    audio.save()


def embed_album_art(mp3_path: str, image_path: str) -> bool:
    """Embed album art image into MP3 file."""
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, APIC
    except ImportError:
        return False
    audio = MP3(mp3_path, ID3=ID3)
    try:
        audio.add_tags()
    except Exception:
        pass
    with open(image_path, 'rb') as f:
        img_data = f.read()
    mime = 'image/png' if image_path.lower().endswith('.png') else 'image/jpeg'
    audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=img_data))
    audio.save()
    return True


def get_lora_status(url: str = "http://localhost:8001") -> dict:
    """GET /v1/lora/status — current LoRA state."""
    try:
        r = requests.get(f"{url}/v1/lora/status", timeout=5)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception:
        return {}


def load_lora(url: str, lora_path: str) -> tuple[bool, str]:
    """POST /v1/lora/load — load a LoRA adapter."""
    try:
        r = requests.post(f"{url}/v1/lora/load",
                          json={"lora_path": lora_path}, timeout=30)
        r.raise_for_status()
        return True, "LoRA loaded"
    except Exception as e:
        return False, str(e)


def unload_lora(url: str) -> tuple[bool, str]:
    """POST /v1/lora/unload — unload current LoRA."""
    try:
        r = requests.post(f"{url}/v1/lora/unload", json={}, timeout=10)
        r.raise_for_status()
        return True, "LoRA unloaded"
    except Exception as e:
        return False, str(e)


def set_lora_scale(url: str, scale: float) -> bool:
    """POST /v1/lora/scale — adjust LoRA influence (0.0–1.0)."""
    try:
        r = requests.post(f"{url}/v1/lora/scale", json={"scale": scale}, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def toggle_lora(url: str, enabled: bool) -> bool:
    """POST /v1/lora/toggle — enable/disable LoRA without unloading."""
    try:
        r = requests.post(f"{url}/v1/lora/toggle", json={"use_lora": enabled}, timeout=5)
        return r.status_code == 200
    except Exception:
        return False
