"""
🔥 Forge Backend - Shared AI Generation Infrastructure
Framework-agnostic code for model discovery and ComfyUI integration.

This file is used by both forge_nicegui.py (active) and forge_v2.py (deprecated).
"""

import os
import json
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION (Environment Variable Overrides)
# ═══════════════════════════════════════════════════════════════════════════════

FORGE_DIR = Path(__file__).parent
OUTPUT_DIR = Path(os.environ.get('FORGE_OUTPUT_DIR', FORGE_DIR / "output"))
WORKFLOWS_DIR = Path(os.environ.get('FORGE_WORKFLOWS_DIR', FORGE_DIR / "workflows"))
OUTPUT_DIR.mkdir(exist_ok=True)

# ComfyUI backend URL - can be overridden with COMFYUI_URL env var
COMFYUI_URL = os.environ.get('COMFYUI_URL', "http://127.0.0.1:8188")

# Model search paths - extend via FORGE_MODEL_PATHS (colon-separated)
_default_model_paths = [
    Path.home() / ".comfyui" / "models",
    Path.home() / "ComfyUI" / "models",
    FORGE_DIR / "models",
]

# Add any paths from environment
_extra_paths = os.environ.get('FORGE_MODEL_PATHS', '')
if _extra_paths:
    for p in _extra_paths.split(':'):
        if p:
            _default_model_paths.append(Path(p))

# Users can add additional model paths via FORGE_MODEL_PATHS environment variable
# Example: export FORGE_MODEL_PATHS="/path/to/models:/another/path"

MODEL_SEARCH_PATHS = _default_model_paths

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SystemInfo:
    """Detected system capabilities."""
    machine: str
    ram_gb: int
    chip: str
    tier: str  # "studio", "pro", "lite"
    
    @classmethod
    def detect(cls) -> "SystemInfo":
        try:
            result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
            ram_gb = int(result.stdout.strip()) // (1024**3)
        except:
            ram_gb = 8
        
        try:
            result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
            chip = result.stdout.strip()
            if "Apple" in chip:
                chip = chip.replace("Apple ", "")
        except:
            chip = "Unknown"
        
        if ram_gb >= 48:
            return cls("Mac Studio", ram_gb, chip, "studio")
        elif ram_gb >= 16:
            return cls("MacBook Pro", ram_gb, chip, "pro")
        else:
            return cls("Mac", ram_gb, chip, "lite")

# Global system info
SYSTEM = SystemInfo.detect()

# ═══════════════════════════════════════════════════════════════════════════════
# MODEL REPRESENTATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Model:
    """A discovered AI model."""
    name: str
    path: Path
    family: str
    size_gb: float
    tier_required: str  # "lite", "pro", "studio"
    media_type: str = "unknown"  # "image", "video", "speech", "music"
    description: str = ""
    works_on_mac: bool = True  # Whether it works on Apple Silicon
    
    def available_on_system(self) -> bool:
        """Check if model is available on current system (tier AND platform)."""
        tiers = {"lite": 0, "pro": 1, "studio": 2}
        tier_ok = tiers.get(SYSTEM.tier, 0) >= tiers.get(self.tier_required, 0)
        # On Mac, also check Mac compatibility
        is_mac = "apple" in SYSTEM.chip.lower() or "m1" in SYSTEM.chip.lower() or "m2" in SYSTEM.chip.lower() or "m3" in SYSTEM.chip.lower() or "m4" in SYSTEM.chip.lower()
        if is_mac and not self.works_on_mac:
            return False
        return tier_ok


@dataclass
class LoRA:
    """A discovered LoRA model."""
    name: str
    path: Path
    size_mb: float
    compatible_with: str = "unknown"  # "sdxl", "sd15", "flux", "ltx", etc.
    description: str = ""

    @classmethod
    def detect_compatibility(cls, filename: str) -> str:
        """Guess LoRA compatibility from filename."""
        name_lower = filename.lower()
        if "sdxl" in name_lower or "xl" in name_lower:
            return "sdxl"
        if "sd15" in name_lower or "sd1.5" in name_lower or "sd-1" in name_lower:
            return "sd15"
        if "flux" in name_lower:
            return "flux"
        if "ltx" in name_lower:
            return "ltx"
        if "wan" in name_lower:
            return "wan"
        return "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# SPECIFIC MODEL DESCRIPTIONS
# Each model gets a unique "why would I choose this?" description
# ═══════════════════════════════════════════════════════════════════════════════

