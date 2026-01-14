"""
💡 NeoVak Backend - Shared AI Generation Infrastructure
Framework-agnostic code for model discovery and ComfyUI integration.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION (Config file > Environment Variables > Defaults)
# ═══════════════════════════════════════════════════════════════════════════════

NEOVAK_DIR = Path(__file__).parent
CONFIG_FILE = NEOVAK_DIR / "neovak_config.json"

# Load config file if it exists
_config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE) as f:
            _config = json.load(f)
        print(f"📁 Loaded config from {CONFIG_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to load config: {e}")

def _get_config(key: str, env_var: str, default):
    """Get config value from: config file > env var > default."""
    if key in _config:
        return _config[key]
    return os.environ.get(env_var, default)

OUTPUT_DIR = Path(_get_config('output_dir', 'NEOVAK_OUTPUT_DIR', NEOVAK_DIR / "output"))
WORKFLOWS_DIR = Path(_get_config('workflows_dir', 'NEOVAK_WORKFLOWS_DIR', NEOVAK_DIR / "workflows"))
OUTPUT_DIR.mkdir(exist_ok=True)

# ComfyUI backend URL
COMFYUI_URL = _get_config('comfyui_url', 'COMFYUI_URL', "http://127.0.0.1:8188")

# Model search paths
_default_model_paths = [
    Path.home() / ".comfyui" / "models",
    Path.home() / "ComfyUI" / "models",
    NEOVAK_DIR / "models",
]

# Add paths from config file
if 'model_paths' in _config:
    for p in _config['model_paths']:
        path = Path(p).expanduser()
        if path not in _default_model_paths:
            _default_model_paths.append(path)

# Add paths from environment variable
_extra_paths = os.environ.get('NEOVAK_MODEL_PATHS', '')
if _extra_paths:
    for p in _extra_paths.split(':'):
        if p:
            _default_model_paths.append(Path(p))

# Add common external drive locations if they exist
_external_paths = [
    Path("/Volumes/Mix Master Mike/Experimental Models/ComfyUI_Models"),
]
for p in _external_paths:
    if p.exists():
        _default_model_paths.append(p)

MODEL_SEARCH_PATHS = _default_model_paths


def save_config(config_dict: dict):
    """Save configuration to neovak_config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save config: {e}")
        return False


def get_current_config() -> dict:
    """Get current configuration as a dictionary."""
    return {
        "comfyui_url": COMFYUI_URL,
        "output_dir": str(OUTPUT_DIR),
        "model_paths": [str(p) for p in MODEL_SEARCH_PATHS],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PRESETS / FAVORITES SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

PRESETS_FILE = NEOVAK_DIR / "neovak_presets.json"

@dataclass
class Preset:
    """A saved generation preset."""
    name: str
    tab: str  # "image", "video", "voice", "music"
    prompt: str
    model: str
    # Image-specific
    width: int = 1024
    height: int = 1024
    steps: int = 30
    cfg: float = 7.0
    seed: int = -1
    # Video-specific
    frames: int = 49
    motion: float = 1.0
    # Voice-specific
    voice_mode: str = "quick"
    speed: float = 1.0
    pitch: int = 0
    # Music-specific
    duration: int = 30
    style_tags: List[str] = field(default_factory=list)
    # Metadata
    created: str = ""
    thumbnail: str = ""  # Path to thumbnail image

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tab": self.tab,
            "prompt": self.prompt,
            "model": self.model,
            "width": self.width,
            "height": self.height,
            "steps": self.steps,
            "cfg": self.cfg,
            "seed": self.seed,
            "frames": self.frames,
            "motion": self.motion,
            "voice_mode": self.voice_mode,
            "speed": self.speed,
            "pitch": self.pitch,
            "duration": self.duration,
            "style_tags": self.style_tags,
            "created": self.created,
            "thumbnail": self.thumbnail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Preset':
        return cls(
            name=data.get("name", "Untitled"),
            tab=data.get("tab", "image"),
            prompt=data.get("prompt", ""),
            model=data.get("model", ""),
            width=data.get("width", 1024),
            height=data.get("height", 1024),
            steps=data.get("steps", 30),
            cfg=data.get("cfg", 7.0),
            seed=data.get("seed", -1),
            frames=data.get("frames", 49),
            motion=data.get("motion", 1.0),
            voice_mode=data.get("voice_mode", "quick"),
            speed=data.get("speed", 1.0),
            pitch=data.get("pitch", 0),
            duration=data.get("duration", 30),
            style_tags=data.get("style_tags", []),
            created=data.get("created", ""),
            thumbnail=data.get("thumbnail", ""),
        )


def load_presets() -> List[Preset]:
    """Load all presets from file."""
    if not PRESETS_FILE.exists():
        return []
    try:
        with open(PRESETS_FILE) as f:
            data = json.load(f)
        return [Preset.from_dict(p) for p in data.get("presets", [])]
    except Exception as e:
        print(f"Failed to load presets: {e}")
        return []


def save_presets(presets: List[Preset]) -> bool:
    """Save all presets to file."""
    try:
        data = {"presets": [p.to_dict() for p in presets]}
        with open(PRESETS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save presets: {e}")
        return False


def add_preset(preset: Preset) -> bool:
    """Add a new preset."""
    presets = load_presets()
    # Add timestamp if not set
    if not preset.created:
        from datetime import datetime
        preset.created = datetime.now().isoformat()
    presets.append(preset)
    return save_presets(presets)


def delete_preset(name: str) -> bool:
    """Delete a preset by name."""
    presets = load_presets()
    presets = [p for p in presets if p.name != name]
    return save_presets(presets)


def get_presets_for_tab(tab: str) -> List[Preset]:
    """Get presets filtered by tab."""
    return [p for p in load_presets() if p.tab == tab]


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BatchJob:
    """A single job in a batch generation queue."""
    id: int
    prompt: str
    seed: int
    status: str = "pending"  # pending, running, completed, failed
    output_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BatchConfig:
    """Configuration for batch generation."""
    model: str
    width: int
    height: int
    steps: int
    cfg: float
    # Batch settings
    num_images: int = 4
    seed_mode: str = "random"  # "random", "sequential", "fixed"
    base_seed: int = -1
    prompt_variations: List[str] = field(default_factory=list)  # Optional prompt variations


def create_batch_jobs(config: BatchConfig, base_prompt: str) -> List[BatchJob]:
    """Create a list of batch jobs based on configuration.

    Args:
        config: Batch configuration with model settings and batch options
        base_prompt: The base prompt to use (may be varied)

    Returns:
        List of BatchJob objects ready for processing
    """
    import random

    jobs = []
    prompts = config.prompt_variations if config.prompt_variations else [base_prompt]

    # Generate seeds based on mode
    if config.seed_mode == "fixed" and config.base_seed >= 0:
        seeds = [config.base_seed] * config.num_images
    elif config.seed_mode == "sequential" and config.base_seed >= 0:
        seeds = [config.base_seed + i for i in range(config.num_images)]
    else:  # random
        seeds = [random.randint(0, 2**32-1) for _ in range(config.num_images)]

    # Create jobs - cycle through prompts if fewer than num_images
    for i in range(config.num_images):
        prompt = prompts[i % len(prompts)]
        jobs.append(BatchJob(
            id=i,
            prompt=prompt,
            seed=seeds[i],
        ))

    return jobs


def get_batch_status(jobs: List[BatchJob]) -> dict:
    """Get summary status of batch jobs.

    Returns:
        Dict with counts: pending, running, completed, failed, total
    """
    return {
        "pending": sum(1 for j in jobs if j.status == "pending"),
        "running": sum(1 for j in jobs if j.status == "running"),
        "completed": sum(1 for j in jobs if j.status == "completed"),
        "failed": sum(1 for j in jobs if j.status == "failed"),
        "total": len(jobs),
    }


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

        # Detect machine type from chip name and model identifier
        machine = "Mac"
        try:
            # Try to get actual hardware model
            result = subprocess.run(["sysctl", "-n", "hw.model"], capture_output=True, text=True)
            model = result.stdout.strip().lower()
            if "macbookpro" in model:
                machine = "MacBook Pro"
            elif "macbookair" in model:
                machine = "MacBook Air"
            elif "macmini" in model:
                machine = "Mac mini"
            elif "macstudio" in model:
                machine = "Mac Studio"
            elif "macpro" in model:
                machine = "Mac Pro"
            elif "imac" in model:
                machine = "iMac"
        except:
            # Fallback: guess from chip name
            if "Ultra" in chip or "Max" in chip:
                machine = "Mac Studio" if ram_gb >= 64 else "MacBook Pro"
            elif "Pro" in chip:
                machine = "MacBook Pro"
            elif "M1" in chip or "M2" in chip or "M3" in chip or "M4" in chip:
                machine = "MacBook Air"

        # Tier based on RAM (what models can you realistically run)
        if ram_gb >= 48:
            tier = "studio"  # Can run everything
        elif ram_gb >= 16:
            tier = "pro"     # Can run most things
        else:
            tier = "lite"    # Limited to smaller models

        return cls(machine, ram_gb, chip, tier)

    def get_available_memory_gb(self) -> float:
        """Get currently available memory (not just total RAM).

        On Apple Silicon, unified memory is shared between CPU and GPU,
        so we check actual availability, not just total.
        """
        try:
            import platform
            if platform.system() == "Darwin":
                # macOS: use vm_stat for memory pressure info
                result = subprocess.run(["vm_stat"], capture_output=True, text=True)
                lines = result.stdout.strip().split("\n")

                # Parse page size
                page_size = 4096  # default
                for line in lines:
                    if "page size of" in line:
                        page_size = int(line.split()[-2])
                        break

                # Parse free + inactive pages (available for use)
                free_pages = 0
                inactive_pages = 0
                for line in lines:
                    if line.startswith("Pages free:"):
                        free_pages = int(line.split()[2].replace(".", ""))
                    elif line.startswith("Pages inactive:"):
                        inactive_pages = int(line.split()[2].replace(".", ""))

                available_bytes = (free_pages + inactive_pages) * page_size
                return available_bytes / (1024**3)
            else:
                # Linux/other: try /proc/meminfo
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemAvailable:"):
                            kb = int(line.split()[1])
                            return kb / (1024**2)
        except Exception:
            pass

        # Fallback: assume 60% of total RAM is available
        return self.ram_gb * 0.6

    def get_memory_pressure(self) -> str:
        """Get current memory pressure level: 'low', 'medium', 'high', 'critical'."""
        available = self.get_available_memory_gb()
        ratio = available / self.ram_gb

        if ratio > 0.4:
            return "low"
        elif ratio > 0.25:
            return "medium"
        elif ratio > 0.1:
            return "high"
        else:
            return "critical"

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
    vram_required_gb: float = 0.0  # Estimated VRAM/unified memory needed
    backend_mode: str = "comfyui"  # "comfyui" or "direct" - how to run the model

    def available_on_system(self) -> bool:
        """Check if model can run on this hardware (static check)."""
        tiers = {"lite": 0, "pro": 1, "studio": 2}
        return tiers.get(SYSTEM.tier, 0) >= tiers.get(self.tier_required, 0)

    def can_run_now(self) -> tuple[bool, str]:
        """Check if model can run RIGHT NOW given current memory.

        Returns: (can_run, reason)
        """
        available = SYSTEM.get_available_memory_gb()
        required = self.vram_required_gb

        if required <= 0:
            # No estimate available, assume it's fine
            return True, "Memory requirements unknown"

        # Leave 2GB headroom for system
        usable = available - 2.0

        if usable >= required:
            headroom = usable - required
            if headroom > 4:
                return True, f"Plenty of room ({available:.1f}GB available)"
            else:
                return True, f"Should work ({available:.1f}GB available, needs ~{required:.1f}GB)"
        elif usable >= required * 0.8:
            return True, f"Tight fit - may be slow ({available:.1f}GB available, needs ~{required:.1f}GB)"
        else:
            return False, f"Not enough memory ({available:.1f}GB available, needs ~{required:.1f}GB)"

    def memory_status(self) -> str:
        """Get a short status string for UI: 'ok', 'tight', 'warning', 'no'."""
        can_run, _ = self.can_run_now()
        if not can_run:
            return "no"

        available = SYSTEM.get_available_memory_gb()
        required = self.vram_required_gb
        if required <= 0:
            return "ok"

        ratio = available / required
        if ratio > 2.0:
            return "ok"
        elif ratio > 1.3:
            return "tight"
        else:
            return "warning"


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY ESTIMATION
# ═══════════════════════════════════════════════════════════════════════════════

# Memory multipliers by architecture type
# These are empirical estimates for peak memory during inference
MEMORY_MULTIPLIERS = {
    # Image models - file size × multiplier = peak VRAM
    "sdxl": 1.2,        # SDXL needs ~1.2x file size
    "sd15": 1.1,        # SD 1.5 is efficient
    "flux": 1.4,        # FLUX is memory hungry
    "dreamshaper": 1.2,
    "realvis": 1.2,
    "lightning": 1.0,   # Lightning is optimized

    # Video models - more complex, need more overhead
    "ltxv": 1.8,        # LTX-Video needs significant overhead for temporal
    "ltx2": 2.0,        # LTX-2 even more
    "wan": 2.5,         # Wan is memory intensive
    "hunyuan": 2.0,

    # Audio/TTS models
    "chatterbox": 1.3,
    "xtts": 1.4,         # Coqui XTTS
    "f5tts": 1.3,        # F5-TTS
    "bark": 2.0,         # Bark is memory hungry
    "tortoise": 2.5,     # TorToise is slow but quality
    "styletts": 1.2,     # StyleTTS2

    # Music/Audio models
    "musicgen": 1.5,       # MusicGen small-medium
    "musicgen_large": 2.5, # MusicGen large
    "stable_audio": 1.8,   # Stable Audio Open
    "audiocraft": 2.0,     # Meta AudioCraft
    "riffusion": 1.2,      # Riffusion (SD-based)
    "audioldm": 1.5,       # AudioLDM
    "audioldm2": 2.0,      # AudioLDM2

    # Default
    "unknown": 1.5,
}

# Some models need additional components loaded
ADDITIONAL_MEMORY = {
    # Video models load VAE + text encoder separately
    "ltxv": 1.5,   # T5 encoder + VAE
    "ltx2": 2.0,
    "wan": 3.0,    # Large text encoder

    # FLUX needs T5
    "flux": 2.0,
}


def estimate_memory_required(model_path: Path, family: str) -> float:
    """Estimate memory required to run a model.

    Args:
        model_path: Path to the model file
        family: Model family (sdxl, flux, ltxv, etc.)

    Returns:
        Estimated GB of memory required for inference
    """
    try:
        file_size_gb = model_path.stat().st_size / (1024**3)
    except (FileNotFoundError, OSError):
        return 0.0

    # Base memory from file size
    multiplier = MEMORY_MULTIPLIERS.get(family, MEMORY_MULTIPLIERS["unknown"])
    base_memory = file_size_gb * multiplier

    # Add overhead for additional components
    additional = ADDITIONAL_MEMORY.get(family, 0.0)

    # Add fixed overhead for ComfyUI/Python runtime (~1.5GB)
    runtime_overhead = 1.5

    total = base_memory + additional + runtime_overhead

    # Round to 1 decimal
    return round(total, 1)

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
    
    # LTX-2 variants (newer, larger)
    "ltx-2-19b-dev-fp8": {
        "family": "ltx2", "type": "video",
        "desc": "Best quality LTX (19B params). Stunning detail but needs 48GB+ RAM. For final renders."
    },
    "ltx-2-19b-distilled": {
        "family": "ltx2", "type": "video",
        "desc": "Faster LTX-2. Still needs lots of RAM but quicker than dev version."
    },
    "ltx-2-spatial-upscaler": {
        "family": "ltx2", "type": "video",
        "desc": "Upscale any LTX video 2x. Add detail after generation. Quick post-process."
    },
    
    # Wan variants - cinematic quality (NOTE: Not working on Mac MPS due to fp8 text encoder issues)
    "wan2.1-t2v-14b": {
        "family": "wan", "type": "video",
        "desc": "Wan 2.1 text-to-video (14B). Cinematic. ⚠️ Not yet working on Mac."
    },
    # Wan 2.2 variants (NOTE: Not working on Mac MPS due to fp8 text encoder issues)
    "wan2.2-t2v-1920": {
        "family": "wan", "type": "video",
        "desc": "Cinematic 1080p video. Stunning but slow. ⚠️ Not yet working on Mac."
    },
    "wan2.2-t2v-720": {
        "family": "wan", "type": "video",
        "desc": "720p Wan video. Beautiful motion, reasonable speed. ⚠️ Not yet working on Mac."
    },
    "wan2.2-t2v-rapid": {
        "family": "wan", "type": "video",
        "desc": "Fastest Wan text-to-video. Quick tests. ⚠️ Not yet working on Mac."
    },
    "wan2.2-i2v-rapid": {
        "family": "wan", "type": "video",
        "desc": "Animate any image fast. ⚠️ Not yet working on Mac."
    },
    "wan2.2-i2v-720": {
        "family": "wan", "type": "video",
        "desc": "Image-to-video at 720p. ⚠️ Not yet working on Mac."
    },
    
    # Wan 2.1 variants - lighter weight (NOTE: Not working on Mac MPS due to fp8 text encoder issues)
    "wan2.1_t2v_1.3B": {
        "family": "wan", "type": "video",
        "desc": "Lightweight Wan (1.3B). Only 8GB VRAM! ⚠️ Not yet working on Mac (fp8 encoder issue)."
    },
    "wan2.1_t2v_14B": {
        "family": "wan", "type": "video",
        "desc": "Full Wan 2.1 (14B). Cinematic quality, needs 40GB+ VRAM. ⚠️ Not yet working on Mac."
    },
    "wan2.1_i2v_480p": {
        "family": "wan", "type": "video",
        "desc": "Wan 2.1 image-to-video at 480p. ⚠️ Not yet working on Mac."
    },
    "wan2.1_i2v_720p": {
        "family": "wan", "type": "video",
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
    # Video
    "ltx2": {"type": "video", "desc": "LTX-2 video model. Fast text-to-video generation."},
    "ltxv": {"type": "video", "desc": "Original LTX Video. Reliable motion generation."},
    "wan": {"type": "video", "desc": "Wan video model. High-quality motion and composition."},
    "hunyuan": {"type": "video", "desc": "Tencent's video model. Good quality, moderate speed."},
    # Image
    "sdxl": {"type": "image", "desc": "SDXL image model. High-res, versatile generation."},
    "dreamshaper": {"type": "image", "desc": "Artistic, painterly style. Great for fantasy."},
    "realvis": {"type": "image", "desc": "Photorealistic images. Best for lifelike results."},
    "flux": {"type": "image", "desc": "Latest generation. Best prompt following and quality."},
    "sd15": {"type": "image", "desc": "Classic SD 1.5. Fast, lightweight, huge community."},
    # Speech/TTS
    "chatterbox": {"type": "speech", "desc": "Voice cloning TTS. Expression tags, two quality modes.", "backend": "direct"},
    "xtts": {"type": "speech", "desc": "Coqui XTTS. Multilingual voice cloning, natural prosody.", "backend": "comfyui"},
    "f5tts": {"type": "speech", "desc": "F5-TTS. Fast, high-quality zero-shot voice cloning.", "backend": "comfyui"},
    "bark": {"type": "speech", "desc": "Bark by Suno. Expressive with laughs, music, effects.", "backend": "comfyui"},
    "tortoise": {"type": "speech", "desc": "TorToise TTS. Slow but exceptional quality.", "backend": "comfyui"},
    "styletts": {"type": "speech", "desc": "StyleTTS2. Fast, natural-sounding synthesis.", "backend": "comfyui"},
    # Music/Audio
    "musicgen": {"type": "music", "desc": "Meta MusicGen. Text-to-music, melody conditioning.", "backend": "comfyui"},
    "musicgen_large": {"type": "music", "desc": "MusicGen Large. Higher quality, longer generations.", "backend": "comfyui"},
    "stable_audio": {"type": "music", "desc": "Stability AI. Music + sound effects, variable length.", "backend": "comfyui"},
    "audiocraft": {"type": "music", "desc": "Meta AudioCraft. Full audio generation suite.", "backend": "comfyui"},
    "riffusion": {"type": "music", "desc": "Riffusion. Real-time music from spectrograms.", "backend": "comfyui"},
    "audioldm": {"type": "music", "desc": "AudioLDM. Text-to-audio, sound effects.", "backend": "comfyui"},
    "audioldm2": {"type": "music", "desc": "AudioLDM2. Improved quality, speech + music.", "backend": "comfyui"},
    # Unknown
    "unknown": {"type": "unknown", "desc": "Unrecognized model."},
}

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
                "backend": info.get("backend", "comfyui"),
            }
    
    # Second: Fall back to family detection
    family_patterns = [
        # Video
        (["ltx-2", "ltx2"], "ltx2"),
        (["ltxv", "ltx-video"], "ltxv"),
        (["wan"], "wan"),
        (["hunyuan"], "hunyuan"),
        # Image
        (["flux"], "flux"),
        (["dreamshaper"], "dreamshaper"),
        (["realvis", "realisticvision", "realistic_vision"], "realvis"),
        (["sdxl", "sd_xl"], "sdxl"),
        (["sd_", "sd1", "sd-1"], "sd15"),
        (["lightning"], "lightning"),
        # Speech/TTS
        (["chatterbox"], "chatterbox"),
        (["xtts", "coqui"], "xtts"),
        (["f5-tts", "f5tts", "f5_tts"], "f5tts"),
        (["bark"], "bark"),
        (["tortoise"], "tortoise"),
        (["styletts", "style-tts"], "styletts"),
        # Music/Audio
        (["musicgen-large", "musicgen_large"], "musicgen_large"),
        (["musicgen"], "musicgen"),
        (["stable-audio", "stable_audio", "stableaudio"], "stable_audio"),
        (["audiocraft"], "audiocraft"),
        (["riffusion"], "riffusion"),
        (["audioldm2", "audioldm-2"], "audioldm2"),
        (["audioldm"], "audioldm"),
    ]
    
    for patterns, family in family_patterns:
        if any(p in name for p in patterns):
            fallback = FAMILY_FALLBACKS.get(family, FAMILY_FALLBACKS["unknown"])
            return {
                "family": family,
                "type": fallback["type"],
                "tier": tier,
                "desc": fallback["desc"],
                "backend": fallback.get("backend", "comfyui"),
            }

    # Unknown model
    return {
        "family": "unknown",
        "type": "unknown",
        "backend": "comfyui",
        "tier": tier,
        "desc": FAMILY_FALLBACKS["unknown"]["desc"]
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
                
                # Estimate memory requirement
                vram_required = estimate_memory_required(filepath, info["family"])

                # Determine backend mode (comfyui vs direct)
                backend = info.get("backend", "comfyui")

                model = Model(
                    name=filepath.stem,
                    path=filepath,
                    family=info["family"],
                    size_gb=file_size,
                    tier_required=info["tier"],
                    media_type=info["type"],
                    description=info.get("desc", ""),
                    backend_mode=backend,
                    vram_required_gb=vram_required,
                )
                models[info["type"]].append(model)

    # Add built-in Chatterbox TTS (loads from HuggingFace, always available)
    # This is the "Direct Mode" fallback - doesn't need ComfyUI
    chatterbox_model = Model(
        name="Chatterbox TTS",
        path=Path("~/.cache/huggingface"),  # Placeholder - loads from HF
        family="chatterbox",
        size_gb=2.0,  # Approximate total size of both models
        tier_required="lite",
        media_type="speech",
        description="Built-in voice cloning. Expression tags [laugh] [sigh]. No setup needed.",
        backend_mode="direct",
        vram_required_gb=3.5,  # ~2GB model + overhead
    )
    # Insert at beginning so it's the default
    models["speech"].insert(0, chatterbox_model)

    return models

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
            "client_id": f"neovak_{int(time.time())}"
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
                                    NEOVAK_DIR / "output" / subfolder / filename if subfolder else NEOVAK_DIR / "output" / filename,
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
                                    NEOVAK_DIR / "output" / subfolder / filename if subfolder else NEOVAK_DIR / "output" / filename,
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
        progress_callback: Optional callback(GenerationProgress) for real-time updates
    
    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    from neovak_progress import track_generation_progress, GenerationProgress
    
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
            NEOVAK_DIR / "output" / output_filename,
        ]:
            if check_path.exists():
                output_path = str(check_path)
                break
        
        # Wait briefly for file system
        if not output_path:
            time.sleep(2)
            for check_path in [
                OUTPUT_DIR / output_filename,
                NEOVAK_DIR / "output" / output_filename,
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


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE EDITING (img2img, inpainting, upscaling)
# ═══════════════════════════════════════════════════════════════════════════════

# Denoise strength presets for img2img
IMG2IMG_STRENGTH_PRESETS = [
    ("Subtle", 0.3, "Light changes, keep most of original"),
    ("Moderate", 0.5, "Balanced transformation"),
    ("Strong", 0.7, "Major changes, keep structure"),
    ("Creative", 0.9, "Almost new image, guided by original"),
]

# Upscaler models commonly available in ComfyUI
UPSCALER_MODELS = [
    ("4x-UltraSharp", "Best for photos, sharp details"),
    ("4x-AnimeSharp", "Best for anime/illustrations"),
    ("ESRGAN_4x", "General purpose, good quality"),
    ("RealESRGAN_x4plus", "Realistic images, reduces noise"),
    ("RealESRGAN_x4plus_anime", "Anime-optimized"),
]


def generate_img2img(
    prompt_text: str,
    model_name: str,
    input_image_path: str,
    denoise_strength: float = 0.5,
    steps: int = 30,
    cfg: float = 7.0,
    seed: int = -1,
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Generate an image using img2img (image-to-image transformation).

    Args:
        prompt_text: The generation prompt
        model_name: Name of the model to use
        input_image_path: Path to the source image
        denoise_strength: How much to change (0=none, 1=complete redraw)
        steps: Number of sampling steps
        cfg: CFG scale
        seed: Random seed (-1 for random)
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    from neovak_progress import track_generation_progress

    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."

    # Verify input image exists
    input_path = Path(input_image_path)
    if not input_path.exists():
        return None, f"Input image not found: {input_image_path}"

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

    actual_seed = seed if seed >= 0 else random.randint(0, 2**32-1)

    # Detect model family
    is_lightning = "lightning" in model_name.lower()
    is_turbo = "turbo" in model_name.lower()

    # Build img2img workflow
    workflow = build_img2img_workflow(
        model_file=model_file,
        input_image_path=str(input_path),
        prompt=prompt_text,
        denoise=denoise_strength,
        steps=steps if not is_lightning else 4,
        cfg=cfg if not is_lightning else 1.5,
        seed=actual_seed,
        is_lightning=is_lightning,
        is_turbo=is_turbo,
    )

    # Submit and poll
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"

    prompt_id = result

    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=180, on_progress=progress_callback
    )

    if status == "completed" and output_filename:
        output_path = None
        for check_path in [OUTPUT_DIR / output_filename, NEOVAK_DIR / "output" / output_filename]:
            if check_path.exists():
                output_path = str(check_path)
                break

        if output_path:
            return output_path, f"Generated in {progress.format_time(progress.elapsed_seconds)} • Seed: {actual_seed}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Generation timed out"
    else:
        return None, f"Generation failed: {progress.error_message or status}"


def build_img2img_workflow(
    model_file: str,
    input_image_path: str,
    prompt: str,
    denoise: float,
    steps: int,
    cfg: float,
    seed: int,
    is_lightning: bool = False,
    is_turbo: bool = False,
) -> dict:
    """Build a ComfyUI workflow for img2img generation."""

    # Sampler settings based on model type
    if is_lightning:
        sampler = "euler"
        scheduler = "sgm_uniform"
    elif is_turbo:
        sampler = "dpmpp_sde"
        scheduler = "karras"
    else:
        sampler = "euler_ancestral"
        scheduler = "normal"

    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model_file}
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image_path}
        },
        "3": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["1", 2]
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1]
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",  # Negative prompt (empty)
                "clip": ["1", 1]
            }
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["3", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": denoise,
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["1", 2]
            }
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": "neovak_img2img"
            }
        }
    }