# Maps partial filename matches to specific descriptions
# More specific patterns checked first, then family fallbacks
SPECIFIC_MODEL_INFO = {
    # ─────────────────────────────────────────────────────────────────────────
    # VIDEO MODELS - Why each one?
    # ─────────────────────────────────────────────────────────────────────────
    
    # LTX-Video (original) - pattern matches filename substrings
    "ltxv-2b-0.9.8-distilled-fp8": {
        "family": "ltxv", "type": "video", 
        "desc": "Distilled LTX-Video (FP8). Fastest video generation, ~10 sec for 3 sec clip. Best for quick iterations."
    },
    "ltxv-2b-0.9.8-distilled": {
        "family": "ltxv", "type": "video", 
        "desc": "Distilled LTX-Video. Fast generation with good motion. Solid everyday choice."
    },
    "ltxv-2b-0.9.6": {
        "family": "ltxv", "type": "video",
        "desc": "Original LTX-Video. Smooth 3-second clips, reliable motion. The classic."
    },
    
    # LTX-2 variants (newer, larger) - requires Gemma text encoder
    "ltx-2-19b-dev-fp8": {
        "family": "ltx2", "type": "video",
        "desc": "Best quality LTX (19B). Needs Gemma encoder + 48GB+ RAM. Stunning detail."
    },
    "ltx-2-19b-distilled-fp8": {
        "family": "ltx2", "type": "video",
        "desc": "Faster LTX-2. Needs Gemma encoder. Quicker than dev version."
    },
    "ltx-2-19b-distilled": {
        "family": "ltx2", "type": "video",
        "desc": "Faster LTX-2 (full precision). Needs Gemma encoder + lots of RAM."
    },
    "ltx-2-spatial-upscaler": {
        "family": "ltx2", "type": "video",
        "desc": "Upscale any LTX video 2x. Add detail after generation. Quick post-process."
    },
    
    # Wan variants - cinematic quality (NOTE: Not working on Mac MPS due to fp8 text encoder issues)
    "wan2.1-t2v-14b": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Wan 2.1 text-to-video (14B). Cinematic. ⚠️ Not yet working on Mac."
    },
    # Wan 2.2 variants (NOTE: Not working on Mac MPS due to fp8 text encoder issues)
    "wan2.2-t2v-1920": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Cinematic 1080p video. Stunning but slow. ⚠️ Not yet working on Mac."
    },
    "wan2.2-t2v-720": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "720p Wan video. Beautiful motion, reasonable speed. ⚠️ Not yet working on Mac."
    },
    "wan2.2-t2v-rapid": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Fastest Wan text-to-video. Quick tests. ⚠️ Not yet working on Mac."
    },
    "wan2.2-i2v-rapid": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Animate any image fast. ⚠️ Not yet working on Mac."
    },
    "wan2.2-i2v-720": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Image-to-video at 720p. ⚠️ Not yet working on Mac."
    },
    
    # Wan 2.1 variants - lighter weight (NOTE: Not working on Mac MPS due to fp8 text encoder issues)
    "wan2.1_t2v_1.3B": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Lightweight Wan (1.3B). Only 8GB VRAM! ⚠️ Not yet working on Mac (fp8 encoder issue)."
    },
    "wan2.1_t2v_14B": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Full Wan 2.1 (14B). Cinematic quality, needs 40GB+ VRAM. ⚠️ Not yet working on Mac."
    },
    "wan2.1_i2v_480p": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Wan 2.1 image-to-video at 480p. ⚠️ Not yet working on Mac."
    },
    "wan2.1_i2v_720p": {
        "family": "wan", "type": "video", "mac": False,
        "desc": "Wan 2.1 image-to-video at 720p. ⚠️ Not yet working on Mac."
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # IMAGE MODELS - Why each one?
    # ─────────────────────────────────────────────────────────────────────────
    
    # DreamShaper variants
    "dreamshaper_8": {
        "family": "dreamshaper", "type": "image",
        "desc": "Fast artistic images (SD 1.5). Quick fantasy/portrait iterations. 512px native."
    },
    "dreamshaperxl": {
        "family": "dreamshaper", "type": "image",
        "desc": "High-res artistic images. Dreamy, painterly style at 1024px. Worth the wait."
    },
    "turbodpmsde": {
        "family": "dreamshaper", "type": "image",
        "desc": "Speed-optimized DreamShaper. Same style, fewer steps needed. Best of both worlds."
    },
    
    # SDXL base
    "sdxl_base": {
        "family": "sdxl", "type": "image",
        "desc": "Vanilla SDXL baseline. Versatile, well-documented. Start here if unsure."
    },
    
    # RealVis / Realistic Vision
    "realisticvision": {
        "family": "realvis", "type": "image",
        "desc": "Photorealistic people and scenes. Best for portraits that look like real photos."
    },
    "hypervae": {
        "family": "realvis", "type": "image",
        "desc": "Enhanced realism with better details. Skin, hair, eyes look more natural."
    },
    
    # FLUX variants
    "flux2_bf16": {
        "family": "flux", "type": "image",
        "desc": "Maximum FLUX quality (needs 32GB+ RAM). Best prompt understanding. For final art."
    },
    "flux2_fp8": {
        "family": "flux", "type": "image",
        "desc": "FLUX that fits in 16GB RAM. Slightly less precise but still exceptional quality."
    },
    "flux2-vae": {
        "family": "flux", "type": "image",
        "desc": "Just the FLUX decoder. Not for generation - used with other FLUX models."
    },
    
    # Lightning (speed optimized)
    "lightning": {
        "family": "lightning", "type": "image",
        "desc": "8-step generation. Rough but FAST. Use to rapidly test prompt ideas."
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUDIO MODELS
    # ─────────────────────────────────────────────────────────────────────────
    "chatterbox": {
        "family": "chatterbox", "type": "speech",
        "desc": "Clone any voice from 10s of audio. Natural speech, not robotic."
    },
    "musicgen": {
        "family": "musicgen", "type": "music",
        "desc": "Generate background music from text. Good for video soundtracks."
    },
}

# Family fallbacks (if specific model not matched)
FAMILY_FALLBACKS = {
    "ltx2": {"type": "video", "desc": "LTX-2 video model. Fast text-to-video generation."},
    "ltxv": {"type": "video", "desc": "Original LTX Video. Reliable motion generation."},
    "wan": {"type": "video", "desc": "Wan video model. High-quality motion and composition."},
    "hunyuan": {"type": "video", "desc": "Tencent's video model. Good quality, moderate speed."},
    "sdxl": {"type": "image", "desc": "SDXL image model. High-res, versatile generation."},
    "dreamshaper": {"type": "image", "desc": "Artistic, painterly style. Great for fantasy."},
    "realvis": {"type": "image", "desc": "Photorealistic images. Best for lifelike results."},
    "flux": {"type": "image", "desc": "Latest generation. Best prompt following and quality."},
    "sd15": {"type": "image", "desc": "Classic SD 1.5. Fast, lightweight, huge community."},
    "chatterbox": {"type": "speech", "desc": "Voice cloning text-to-speech."},
    "musicgen": {"type": "music", "desc": "Text-to-music generation."},
    "unknown": {"type": "unknown", "desc": "Unrecognized model."},
}

# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMENDED MODELS CATALOG
# Models users can download, with RAM requirements and download info
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RecommendedModel:
    """A model available for download."""
    name: str
    type: str  # image, video, speech, music
    size_gb: float
    min_ram_gb: int  # Minimum RAM to run comfortably
    description: str
    url: str  # HuggingFace or CivitAI URL
    filename: str  # Expected filename after download
    priority: int = 5  # 1-10, higher = recommend more strongly
    works_on_mac: bool = True  # Whether it works on Apple Silicon

RECOMMENDED_MODELS = [
    # ─────────────────────────────────────────────────────────────────────────
    # IMAGE MODELS
    # ─────────────────────────────────────────────────────────────────────────
    RecommendedModel(
        name="FLUX.1 Schnell",
        type="image",
        size_gb=12.0,
        min_ram_gb=16,
        description="Latest generation. Best prompt understanding, fast generation.",
        url="https://huggingface.co/black-forest-labs/FLUX.1-schnell",
        filename="flux1-schnell",
        priority=9,
    ),
    RecommendedModel(
        name="DreamShaper XL",
        type="image",
        size_gb=6.5,
        min_ram_gb=12,
        description="Artistic, painterly style. Great for fantasy and portraits.",
        url="https://civitai.com/models/112902/dreamshaper-xl",
        filename="dreamshaperXL",
        priority=8,
    ),
    RecommendedModel(
        name="Realistic Vision 6.0",
        type="image",
        size_gb=2.0,
        min_ram_gb=8,
        description="Photorealistic people and scenes. Fast SD 1.5 based.",
        url="https://civitai.com/models/4201/realistic-vision-v60",
        filename="realisticVision",
        priority=7,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # VIDEO MODELS
    # ─────────────────────────────────────────────────────────────────────────
    RecommendedModel(
        name="LTX-Video Distilled",
        type="video",
        size_gb=4.0,
        min_ram_gb=16,
        description="Fast 3-second video clips. Best balance of speed and quality.",
        url="https://huggingface.co/Lightricks/LTX-Video",
        filename="ltxv-2b-0.9.8-distilled",
        priority=9,
    ),
    RecommendedModel(
        name="LTX-Video FP8",
        type="video",
        size_gb=2.5,
        min_ram_gb=12,
        description="Fastest video generation. Great for quick iterations.",
        url="https://huggingface.co/Lightricks/LTX-Video",
        filename="ltxv-2b-0.9.8-distilled-fp8",
        priority=8,
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # SPEECH MODELS  
    # ─────────────────────────────────────────────────────────────────────────
    RecommendedModel(
        name="Chatterbox TTS",
        type="speech",
        size_gb=1.5,
        min_ram_gb=8,
        description="Voice cloning text-to-speech. Clone any voice with 10s sample.",
        url="https://huggingface.co/ResembleAI/chatterbox",
        filename="chatterbox",
        priority=7,
    ),
]

def get_recommended_models(ram_gb: int = None, exclude_installed: List[str] = None) -> List[RecommendedModel]:
    """Get models recommended for the current system.
    
    Args:
        ram_gb: Available RAM in GB (defaults to system RAM)
        exclude_installed: List of installed model filenames to exclude
    
    Returns:
        List of RecommendedModel sorted by priority
    """
    if ram_gb is None:
        ram_gb = SYSTEM.ram_gb
    if exclude_installed is None:
        exclude_installed = []
    
    # Normalize exclusion list
    exclude_lower = [f.lower() for f in exclude_installed]
    
    recommendations = []
    for model in RECOMMENDED_MODELS:
        # Skip if already installed
        if any(model.filename.lower() in exc for exc in exclude_lower):
            continue
        # Skip if system can't run it
        if model.min_ram_gb > ram_gb:
            continue
        recommendations.append(model)
    
    # Sort by priority (highest first)
    return sorted(recommendations, key=lambda m: m.priority, reverse=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MODEL CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def classify_model(filepath: Path) -> Dict[str, Any]:
    """Classify a model by its name, with specific descriptions per model."""
    name = filepath.stem.lower()
    size_gb = filepath.stat().st_size / (1024**3) if filepath.exists() else 0
    
    # Determine tier requirement based on size
    if size_gb > 30:
        tier = "studio"
    elif size_gb > 10:
        tier = "pro"
    else:
        tier = "lite"
    
    # First: Check for specific model matches (most specific descriptions)
    # Sort by pattern length descending so longer/more specific patterns match first
    sorted_patterns = sorted(SPECIFIC_MODEL_INFO.items(), key=lambda x: len(x[0]), reverse=True)
    for pattern, info in sorted_patterns:
        if pattern.lower() in name:
            return {
                "family": info["family"],
                "type": info["type"],
                "tier": tier,
                "desc": info["desc"],
                "mac": info.get("mac", True)  # Default to True if not specified
            }
    
    # Second: Fall back to family detection
    family_patterns = [
        (["ltx-2", "ltx2"], "ltx2"),
        (["ltxv", "ltx-video"], "ltxv"),
        (["wan"], "wan"),
        (["hunyuan"], "hunyuan"),
        (["flux"], "flux"),
        (["dreamshaper"], "dreamshaper"),
        (["realvis", "realisticvision", "realistic_vision"], "realvis"),
        (["sdxl", "sd_xl"], "sdxl"),
        (["sd_", "sd1", "sd-1"], "sd15"),
        (["lightning"], "lightning"),
        (["chatterbox"], "chatterbox"),
        (["musicgen"], "musicgen"),
    ]
    
    for patterns, family in family_patterns:
        if any(p in name for p in patterns):
            fallback = FAMILY_FALLBACKS.get(family, FAMILY_FALLBACKS["unknown"])
            return {
                "family": family,
                "type": fallback["type"],
                "tier": tier,
                "desc": fallback["desc"],
                "mac": True  # Family fallbacks default to working on Mac
            }
    
    # Unknown model
    return {
        "family": "unknown",
        "type": "unknown",
        "tier": tier,
        "desc": FAMILY_FALLBACKS["unknown"]["desc"],
        "mac": True
    }

# ═══════════════════════════════════════════════════════════════════════════════
# MODEL DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════

def discover_all_models() -> Dict[str, List[Model]]:
    """Discover all models organized by type."""
    models = {"video": [], "image": [], "speech": [], "music": [], "edit": []}
    seen = set()
    
    # Patterns that indicate component models (not standalone generators)
    # These are checked as whole-word or clear suffixes, not substrings
    def is_component_model(name: str) -> bool:
        name_lower = name.lower()
        # Pure VAEs (but not models that include their own VAE like HyperVAE)
        if name_lower.endswith("-vae") or name_lower.endswith("_vae") or name_lower == "vae":
            return True
        # Pure CLIP models
        if "clip_" in name_lower or name_lower.endswith("_clip"):
            return True
        # Pure embeddings
        if "embedding" in name_lower:
            return True
        # Pure ControlNets
        if "controlnet" in name_lower:
            return True
        # Pure IP-Adapters
        if "ipadapter" in name_lower or "ip-adapter" in name_lower:
            return True
        return False
    
    for search_path in MODEL_SEARCH_PATHS:
        if not search_path.exists():
            continue
        
        for pattern in ["**/*.safetensors", "**/*.ckpt", "**/*.pth", "**/*.bin"]:
            for filepath in search_path.glob(pattern):
                if filepath.name in seen:
                    continue
                seen.add(filepath.name)
                
                # Skip component models (VAEs, ControlNets, etc.)
                if is_component_model(filepath.stem):
                    continue
                
                info = classify_model(filepath)
                if info["type"] == "unknown":
                    continue
                
                # Skip files that don't actually exist (broken symlinks, etc.)
                try:
                    file_size = filepath.stat().st_size / (1024**3)
                except (FileNotFoundError, OSError):
                    continue
                
                model = Model(
                    name=filepath.stem,
                    path=filepath,
                    family=info["family"],
                    size_gb=file_size,
                    tier_required=info["tier"],
                    media_type=info["type"],
                    description=info.get("desc", ""),
                    works_on_mac=info.get("mac", True)
                )
                models[info["type"]].append(model)
    
    return models


def discover_loras() -> List[LoRA]:
    """Discover all LoRA models in the loras directory."""
    loras = []
    seen = set()

    # Look in all model search paths for loras subdirectory
    lora_dirs = []
    for search_path in MODEL_SEARCH_PATHS:
        lora_dir = search_path / "loras"
        if lora_dir.exists():
            lora_dirs.append(lora_dir)

    for lora_dir in lora_dirs:
        if not lora_dir.exists():
            continue

        for pattern in ["**/*.safetensors", "**/*.ckpt", "**/*.pt"]:
            for filepath in lora_dir.glob(pattern):
                if filepath.name in seen:
                    continue
                seen.add(filepath.name)

                # Skip broken symlinks
                try:
                    file_size = filepath.stat().st_size / (1024**2)  # MB
                except (FileNotFoundError, OSError):
                    continue

                lora = LoRA(
                    name=filepath.stem,
                    path=filepath,
                    size_mb=file_size,
                    compatible_with=LoRA.detect_compatibility(filepath.stem),
                )
                loras.append(lora)

    return sorted(loras, key=lambda x: x.name.lower())


# ═══════════════════════════════════════════════════════════════════════════════
# COMFYUI BACKEND
# ═══════════════════════════════════════════════════════════════════════════════

def check_backend() -> tuple[bool, str]:
    """Check if ComfyUI backend is running."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/system_stats")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True, "Connected"
    except urllib.error.URLError as e:
        if "Connection refused" in str(e.reason):
            return False, f"ComfyUI not running at {COMFYUI_URL}. Start it with: python main.py"
        return False, f"Cannot reach ComfyUI: {e.reason}"
    except TimeoutError:
        return False, f"ComfyUI at {COMFYUI_URL} not responding (timeout)"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def submit_workflow(workflow: dict) -> tuple[bool, str]:
    """Submit a workflow to ComfyUI."""
    import urllib.request
    import urllib.error
    try:
        payload = json.dumps({
            "prompt": workflow,
            "client_id": f"forge_{int(time.time())}"
        }).encode()
        req = urllib.request.Request(
            f"{COMFYUI_URL}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if "error" in result:
                # ComfyUI returned an error
                error_msg = result.get("error", {}).get("message", str(result["error"]))
                return False, f"ComfyUI error: {error_msg}"
            return True, result.get("prompt_id", "")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            # Try to parse error response
            try:
                error_data = json.loads(e.read().decode())
                error_msg = error_data.get("error", {}).get("message", "Invalid workflow")
                return False, f"Invalid workflow: {error_msg}"
            except:
                pass
        return False, f"HTTP error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Cannot reach ComfyUI: {e.reason}"
    except Exception as e:
        return False, f"Submit error: {str(e)}"

def poll_for_result(prompt_id: str, timeout: int = 300, progress_callback=None) -> tuple[str, Optional[str]]:
    """Poll ComfyUI for generation result with progress updates."""
    import urllib.request
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            # Check progress via queue endpoint
            if progress_callback:
                try:
                    req = urllib.request.Request(f"{COMFYUI_URL}/queue")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        queue = json.loads(resp.read().decode())
                    
                    # Check running queue for our prompt
                    running = queue.get("queue_running", [])
                    for item in running:
                        if len(item) >= 3 and item[1] == prompt_id:
                            # item[2] contains nodes info
                            progress_callback({"status": "running", "queue_position": 0})
                except:
                    pass
            
            req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                history = json.loads(resp.read().decode())
            
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                
                if status.get("completed"):
                    # Find output files (with retry for file system lag)
                    for node_out in entry.get("outputs", {}).values():
                        # Check for images
                        for img in node_out.get("images", []):
                            if "filename" in img:
                                filename = img["filename"]
                                subfolder = img.get("subfolder", "")
                                paths_to_check = [
                                    OUTPUT_DIR / subfolder / filename if subfolder else OUTPUT_DIR / filename,
                                    FORGE_DIR / "output" / subfolder / filename if subfolder else FORGE_DIR / "output" / filename,
                                ]
                                # Retry up to 10 times for file to appear
                                for _ in range(10):
                                    for check_path in paths_to_check:
                                        if check_path.exists():
                                            return "completed", str(check_path)
                                    time.sleep(1)
                        
                        # Check for gifs/videos
                        for gif in node_out.get("gifs", []):
                            if "filename" in gif:
                                filename = gif["filename"]
                                subfolder = gif.get("subfolder", "")
                                paths_to_check = [
                                    OUTPUT_DIR / subfolder / filename if subfolder else OUTPUT_DIR / filename,
                                    FORGE_DIR / "output" / subfolder / filename if subfolder else FORGE_DIR / "output" / filename,
                                ]
                                for _ in range(10):
                                    for check_path in paths_to_check:
                                        if check_path.exists():
                                            return "completed", str(check_path)
                                    time.sleep(1)
                    
                    return "completed", None
                    
                elif status.get("status_str") == "error":
                    return "error", str(status)
        except:
            pass
        
        time.sleep(1)
    
    return "timeout", None

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT ENHANCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

# Quality and style modifiers for different vibes
QUALITY_MODIFIERS = [
    "highly detailed", "professional", "masterpiece", "best quality",
    "sharp focus", "intricate details", "beautiful lighting"
]

STYLE_MODIFIERS = {
    "photo": ["photorealistic", "8k uhd", "dslr", "soft lighting", "film grain"],
    "art": ["digital art", "trending on artstation", "concept art", "illustration"],
    "cinematic": ["cinematic lighting", "dramatic", "volumetric lighting", "ray tracing"],
    "portrait": ["studio lighting", "professional portrait", "bokeh background"],
    "fantasy": ["fantasy art", "magical", "ethereal glow", "mystical atmosphere"],
    "anime": ["anime style", "cel shaded", "vibrant colors", "clean linework"],
}

def enhance_prompt(prompt: str, style: str = "auto") -> str:
    """
    Enhance a basic prompt with quality modifiers and style keywords.
    
    Args:
        prompt: The original user prompt
        style: One of "photo", "art", "cinematic", "portrait", "fantasy", "anime", or "auto"
    
    Returns:
        Enhanced prompt with quality modifiers
    """
    import random
    
    prompt = prompt.strip()
    if not prompt:
        return prompt
    
    # Auto-detect style from prompt keywords
    if style == "auto":
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["photo", "photograph", "realistic", "real"]):
            style = "photo"
        elif any(w in prompt_lower for w in ["portrait", "headshot", "face", "person"]):
            style = "portrait"
        elif any(w in prompt_lower for w in ["anime", "manga", "cartoon"]):
            style = "anime"
        elif any(w in prompt_lower for w in ["fantasy", "magic", "dragon", "wizard", "elf"]):
            style = "fantasy"
        elif any(w in prompt_lower for w in ["movie", "film", "cinematic", "scene"]):
            style = "cinematic"
        else:
            style = "art"  # Default to general art style
    
    # Build enhanced prompt
    parts = [prompt]
    
    # Add 2-3 quality modifiers
    quality = random.sample(QUALITY_MODIFIERS, min(3, len(QUALITY_MODIFIERS)))
    parts.extend(quality)
    
    # Add 2-3 style modifiers
    if style in STYLE_MODIFIERS:
        style_mods = random.sample(STYLE_MODIFIERS[style], min(3, len(STYLE_MODIFIERS[style])))
        parts.extend(style_mods)
    
    return ", ".join(parts)

# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_image(prompt_text: str, model_name: str, width: int, height: int,
                   steps: int, cfg: float, seed: int,
                   lora_name: Optional[str] = None, lora_strength: float = 1.0,
                   progress_callback=None) -> tuple[Optional[str], str]:
    """Generate an image using ComfyUI.

    Args:
        prompt_text: The generation prompt
        model_name: Name of the model to use
        width: Image width
        height: Image height
        steps: Number of sampling steps (quality)
        cfg: CFG scale (creativity - higher = more literal)
        seed: Random seed (-1 for random)
        lora_name: Optional LoRA filename to apply
        lora_strength: LoRA strength (0.0 to 1.0, default 1.0)
        progress_callback: Optional callback(GenerationProgress) for real-time updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    from forge_progress import track_generation_progress, GenerationProgress
    
    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."
    
    # Load workflow
    workflow_path = WORKFLOWS_DIR / "sdxl_simple.json"
    if not workflow_path.exists():
        return None, f"Workflow not found: {workflow_path}"
    
    with open(workflow_path) as f:
        workflow = json.load(f)
    
    # Find model file
    model_file = None
    for search_path in MODEL_SEARCH_PATHS:
        for pattern in ["**/*.safetensors", "**/*.ckpt"]:
            for fp in search_path.glob(pattern):
                if model_name in fp.stem:
                    model_file = fp.name
                    break
    
    if not model_file:
        model_file = f"{model_name}.safetensors"
    
    # Parameterize workflow
    actual_seed = seed if seed >= 0 else random.randint(0, 2**32-1)
    
    # Detect model family for special handling
    is_lightning = "lightning" in model_name.lower()
    is_turbo = "turbo" in model_name.lower()
    is_sd15 = any(x in model_name.lower() for x in ["dreamshaper_8", "realvis", "realisticvision"])
    
    for node_id, node in workflow.items():
        cls = node.get("class_type", "")
        inputs = node.get("inputs", {})
        
        if cls == "CheckpointLoaderSimple":
            inputs["ckpt_name"] = model_file
        elif cls == "EmptyLatentImage":
            inputs["width"] = int(width)
            inputs["height"] = int(height)
        elif cls == "KSampler":
            inputs["seed"] = actual_seed
            
            # Lightning models need specific settings
            if is_lightning:
                inputs["steps"] = 4  # Lightning is optimized for 4 steps
                inputs["cfg"] = 1.5  # Low CFG for lightning
                inputs["sampler_name"] = "euler"
                inputs["scheduler"] = "sgm_uniform"
            elif is_turbo:
                inputs["steps"] = min(int(steps), 8)  # Turbo models use fewer steps
                inputs["cfg"] = 2.0
                inputs["sampler_name"] = "dpmpp_sde"
                inputs["scheduler"] = "karras"
            elif is_sd15:
                # SD 1.5 models work well with default settings
                inputs["steps"] = int(steps)
                inputs["cfg"] = float(cfg)
                inputs["sampler_name"] = "euler_ancestral"
                inputs["scheduler"] = "normal"
            else:
                # SDXL and others
                inputs["steps"] = int(steps)
                inputs["cfg"] = float(cfg)
                inputs["sampler_name"] = "euler_ancestral"
                inputs["scheduler"] = "normal"
                
        elif cls == "CLIPTextEncode":
            if node_id == "6":  # Positive prompt node
                inputs["text"] = prompt_text

    # Inject LoRA if specified
    if lora_name:
        # Find the LoRA file
        lora_file = None
        for search_path in MODEL_SEARCH_PATHS:
            lora_dir = search_path / "loras"
            if lora_dir.exists():
                for fp in lora_dir.glob("**/*.safetensors"):
                    if lora_name in fp.name or lora_name == fp.stem:
                        lora_file = fp.name
                        break
            if lora_file:
                break

        if lora_file:
            # Add LoraLoader node - inserts between checkpoint and sampler/clip
            # Node structure: checkpoint(4) -> lora(10) -> sampler(3), clip(6,7)
            workflow["10"] = {
                "class_type": "LoraLoader",
                "inputs": {
                    "lora_name": lora_file,
                    "strength_model": float(lora_strength),
                    "strength_clip": float(lora_strength),
                    "model": ["4", 0],  # Connect to checkpoint model output
                    "clip": ["4", 1],   # Connect to checkpoint clip output
                }
            }
            # Rewire sampler and clip nodes to use LoRA output instead of checkpoint
            if "3" in workflow:  # KSampler
                workflow["3"]["inputs"]["model"] = ["10", 0]
            if "6" in workflow:  # Positive CLIP
                workflow["6"]["inputs"]["clip"] = ["10", 1]
            if "7" in workflow:  # Negative CLIP
                workflow["7"]["inputs"]["clip"] = ["10", 1]
            print(f"🎭 Applied LoRA: {lora_file} (strength: {lora_strength})")

    # Submit and poll with progress tracking
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"
    
    prompt_id = result
    
    # Use new progress tracker for real-time updates
    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=180, on_progress=progress_callback
    )
    
    if status == "completed" and output_filename:
        # Find full path to output file
        output_path = None
        for check_path in [
            OUTPUT_DIR / output_filename,
            FORGE_DIR / "output" / output_filename,
        ]:
            if check_path.exists():
                output_path = str(check_path)
                break
        
        # Wait briefly for file system
        if not output_path:
            time.sleep(2)
            for check_path in [
                OUTPUT_DIR / output_filename,
                FORGE_DIR / "output" / output_filename,
            ]:
                if check_path.exists():
                    output_path = str(check_path)
                    break
        
        if output_path:
            return output_path, f"Generated in {progress.format_time(progress.elapsed_seconds)} • Seed: {actual_seed}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Generation timed out after 3 minutes"
    else:
        return None, f"Generation failed: {progress.error_message or status}"


def generate_video(prompt_text: str, model_name: str, width: int, height: int,
                   num_frames: int, steps: int, cfg: float, seed: int,
                   progress_callback=None) -> tuple[Optional[str], str]:
    """Generate a video using ComfyUI with LTX-Video or Wan models.
    
    Args:
        prompt_text: The generation prompt
        model_name: Name of the video model to use
        width: Video width (multiple of 32)
        height: Video height (multiple of 32)
        num_frames: Number of frames
        steps: Number of sampling steps
        cfg: CFG scale
        seed: Random seed (-1 for random)
        progress_callback: Optional callback(GenerationProgress) for real-time updates
    
    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    from forge_progress import track_generation_progress
    
    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."
    
    # Detect model family and select workflow
    import platform
    is_mac = platform.system() == "Darwin"
    
    model_lower = model_name.lower()
    if "wan" in model_lower:
        # Check for text encoder - Mac needs FP16, others can use FP8
        fp16_encoder = FORGE_DIR / "models" / "text_encoders" / "umt5_xxl_fp16.safetensors"
        fp8_encoder = FORGE_DIR / "models" / "text_encoders" / "umt5_xxl_fp8_e4m3fn_scaled.safetensors"

        if is_mac:
            if not fp16_encoder.exists():
                return None, "Wan models on Mac require FP16 text encoder (MPS doesn't support FP8). Missing: umt5_xxl_fp16.safetensors"
            wan_encoder = "umt5_xxl_fp16.safetensors"
        else:
            # Prefer FP8 on non-Mac (smaller), fall back to FP16
            if fp8_encoder.exists():
                wan_encoder = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
            elif fp16_encoder.exists():
                wan_encoder = "umt5_xxl_fp16.safetensors"
            else:
                return None, "Wan models require UMT5 text encoder. Missing: umt5_xxl_fp16.safetensors or umt5_xxl_fp8_e4m3fn_scaled.safetensors"

        workflow_name = "wan21_t2v_api.json"
        model_family = "wan"
    elif "ltx-2" in model_lower or "ltx2" in model_lower:
        # LTX-2 (19B) requires Gemma text encoder - different workflow
        # Check if required text encoders exist
        gemma_paths = [
            FORGE_DIR / "models" / "text_encoders" / "gemma_3_12B_it_fp8_e4m3fn.safetensors",
            FORGE_DIR / "models" / "clip" / "gemma_3_12B_it_fp8_e4m3fn.safetensors",
        ]
        proj_paths = [
            FORGE_DIR / "models" / "text_encoders" / "ltx-2-19b-dev-fp4_projections_only.safetensors",
            FORGE_DIR / "models" / "clip" / "ltx-2-19b-dev-fp4_projections_only.safetensors",
        ]
        has_gemma = any(p.exists() for p in gemma_paths)
        has_proj = any(p.exists() for p in proj_paths)

        if not has_gemma or not has_proj:
            missing = []
            if not has_gemma:
                missing.append("Gemma FP8 encoder (gemma_3_12B_it_fp8_e4m3fn.safetensors)")
            if not has_proj:
                missing.append("LTX-2 projections (ltx-2-19b-dev-fp4_projections_only.safetensors)")
            return None, f"LTX-2 requires additional text encoders. Missing: {', '.join(missing)}. Download from: https://huggingface.co/GitMylo/LTX-2-comfy_gemma_fp8_e4m3fn"

        workflow_name = "ltx2_t2v_api.json"
        model_family = "ltx2"
    elif "ltx" in model_lower:
        # Original LTX-Video uses T5 encoder
        workflow_name = "ltxv_t2v_api.json"
        model_family = "ltx"
    else:
        return None, f"Unknown video model family: {model_name}"
    
    workflow_path = WORKFLOWS_DIR / workflow_name
    if not workflow_path.exists():
        return None, f"Workflow not found: {workflow_path}"
    
    with open(workflow_path) as f:
        workflow = json.load(f)
    
    # Find model file
    model_file = None
    for search_path in MODEL_SEARCH_PATHS:
        for pattern in ["**/*.safetensors", "**/*.ckpt"]:
            for fp in search_path.glob(pattern):
                if model_name in fp.stem:
                    model_file = fp.name
                    break
    
    if not model_file:
        model_file = f"{model_name}.safetensors"
    
    # Parameterize workflow
    actual_seed = seed if seed >= 0 else random.randint(0, 2**32-1)
    negative_prompt = "low quality, worst quality, deformed, distorted, disfigured, motion smear, motion artifacts, fused fingers, bad anatomy, weird hand, ugly"
    
    if model_family == "wan":
        # Wan 2.1 workflow parameterization
        for node_id, node in workflow.items():
            cls = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if cls == "UNETLoader":
                inputs["unet_name"] = model_file
            elif cls == "CLIPLoader":
                # Inject the selected encoder (FP16 on Mac, FP8 on others)
                inputs["clip_name"] = wan_encoder
            elif cls == "EmptyHunyuanLatentVideo":
                inputs["width"] = int(width)
                inputs["height"] = int(height)
                inputs["length"] = int(num_frames)
            elif cls == "KSampler":
                inputs["seed"] = actual_seed
                inputs["steps"] = int(steps)
                inputs["cfg"] = float(cfg)
            elif cls == "CLIPTextEncode":
                if node_id == "6":  # Positive prompt
                    inputs["text"] = prompt_text
                elif node_id == "7":  # Negative prompt
                    inputs["text"] = negative_prompt
    elif model_family == "ltx2":
        # LTX-2 (19B) workflow parameterization - uses Gemma encoder
        for node_id, node in workflow.items():
            cls = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if cls == "CheckpointLoaderSimple":
                inputs["ckpt_name"] = model_file
            elif cls == "EmptyLTXVLatentVideo":
                inputs["width"] = int(width)
                inputs["height"] = int(height)
                inputs["length"] = int(num_frames)
            elif cls == "LTXVScheduler":
                inputs["steps"] = int(steps)
            elif cls == "SamplerCustom":
                inputs["cfg"] = float(cfg)
                inputs["noise_seed"] = actual_seed
            elif cls == "CLIPTextEncode":
                if node_id == "102":  # Positive prompt (LTX-2 workflow uses different IDs)
                    inputs["text"] = prompt_text
                elif node_id == "103":  # Negative prompt
                    inputs["text"] = negative_prompt
    else:
        # Original LTX-Video workflow parameterization - uses T5 encoder
        for node_id, node in workflow.items():
            cls = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if cls == "CheckpointLoaderSimple":
                inputs["ckpt_name"] = model_file
            elif cls == "EmptyLTXVLatentVideo":
                inputs["width"] = int(width)
                inputs["height"] = int(height)
                inputs["length"] = int(num_frames)
            elif cls == "LTXVScheduler":
                inputs["steps"] = int(steps)
            elif cls == "SamplerCustom":
                inputs["cfg"] = float(cfg)
                inputs["noise_seed"] = actual_seed
            elif cls == "CLIPTextEncode":
                if node_id == "6":  # Positive prompt
                    inputs["text"] = prompt_text
                elif node_id == "7":  # Negative prompt
                    inputs["text"] = negative_prompt
    
    # Submit and poll with progress tracking (video takes longer)
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"
    
    prompt_id = result
    
    # Use new progress tracker for real-time updates
    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=600, on_progress=progress_callback
    )
    
    if status == "completed" and output_filename:
        # Find full path to output file
        output_path = None
        for check_path in [
            OUTPUT_DIR / output_filename,
            FORGE_DIR / "output" / output_filename,
        ]:
            if check_path.exists():
                output_path = str(check_path)
                break
        
        # Wait briefly for file system
        if not output_path:
            time.sleep(2)
            for check_path in [
                OUTPUT_DIR / output_filename,
                FORGE_DIR / "output" / output_filename,
            ]:
                if check_path.exists():
                    output_path = str(check_path)
                    break
        
        if output_path:
            return output_path, f"Generated in {progress.format_time(progress.elapsed_seconds)} • Seed: {actual_seed}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Generation timed out after 10 minutes"
    else:
        return None, f"Generation failed: {progress.error_message or status}"


def generate_video_from_image(prompt_text: str, image_path: str, model_name: str, 
                               width: int, height: int, num_frames: int, 
                               steps: int, cfg: float, seed: int,
                               strength: float = 0.9,
                               progress_callback=None) -> tuple[Optional[str], str]:
    """Generate a video from an input image using LTX-Video.
    
    Args:
        prompt_text: Motion/action prompt (describe what should happen)
        image_path: Path to the input image
        model_name: Name of the video model to use
        width: Video width (multiple of 32)
        height: Video height (multiple of 32)
        num_frames: Number of frames
        steps: Number of sampling steps
        cfg: CFG scale
        seed: Random seed (-1 for random)
        strength: How much the first frame can deviate (0-1, lower = more faithful)
        progress_callback: Optional callback for progress updates
    
    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    import shutil
    from forge_progress import track_generation_progress
    
    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."
    
    # Validate image exists
    if not Path(image_path).exists():
        return None, f"Image not found: {image_path}"
    
    # Only LTX supports I2V on Mac currently
    model_lower = model_name.lower()
    if "ltx" not in model_lower:
        return None, "Image-to-video currently only supported with LTX-Video models"
    
    workflow_path = WORKFLOWS_DIR / "ltxv_i2v_api.json"
    if not workflow_path.exists():
        return None, f"I2V workflow not found: {workflow_path}"
    
    with open(workflow_path) as f:
        workflow = json.load(f)
    
    # Copy image to ComfyUI input folder
    comfyui_input = Path(image_path).parent.parent / "input"
    if not comfyui_input.exists():
        comfyui_input = COMFYUI_PATH / "input"
    comfyui_input.mkdir(exist_ok=True)
    
    input_image_name = f"forge_i2v_{random.randint(0, 99999)}.png"
    dest_path = comfyui_input / input_image_name
    shutil.copy(image_path, dest_path)
    
    # Find model file
    model_file = None
    for search_path in MODEL_SEARCH_PATHS:
        for pattern in ["**/*.safetensors", "**/*.ckpt"]:
            for fp in search_path.glob(pattern):
                if model_name in fp.stem:
                    model_file = fp.name
                    break
    
    if not model_file:
        model_file = f"{model_name}.safetensors"
    
    # Parameterize workflow
    actual_seed = seed if seed >= 0 else random.randint(0, 2**32-1)
    negative_prompt = "low quality, worst quality, deformed, distorted, disfigured, motion smear, motion artifacts, fused fingers, bad anatomy, weird hand, ugly"
    
    for node_id, node in workflow.items():
        cls = node.get("class_type", "")
        inputs = node.get("inputs", {})
        
        if cls == "LoadImage":
            inputs["image"] = input_image_name
        elif cls == "CheckpointLoaderSimple":
            inputs["ckpt_name"] = model_file
        elif cls == "EmptyLTXVLatentVideo":
            inputs["width"] = int(width)
            inputs["height"] = int(height)
            inputs["length"] = int(num_frames)
        elif cls == "LTXVImgToVideoInplace":
            inputs["strength"] = float(strength)
        elif cls == "LTXVScheduler":
            inputs["steps"] = int(steps)
        elif cls == "SamplerCustom":
            inputs["noise_seed"] = actual_seed
            inputs["cfg"] = float(cfg)
        elif cls == "CLIPTextEncode":
            if node_id == "6":  # Positive prompt
                inputs["text"] = prompt_text
            elif node_id == "7":  # Negative prompt
                inputs["text"] = negative_prompt
    
    # Submit and poll with progress tracking
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"
    
    prompt_id = result
    
    # Use progress tracker
    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=600, on_progress=progress_callback
    )
    
    if status == "completed" and output_filename:
        # Find full path to output file
        output_path = None
        for check_path in [
            OUTPUT_DIR / output_filename,
            FORGE_DIR / "output" / output_filename,
        ]:
            if check_path.exists():
                output_path = str(check_path)
                break
        
        # Wait briefly for file system
        if not output_path:
            time.sleep(2)
            for check_path in [
                OUTPUT_DIR / output_filename,
                FORGE_DIR / "output" / output_filename,
            ]:
                if check_path.exists():
                    output_path = str(check_path)
                    break
        
        if output_path:
            return output_path, f"Generated in {progress.format_time(progress.elapsed_seconds)} • Seed: {actual_seed}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Generation timed out after 10 minutes"
    else:
        return None, f"Generation failed: {progress.error_message or status}"