def generate_inpaint(
    prompt_text: str,
    model_name: str,
    input_image_path: str,
    mask_image_path: str,
    denoise_strength: float = 0.8,
    steps: int = 30,
    cfg: float = 7.0,
    seed: int = -1,
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Generate an image using inpainting (edit masked regions).

    Args:
        prompt_text: What to generate in the masked area
        model_name: Name of the model to use
        input_image_path: Path to the source image
        mask_image_path: Path to the mask (white = edit, black = keep)
        denoise_strength: How much to change masked area
        steps: Number of sampling steps
        cfg: CFG scale
        seed: Random seed (-1 for random)
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    from neovak_progress import track_generation_progress

    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."

    # Verify input files exist
    input_path = Path(input_image_path)
    mask_path = Path(mask_image_path)
    if not input_path.exists():
        return None, f"Input image not found: {input_image_path}"
    if not mask_path.exists():
        return None, f"Mask image not found: {mask_image_path}"

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

    actual_seed = seed if seed >= 0 else random.randint(0, 2**32-1)

    # Build inpaint workflow
    workflow = build_inpaint_workflow(
        model_file=model_file,
        input_image_path=str(input_path),
        mask_image_path=str(mask_path),
        prompt=prompt_text,
        denoise=denoise_strength,
        steps=steps,
        cfg=cfg,
        seed=actual_seed,
    )

    # Submit and poll
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"

    prompt_id = result

    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=180, on_progress=progress_callback
    )

    if status == "completed" and output_filename:
        output_path = None
        for check_path in [OUTPUT_DIR / output_filename, NEOVAK_DIR / "output" / output_filename]:
            if check_path.exists():
                output_path = str(check_path)
                break

        if output_path:
            return output_path, f"Generated in {progress.format_time(progress.elapsed_seconds)} • Seed: {actual_seed}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Generation timed out"
    else:
        return None, f"Generation failed: {progress.error_message or status}"


def build_inpaint_workflow(
    model_file: str,
    input_image_path: str,
    mask_image_path: str,
    prompt: str,
    denoise: float,
    steps: int,
    cfg: float,
    seed: int,
) -> dict:
    """Build a ComfyUI workflow for inpainting."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model_file}
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image_path}
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": mask_image_path}
        },
        "4": {
            "class_type": "VAEEncodeForInpaint",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["1", 2],
                "mask": ["3", 0],
                "grow_mask_by": 6,  # Feather mask edges
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1]
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            }
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["4", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": denoise,
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["1", 2]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "neovak_inpaint"
            }
        }
    }


def upscale_image(
    input_image_path: str,
    upscaler_model: str = "4x-UltraSharp",
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Upscale an image using an upscaler model.

    Args:
        input_image_path: Path to the image to upscale
        upscaler_model: Name of the upscaler model
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    from neovak_progress import track_generation_progress

    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."

    # Verify input image exists
    input_path = Path(input_image_path)
    if not input_path.exists():
        return None, f"Input image not found: {input_image_path}"

    # Build upscale workflow
    workflow = build_upscale_workflow(
        input_image_path=str(input_path),
        upscaler_model=upscaler_model,
    )

    # Submit and poll
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"

    prompt_id = result

    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=300, on_progress=progress_callback
    )

    if status == "completed" and output_filename:
        output_path = None
        for check_path in [OUTPUT_DIR / output_filename, NEOVAK_DIR / "output" / output_filename]:
            if check_path.exists():
                output_path = str(check_path)
                break

        if output_path:
            return output_path, f"Upscaled in {progress.format_time(progress.elapsed_seconds)}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Upscaling timed out"
    else:
        return None, f"Upscaling failed: {progress.error_message or status}"


def build_upscale_workflow(input_image_path: str, upscaler_model: str) -> dict:
    """Build a ComfyUI workflow for image upscaling."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image_path}
        },
        "2": {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": f"{upscaler_model}.pth"}
        },
        "3": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {
                "upscale_model": ["2", 0],
                "image": ["1", 0]
            }
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["3", 0],
                "filename_prefix": "neovak_upscaled"
            }
        }
    }


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
    from neovak_progress import track_generation_progress
    
    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."
    
    # Detect model family and select workflow
    import platform
    is_mac = platform.system() == "Darwin"
    
    model_lower = model_name.lower()
    if "wan" in model_lower:
        if is_mac:
            return None, "Wan models not yet supported on Mac (fp8 text encoder incompatible with MPS). Use LTX-Video instead."
        workflow_name = "wan21_t2v_api.json"
        model_family = "wan"
    elif "ltx" in model_lower:
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
    else:
        # LTX workflow parameterization
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
            NEOVAK_DIR / "output" / output_filename,
        ]:
            if check_path.exists():
                output_path = str(check_path)
                break
        
        # Wait briefly for file system
        if not output_path:
            time.sleep(2)
            for check_path in [
                OUTPUT_DIR / output_filename,
                NEOVAK_DIR / "output" / output_filename,
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


# ═══════════════════════════════════════════════════════════════════════════════
# VOICE/SPEECH GENERATION (Chatterbox TTS)
# ═══════════════════════════════════════════════════════════════════════════════

# Voice model state - lazy loaded
_voice_models = {"turbo": None, "standard": None, "loading": False, "error": None}
_voice_lock = None

def _get_voice_lock():
    """Get or create the voice model lock (thread-safe initialization)."""
    global _voice_lock
    if _voice_lock is None:
        import threading
        _voice_lock = threading.Lock()
    return _voice_lock

def get_voice_model_status() -> tuple[bool, str]:
    """Check if voice models are loaded.

    Returns: (ready, message)
    """
    if _voice_models["error"]:
        return False, f"Error: {_voice_models['error']}"
    if _voice_models["loading"]:
        return False, "Loading voice models..."
    if _voice_models["turbo"] is not None:
        return True, "Voice models ready"
    return False, "Voice models not loaded"

def load_voice_models(progress_callback=None) -> tuple[bool, str]:
    """Load Chatterbox TTS models.

    Args:
        progress_callback: Optional callback(percent, message) for progress updates

    Returns: (success, message)
    """
    lock = _get_voice_lock()
    with lock:
        # Already loaded?
        if _voice_models["turbo"] is not None:
            return True, "Already loaded"

        # Already loading?
        if _voice_models["loading"]:
            return False, "Already loading"

        _voice_models["loading"] = True
        _voice_models["error"] = None

    try:
        import torch
        device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

        if progress_callback:
            progress_callback(10, "Loading fast voice model...")

        from chatterbox.tts_turbo import ChatterboxTurboTTS
        turbo = ChatterboxTurboTTS.from_pretrained(device)

        if progress_callback:
            progress_callback(55, "Loading quality voice model...")

        from chatterbox.tts import ChatterboxTTS
        standard = ChatterboxTTS.from_pretrained(device)

        with lock:
            _voice_models["turbo"] = turbo
            _voice_models["standard"] = standard
            _voice_models["loading"] = False

        if progress_callback:
            progress_callback(100, "Voice models ready!")

        return True, "Voice models loaded"

    except ImportError as e:
        error_msg = "Chatterbox TTS not installed. Run: pip install chatterbox-tts"
        with lock:
            _voice_models["loading"] = False
            _voice_models["error"] = error_msg
        return False, error_msg

    except Exception as e:
        error_msg = str(e)
        with lock:
            _voice_models["loading"] = False
            _voice_models["error"] = error_msg
        return False, f"Failed to load voice models: {error_msg}"

def unload_voice_models():
    """Unload voice models to free memory."""
    lock = _get_voice_lock()
    with lock:
        _voice_models["turbo"] = None
        _voice_models["standard"] = None
        _voice_models["loading"] = False
        _voice_models["error"] = None

    # Force garbage collection
    import gc
    gc.collect()

    try:
        import torch
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        elif torch.cuda.is_available():
            torch.cuda.empty_cache()
    except:
        pass

def process_voice_audio(audio, sr: int, speed: float = 1.0, semitones: int = 0):
    """Apply speed and pitch changes to audio using SoundTouch.

    Args:
        audio: numpy array of audio samples
        sr: sample rate
        speed: playback speed (0.5 to 1.5)
        semitones: pitch shift (-6 to +6)

    Returns:
        Processed audio as numpy array
    """
    if speed == 1.0 and semitones == 0:
        return audio

    import tempfile
    import soundfile as sf

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f_in:
        sf.write(f_in.name, audio, sr)
        in_path = f_in.name

    out_path = in_path.replace('.wav', '_out.wav')

    # Build soundstretch command
    cmd = ['soundstretch', in_path, out_path]
    if speed != 1.0:
        tempo_pct = (speed - 1.0) * 100
        cmd.append(f'-tempo={tempo_pct:+.1f}')
    if semitones != 0:
        cmd.append(f'-pitch={semitones:+.1f}')

    try:
        result = subprocess.run(cmd, check=True, capture_output=True)
        processed, _ = sf.read(out_path)
        return processed
    except FileNotFoundError:
        # soundstretch not installed
        print("Warning: soundstretch not found. Install with: brew install sound-touch")
        return audio
    except Exception as e:
        print(f"SoundTouch error: {e}")
        return audio
    finally:
        Path(in_path).unlink(missing_ok=True)
        Path(out_path).unlink(missing_ok=True)

def generate_speech(
    text: str,
    mode: str = "quick",
    voice_file: Optional[str] = None,
    emotion: float = 0.5,
    speed: float = 1.0,
    pitch: int = 0,
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Generate speech from text using Chatterbox TTS.

    Args:
        text: Text to convert to speech (can include tags like [laugh], [sigh])
        mode: "quick" (fast with expression tags) or "quality" (better audio, emotion control)
        voice_file: Optional path to voice sample for cloning (5-10 sec of speech)
        emotion: Emotion/exaggeration level 0-1 (quality mode only)
        speed: Playback speed 0.5-1.5
        pitch: Pitch shift in semitones -6 to +6
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    import soundfile as sf

    # Check if models are loaded
    ready, status = get_voice_model_status()
    if not ready:
        # Try to load them
        if progress_callback:
            progress_callback(0, "Loading voice models...")
        success, msg = load_voice_models(progress_callback)
        if not success:
            return None, msg

    if not text.strip():
        return None, "Please enter some text"

    start_time = time.time()

    try:
        if progress_callback:
            progress_callback(70, "Generating speech...")

        if mode == "quick":
            model = _voice_models["turbo"]
            wav = model.generate(
                text,
                audio_prompt_path=voice_file,
                temperature=0.8,
                top_p=0.95,
                repetition_penalty=1.1
            )
            sr = model.sr
        else:  # quality mode
            model = _voice_models["standard"]
            wav = model.generate(
                text,
                audio_prompt_path=voice_file,
                exaggeration=emotion,
                cfg_weight=0.5,
                temperature=1.0
            )
            sr = model.sr

        # Convert to numpy
        audio = wav.squeeze(0).numpy()

        if progress_callback:
            progress_callback(85, "Processing audio...")

        # Apply speed/pitch if needed
        audio = process_voice_audio(audio, sr, speed, pitch)

        # Save output
        timestamp = int(time.time())
        output_filename = f"voice_{timestamp}.wav"
        output_path = OUTPUT_DIR / output_filename
        sf.write(str(output_path), audio, sr)

        elapsed = time.time() - start_time

        if progress_callback:
            progress_callback(100, "Done!")

        return str(output_path), f"Generated in {elapsed:.1f}s"

    except Exception as e:
        return None, f"Generation failed: {str(e)}"

# Expression tags supported by Chatterbox Turbo
VOICE_EXPRESSION_TAGS = [
    ("[laugh]", "Laughter"),
    ("[chuckle]", "Soft laugh"),
    ("[sigh]", "Sigh"),
    ("[gasp]", "Gasp"),
    ("[cough]", "Cough"),
    ("[sniff]", "Sniff"),
    ("[groan]", "Groan"),
]

# Voice presets directory
VOICES_DIR = NEOVAK_DIR / "voices"

def get_voice_presets() -> List[str]:
    """Get list of available voice preset names."""
    presets = []
    if VOICES_DIR.exists():
        for f in sorted(VOICES_DIR.glob("*.wav")) + sorted(VOICES_DIR.glob("*.mp3")):
            presets.append(f.stem)
    return presets

def resolve_voice_preset(preset_name: str) -> Optional[str]:
    """Resolve a voice preset name to its file path."""
    if not preset_name:
        return None
    for ext in [".wav", ".mp3"]:
        path = VOICES_DIR / f"{preset_name}{ext}"
        if path.exists():
            return str(path)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# COMFYUI TTS GENERATION (BYOM - Bring Your Own Model)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_speech_comfyui(
    model: 'Model',
    text: str,
    voice_file: Optional[str] = None,
    speed: float = 1.0,
    pitch: int = 0,
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Generate speech using a TTS model through ComfyUI.

    This function routes TTS generation through ComfyUI, allowing users to
    bring their own TTS models (XTTS, F5-TTS, Bark, TorToise, StyleTTS2, etc.)

    Args:
        model: The Model object for the TTS model to use
        text: Text to convert to speech
        voice_file: Optional path to voice sample for cloning
        speed: Playback speed 0.5-1.5
        pitch: Pitch shift in semitones -6 to +6
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    if progress_callback:
        progress_callback(10, f"Loading {model.name}...")

    # Check if ComfyUI backend is available
    backend_ok, backend_status = check_backend()
    if not backend_ok:
        return None, f"ComfyUI not running. Start it first to use {model.name}."

    if progress_callback:
        progress_callback(20, "Preparing workflow...")

    # Build ComfyUI workflow for TTS
    # The workflow structure depends on which ComfyUI TTS nodes are installed
    # Common ones: ComfyUI-XTTS, ComfyUI-F5TTS, etc.
    workflow = build_tts_workflow(model, text, voice_file)

    if workflow is None:
        return None, f"No ComfyUI workflow available for {model.family}. Install the appropriate nodes."

    try:
        if progress_callback:
            progress_callback(40, "Generating speech...")

        # Queue the workflow
        import requests
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        prompt_id = result.get("prompt_id")

        if not prompt_id:
            return None, "Failed to queue TTS workflow"

        # Poll for completion
        if progress_callback:
            progress_callback(60, "Processing...")

        # Wait for output (similar to image generation)
        output_path = poll_comfyui_output(prompt_id, "audio", progress_callback)

        if output_path:
            # Apply speed/pitch post-processing if needed
            if speed != 1.0 or pitch != 0:
                if progress_callback:
                    progress_callback(90, "Applying audio effects...")
                import soundfile as sf
                audio, sr = sf.read(output_path)
                audio = process_voice_audio(audio, sr, speed, pitch)
                sf.write(output_path, audio, sr)

            if progress_callback:
                progress_callback(100, "Done!")
            return output_path, f"Generated with {model.name}"
        else:
            return None, "Generation timed out or failed"

    except Exception as e:
        return None, f"ComfyUI TTS error: {str(e)}"


def build_tts_workflow(model: 'Model', text: str, voice_file: Optional[str] = None) -> Optional[dict]:
    """Build a ComfyUI workflow for TTS generation.

    This creates the appropriate workflow based on which TTS model family
    is being used and which ComfyUI nodes are available.
    """
    # Check which TTS nodes are available in ComfyUI
    # This is model-family specific

    if model.family == "xtts":
        return build_xtts_workflow(model, text, voice_file)
    elif model.family == "f5tts":
        return build_f5tts_workflow(model, text, voice_file)
    elif model.family == "bark":
        return build_bark_workflow(model, text, voice_file)
    elif model.family == "tortoise":
        return build_tortoise_workflow(model, text, voice_file)
    elif model.family == "styletts":
        return build_styletts_workflow(model, text, voice_file)
    else:
        # Unknown model family - try generic workflow
        return None


def build_xtts_workflow(model: 'Model', text: str, voice_file: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for XTTS/Coqui TTS."""
    # Standard XTTS node workflow
    # Requires: ComfyUI-XTTS or similar node pack
    return {
        "1": {
            "class_type": "XTTSLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "XTTSGenerate",
            "inputs": {
                "model": ["1", 0],
                "text": text,
                "speaker_wav": voice_file or "",
                "language": "en",
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "voice_xtts"
            }
        }
    }


def build_f5tts_workflow(model: 'Model', text: str, voice_file: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for F5-TTS."""
    return {
        "1": {
            "class_type": "F5TTSLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "F5TTSGenerate",
            "inputs": {
                "model": ["1", 0],
                "text": text,
                "ref_audio": voice_file or "",
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "voice_f5"
            }
        }
    }


def build_bark_workflow(model: 'Model', text: str, voice_file: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for Bark TTS."""
    return {
        "1": {
            "class_type": "BarkLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "BarkGenerate",
            "inputs": {
                "model": ["1", 0],
                "text": text,
                "voice_preset": voice_file or "v2/en_speaker_6",
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "voice_bark"
            }
        }
    }


def build_tortoise_workflow(model: 'Model', text: str, voice_file: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for TorToise TTS."""
    return {
        "1": {
            "class_type": "TortoiseLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "TortoiseGenerate",
            "inputs": {
                "model": ["1", 0],
                "text": text,
                "voice_dir": voice_file or "",
                "preset": "fast",  # fast, standard, high_quality
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "voice_tortoise"
            }
        }
    }


def build_styletts_workflow(model: 'Model', text: str, voice_file: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for StyleTTS2."""
    return {
        "1": {
            "class_type": "StyleTTS2Loader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "StyleTTS2Generate",
            "inputs": {
                "model": ["1", 0],
                "text": text,
                "reference_audio": voice_file or "",
                "diffusion_steps": 5,
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "voice_styletts"
            }
        }
    }


def poll_comfyui_output(prompt_id: str, output_type: str = "image", progress_callback=None, timeout: int = 300) -> Optional[str]:
    """Poll ComfyUI for workflow completion and return output path.

    Args:
        prompt_id: The prompt ID from queueing the workflow
        output_type: "image" or "audio" to look for correct output
        progress_callback: Optional progress callback
        timeout: Maximum seconds to wait

    Returns:
        Path to output file or None if failed/timeout
    """
    import requests
    import time as time_module

    start = time_module.time()
    while time_module.time() - start < timeout:
        try:
            # Check history for this prompt
            response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        # Look for audio or image outputs
                        if output_type == "audio" and "audio" in node_output:
                            audio_info = node_output["audio"][0]
                            filename = audio_info.get("filename")
                            subfolder = audio_info.get("subfolder", "")
                            # Build full path
                            output_path = OUTPUT_DIR / filename
                            if output_path.exists():
                                return str(output_path)
                            # Try ComfyUI output folder
                            comfy_output = Path.home() / "ComfyUI" / "output" / subfolder / filename
                            if comfy_output.exists():
                                return str(comfy_output)
                        elif output_type == "image" and "images" in node_output:
                            # Handle image output (existing logic)
                            pass

            time_module.sleep(1)
            if progress_callback:
                elapsed = time_module.time() - start
                pct = min(90, 60 + (elapsed / timeout) * 30)
                progress_callback(int(pct), "Waiting for output...")

        except Exception:
            time_module.sleep(1)

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC GENERATION (ComfyUI Backend)
# ═══════════════════════════════════════════════════════════════════════════════

# Music generation presets
MUSIC_DURATION_PRESETS = [
    ("Short", 5, "~5 seconds - Jingles, stingers"),
    ("Medium", 15, "~15 seconds - Loops, transitions"),
    ("Standard", 30, "~30 seconds - Background music"),
    ("Long", 60, "~60 seconds - Full pieces"),
]

MUSIC_STYLE_TAGS = [
    ("ambient", "Atmospheric, floating"),
    ("electronic", "Synths, beats"),
    ("acoustic", "Natural instruments"),
    ("orchestral", "Cinematic, epic"),
    ("lofi", "Chill, relaxed"),
    ("rock", "Guitars, drums"),
    ("jazz", "Smooth, improvised"),
    ("classical", "Traditional, composed"),
]


def generate_music(
    model: 'Model',
    prompt: str,
    duration: int = 30,
    melody_audio: Optional[str] = None,
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Generate music using a music model through ComfyUI.

    Args:
        model: The Model object for the music model to use
        prompt: Text description of the music to generate
        duration: Target duration in seconds
        melody_audio: Optional path to audio file for melody conditioning
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    if progress_callback:
        progress_callback(10, f"Loading {model.name}...")

    # Check if ComfyUI backend is available
    backend_ok, backend_status = check_backend()
    if not backend_ok:
        return None, f"ComfyUI not running. Start it first to use {model.name}."

    if progress_callback:
        progress_callback(20, "Preparing workflow...")

    # Build ComfyUI workflow for music
    workflow = build_music_workflow(model, prompt, duration, melody_audio)

    if workflow is None:
        return None, f"No ComfyUI workflow available for {model.family}. Install the appropriate nodes."

    try:
        if progress_callback:
            progress_callback(30, "Generating music...")

        # Queue the workflow
        import requests
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
            timeout=300  # Music can take a while
        )
        response.raise_for_status()
        result = response.json()
        prompt_id = result.get("prompt_id")

        if not prompt_id:
            return None, "Failed to queue music workflow"

        # Poll for completion (longer timeout for music)
        if progress_callback:
            progress_callback(50, "Processing audio...")

        output_path = poll_comfyui_output(prompt_id, "audio", progress_callback, timeout=600)

        if output_path:
            if progress_callback:
                progress_callback(100, "Done!")
            return output_path, f"Generated {duration}s with {model.name}"
        else:
            return None, "Generation timed out or failed"

    except Exception as e:
        return None, f"Music generation error: {str(e)}"


def build_music_workflow(model: 'Model', prompt: str, duration: int, melody_audio: Optional[str] = None) -> Optional[dict]:
    """Build a ComfyUI workflow for music generation.

    Dispatches to model-family-specific workflow builders.
    """
    if model.family in ("musicgen", "musicgen_large"):
        return build_musicgen_workflow(model, prompt, duration, melody_audio)
    elif model.family == "stable_audio":
        return build_stable_audio_workflow(model, prompt, duration)
    elif model.family == "audiocraft":
        return build_audiocraft_workflow(model, prompt, duration, melody_audio)
    elif model.family == "riffusion":
        return build_riffusion_workflow(model, prompt, duration)
    elif model.family in ("audioldm", "audioldm2"):
        return build_audioldm_workflow(model, prompt, duration)
    else:
        return None


def build_musicgen_workflow(model: 'Model', prompt: str, duration: int, melody_audio: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for MusicGen."""
    # MusicGen workflow - requires ComfyUI-MusicGen or similar
    workflow = {
        "1": {
            "class_type": "MusicGenLoader",
            "inputs": {
                "model_name": str(model.path.name) if model.path.exists() else "facebook/musicgen-small",
            }
        },
        "2": {
            "class_type": "MusicGenGenerate",
            "inputs": {
                "model": ["1", 0],
                "prompt": prompt,
                "duration": duration,
                "top_k": 250,
                "top_p": 0.0,
                "temperature": 1.0,
                "cfg_coef": 3.0,
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "music_musicgen"
            }
        }
    }

    # Add melody conditioning if provided
    if melody_audio:
        workflow["4"] = {
            "class_type": "LoadAudio",
            "inputs": {"audio": melody_audio}
        }
        workflow["2"]["inputs"]["melody"] = ["4", 0]

    return workflow


def build_stable_audio_workflow(model: 'Model', prompt: str, duration: int) -> dict:
    """Build ComfyUI workflow for Stable Audio."""
    return {
        "1": {
            "class_type": "StableAudioLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "StableAudioGenerate",
            "inputs": {
                "model": ["1", 0],
                "prompt": prompt,
                "negative_prompt": "low quality, noise, distortion",
                "seconds_start": 0,
                "seconds_total": duration,
                "cfg_scale": 7.0,
                "steps": 100,
                "seed": -1,  # Random
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "music_stable"
            }
        }
    }


def build_audiocraft_workflow(model: 'Model', prompt: str, duration: int, melody_audio: Optional[str] = None) -> dict:
    """Build ComfyUI workflow for AudioCraft."""
    workflow = {
        "1": {
            "class_type": "AudioCraftLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "AudioCraftGenerate",
            "inputs": {
                "model": ["1", 0],
                "prompt": prompt,
                "duration": duration,
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "music_audiocraft"
            }
        }
    }

    if melody_audio:
        workflow["4"] = {
            "class_type": "LoadAudio",
            "inputs": {"audio": melody_audio}
        }
        workflow["2"]["inputs"]["melody_conditioning"] = ["4", 0]

    return workflow


def build_riffusion_workflow(model: 'Model', prompt: str, duration: int) -> dict:
    """Build ComfyUI workflow for Riffusion."""
    # Riffusion generates spectrograms that are converted to audio
    return {
        "1": {
            "class_type": "RiffusionLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "RiffusionGenerate",
            "inputs": {
                "model": ["1", 0],
                "prompt": prompt,
                "negative_prompt": "",
                "num_inference_steps": 50,
                "guidance_scale": 7.0,
                "duration": duration,
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "music_riffusion"
            }
        }
    }


def build_audioldm_workflow(model: 'Model', prompt: str, duration: int) -> dict:
    """Build ComfyUI workflow for AudioLDM/AudioLDM2."""
    return {
        "1": {
            "class_type": "AudioLDMLoader",
            "inputs": {
                "model_path": str(model.path),
            }
        },
        "2": {
            "class_type": "AudioLDMGenerate",
            "inputs": {
                "model": ["1", 0],
                "prompt": prompt,
                "negative_prompt": "low quality",
                "duration": duration,
                "guidance_scale": 2.5,
                "num_inference_steps": 200,
                "audio_length_in_s": float(duration),
            }
        },
        "3": {
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["2", 0],
                "filename_prefix": "music_audioldm"
            }
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLNET SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

# ControlNet preprocessor types
CONTROLNET_PREPROCESSORS = [
    ("none", "None", "Use image directly as control"),
    ("canny", "Canny Edge", "Extract edges from image"),
    ("depth", "Depth Map", "Extract depth information"),
    ("openpose", "OpenPose", "Detect human poses"),
    ("lineart", "Line Art", "Convert to line art style"),
    ("scribble", "Scribble", "Simple sketch to guide generation"),
]

# ControlNet models (common ones for SDXL)
CONTROLNET_MODELS = [
    ("controlnet-canny-sdxl-1.0", "Canny Edge", "Guide with edge detection"),
    ("controlnet-depth-sdxl-1.0", "Depth", "Guide with depth maps"),
    ("control-lora-canny-rank256", "Canny LoRA", "Lightweight canny control"),
    ("control-lora-depth-rank256", "Depth LoRA", "Lightweight depth control"),
]


def discover_controlnet_models() -> List[str]:
    """Discover available ControlNet models in ComfyUI."""
    controlnet_models = []
    for search_path in MODEL_SEARCH_PATHS:
        controlnet_dir = search_path / "controlnet"
        if controlnet_dir.exists():
            for pattern in ["*.safetensors", "*.pth", "*.bin"]:
                for fp in controlnet_dir.glob(pattern):
                    controlnet_models.append(fp.stem)
    return controlnet_models


def generate_with_controlnet(
    prompt_text: str,
    model_name: str,
    control_image_path: str,
    controlnet_model: str,
    preprocessor: str = "none",
    control_strength: float = 1.0,
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg: float = 7.0,
    seed: int = -1,
    progress_callback=None
) -> tuple[Optional[str], str]:
    """Generate an image using ControlNet guidance.

    Args:
        prompt_text: The generation prompt
        model_name: Name of the base model to use
        control_image_path: Path to the control/reference image
        controlnet_model: Name of the ControlNet model
        preprocessor: Type of preprocessor to apply (canny, depth, etc.)
        control_strength: How strongly the control image guides generation (0-1)
        width: Output image width
        height: Output image height
        steps: Number of sampling steps
        cfg: CFG scale
        seed: Random seed (-1 for random)
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (output_path or None, status_message)
    """
    import random
    from neovak_progress import track_generation_progress

    # Check backend
    running, status = check_backend()
    if not running:
        return None, "ComfyUI not running. Start it first."

    # Verify control image exists
    control_path = Path(control_image_path)
    if not control_path.exists():
        return None, f"Control image not found: {control_image_path}"

    # Find model files
    model_file = None
    for search_path in MODEL_SEARCH_PATHS:
        for pattern in ["**/*.safetensors", "**/*.ckpt"]:
            for fp in search_path.glob(pattern):
                if model_name in fp.stem:
                    model_file = fp.name
                    break

    if not model_file:
        model_file = f"{model_name}.safetensors"

    # Find ControlNet model file
    cn_model_file = None
    for search_path in MODEL_SEARCH_PATHS:
        controlnet_dir = search_path / "controlnet"
        if controlnet_dir.exists():
            for pattern in ["*.safetensors", "*.pth"]:
                for fp in controlnet_dir.glob(pattern):
                    if controlnet_model in fp.stem:
                        cn_model_file = fp.name
                        break

    if not cn_model_file:
        cn_model_file = f"{controlnet_model}.safetensors"

    actual_seed = seed if seed >= 0 else random.randint(0, 2**32-1)

    # Build ControlNet workflow
    workflow = build_controlnet_workflow(
        model_file=model_file,
        controlnet_model=cn_model_file,
        control_image_path=str(control_path),
        preprocessor=preprocessor,
        prompt=prompt_text,
        control_strength=control_strength,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
        seed=actual_seed,
    )

    # Submit and poll
    success, result = submit_workflow(workflow)
    if not success:
        return None, f"Submit failed: {result}"

    prompt_id = result

    status, output_filename, progress = track_generation_progress(
        COMFYUI_URL, prompt_id, timeout=300, on_progress=progress_callback
    )

    if status == "completed" and output_filename:
        output_path = None
        for check_path in [OUTPUT_DIR / output_filename, NEOVAK_DIR / "output" / output_filename]:
            if check_path.exists():
                output_path = str(check_path)
                break

        if output_path:
            return output_path, f"ControlNet generation complete • Seed: {actual_seed}"
        else:
            return None, f"Output file not found: {output_filename}"
    elif status == "timeout":
        return None, "Generation timed out"
    else:
        return None, f"Generation failed: {progress.error_message or status}"


def build_controlnet_workflow(
    model_file: str,
    controlnet_model: str,
    control_image_path: str,
    preprocessor: str,
    prompt: str,
    control_strength: float,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    seed: int,
) -> dict:
    """Build a ComfyUI workflow for ControlNet generation.

    This is a simplified workflow that works with most ControlNet setups.
    For advanced use cases, custom workflows can be loaded from files.
    """
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model_file}
        },
        "2": {
            "class_type": "ControlNetLoader",
            "inputs": {"control_net_name": controlnet_model}
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": control_image_path}
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1]
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "",
                "clip": ["1", 1]
            }
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },
    }

    # Add preprocessor if needed
    if preprocessor == "canny":
        workflow["7"] = {
            "class_type": "CannyEdgePreprocessor",
            "inputs": {
                "image": ["3", 0],
                "low_threshold": 100,
                "high_threshold": 200,
            }
        }
        control_image_node = "7"
    elif preprocessor == "depth":
        workflow["7"] = {
            "class_type": "MiDaS-DepthMapPreprocessor",
            "inputs": {
                "image": ["3", 0],
                "a": 6.283185307179586,
                "bg_threshold": 0.1,
            }
        }
        control_image_node = "7"
    elif preprocessor == "lineart":
        workflow["7"] = {
            "class_type": "LineArtPreprocessor",
            "inputs": {
                "image": ["3", 0],
                "coarse": "disable",
            }
        }
        control_image_node = "7"
    else:
        # No preprocessor - use image directly
        control_image_node = "3"

    # Apply ControlNet
    workflow["8"] = {
        "class_type": "ControlNetApplyAdvanced",
        "inputs": {
            "positive": ["4", 0],
            "negative": ["5", 0],
            "control_net": ["2", 0],
            "image": [control_image_node, 0],
            "strength": control_strength,
            "start_percent": 0.0,
            "end_percent": 1.0,
        }
    }

    # KSampler
    workflow["9"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": ["8", 0],
            "negative": ["8", 1],
            "latent_image": ["6", 0],
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "denoise": 1.0,
        }
    }

    # VAE Decode
    workflow["10"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["9", 0],
            "vae": ["1", 2]
        }
    }

    # Save
    workflow["11"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["10", 0],
            "filename_prefix": "neovak_controlnet"
        }
    }

    return workflow
