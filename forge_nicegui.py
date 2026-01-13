"""
🔥 Forge - Local AI Creative Suite
Version 1.0.0 - Pro Edition

A unified interface for AI image, video, voice, and music generation.
Think "LM Studio for multimedia generation."

Uses NiceGUI with professional tool aesthetic inspired by Affinity Photo / Apple Keynote.
Backend logic in forge_backend.py.
"""

from nicegui import ui, app
from pathlib import Path
import asyncio

from forge_backend import (
    SYSTEM, OUTPUT_DIR, MODEL_SEARCH_PATHS,
    Model, discover_all_models,
    check_backend, generate_image, generate_video, enhance_prompt,
    estimate_memory_required,
    # Voice generation
    generate_speech, get_voice_model_status, load_voice_models, unload_voice_models,
    get_voice_presets, resolve_voice_preset, VOICE_EXPRESSION_TAGS, VOICES_DIR,
    # Music generation
    generate_music, MUSIC_DURATION_PRESETS, MUSIC_STYLE_TAGS,
    # Image editing
    generate_img2img, generate_inpaint, upscale_image,
    IMG2IMG_STRENGTH_PRESETS, UPSCALER_MODELS,
    # Presets system
    Preset, load_presets, add_preset, delete_preset, get_presets_for_tab,
    # Batch generation
    BatchJob, BatchConfig, create_batch_jobs, get_batch_status,
    # ControlNet
    generate_with_controlnet, discover_controlnet_models,
    CONTROLNET_PREPROCESSORS, CONTROLNET_MODELS,
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "Forge"
APP_VERSION = "1.0.0"

# Image mode presets
IMAGE_MODES = [
    ("generate", "Generate", "Create new images from prompts"),
    ("variations", "Variations", "Create variations of existing images"),
    ("inpaint", "Inpaint", "Draw mask and regenerate areas"),
    ("upscale", "Upscale", "Enhance resolution of images"),
]

# Batch generation presets
BATCH_SIZE_PRESETS = [
    (2, "2 images"),
    (4, "4 images"),
    (8, "8 images"),
    (16, "16 images"),
]

BATCH_SEED_MODES = [
    ("random", "Random", "Different random seed for each"),
    ("sequential", "Sequential", "Increment seed for each"),
    ("fixed", "Fixed", "Same seed for all"),
]

# Simplified presets - named for USE CASE, not technical specs
DIMENSION_PRESETS = [
    ("Square", 1024, 1024, "Profile pics, icons, social posts"),
    ("Portrait", 832, 1216, "People, characters, vertical art"),
    ("Landscape", 1216, 832, "Scenes, environments, banners"),
    ("Wide", 1344, 768, "Cinematic, desktop wallpapers"),
    ("Tall", 768, 1344, "Phone wallpapers, stories"),
    ("Custom", 1024, 1024, "Set your own dimensions"),
]

QUALITY_PRESETS = [
    ("Fast", 15, 5, "Quick iterations"),
    ("Good", 30, 7, "Balanced quality"),
    ("Best", 45, 7.5, "Final renders"),
]

# Video-specific presets
VIDEO_SIZE_PRESETS = [
    ("Standard", 512, 320, "Default LTX, fastest"),
    ("Wide", 768, 432, "16:9, cinematic"),
    ("HD", 768, 512, "Higher quality"),
    ("Vertical", 320, 512, "TikTok/Reels"),
]

VIDEO_DURATION_PRESETS = [
    ("Short", 25, "~1 second"),
    ("Medium", 49, "~2 seconds"),
    ("Long", 81, "~3 seconds"),
]

VIDEO_QUALITY_PRESETS = [
    ("Draft", 20, 3.0, "Quick preview"),
    ("Good", 30, 3.5, "Balanced quality"),
    ("Best", 40, 4.0, "Final render"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS - Professional Tool Aesthetic (Affinity/Keynote inspired)
# ═══════════════════════════════════════════════════════════════════════════════

CUSTOM_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════════════════
   FORGE v1.0.0 - Professional Tool Aesthetic
   Inspired by Affinity Photo / Apple Keynote
   Clean, restrained, functional
   ═══════════════════════════════════════════════════════════════════════════════ */

/* COLOR SYSTEM - Cyan accent used sparingly */
:root {
    --accent: #06b6d4;
    --accent-hover: #22d3ee;
    --accent-muted: rgba(6, 182, 212, 0.15);
    --surface-0: #000000;
    --surface-1: #0a0a0a;
    --surface-2: #111111;
    --surface-3: #1a1a1a;
    --surface-4: #222222;
    --border: #2a2a2a;
    --border-subtle: #1f1f1f;
    --text-primary: #ffffff;
    --text-secondary: #999999;
    --text-muted: #666666;
}

/* BASE */
* {
    transition: background-color 0.15s ease, border-color 0.15s ease,
                color 0.15s ease, opacity 0.15s ease;
}
.nicegui-content { background: var(--surface-1) !important; }

/* TYPOGRAPHY */
.forge-title { font-size: 1.5rem; font-weight: 600; color: var(--text-primary); }
.forge-subtitle { font-size: 0.875rem; color: var(--text-secondary); }
.forge-section { font-size: 0.6875rem; font-weight: 500; text-transform: uppercase;
                 letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 0.75rem; }
.forge-section-header { font-size: 0.6875rem; font-weight: 600; text-transform: uppercase;
                        letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 0.75rem; }
.forge-label { font-size: 0.8125rem; font-weight: 500; color: var(--text-secondary); }
.forge-hint { font-size: 0.75rem; color: var(--text-muted); }

/* PANELS */
.forge-card {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
}
.forge-card:hover { border-color: var(--border) !important; }
.forge-card-elevated {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

/* COMMAND BAR - Top bar with model + prompt + actions */
.forge-command-bar {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
}
.forge-command-prompt input {
    background: transparent !important;
    border: none !important;
    color: var(--text-primary) !important;
    font-size: 0.9375rem !important;
}
.forge-command-prompt .q-field__control { background: transparent !important; border: none !important; }

/* HERO AREA - Centered output display */
.forge-hero-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.5rem;
    min-height: 400px;
}
.forge-hero-container {
    background: var(--surface-0) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    width: 100%;
    max-width: 640px;
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
}
.forge-hero-container img { max-width: 100%; max-height: 100%; object-fit: contain; }

/* VIDEO CONTAINER */
.forge-video-container {
    background: var(--surface-0) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    width: 100%;
    max-width: 768px;
    aspect-ratio: 16/10;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

/* QUICK ACTIONS BAR */
.forge-quick-actions {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    background: var(--surface-2);
    border-radius: 6px;
    margin-top: 0.75rem;
}
.forge-quick-actions button {
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-secondary) !important;
}
.forge-quick-actions button:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}

/* HISTORY STRIP - Horizontal thumbnails */
.forge-history-strip {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    overflow-x: auto;
    max-width: 100%;
}
.forge-history-item {
    width: 64px;
    height: 64px;
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    border: 2px solid transparent;
    flex-shrink: 0;
    opacity: 0.8;
}
.forge-history-item:hover {
    opacity: 1;
    border-color: var(--accent);
}
.forge-history-item img { width: 100%; height: 100%; object-fit: cover; }

/* MODE TABS */
.forge-mode-tabs {
    display: flex;
    gap: 0.25rem;
    background: var(--surface-2);
    padding: 4px;
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
}
.forge-mode-tab {
    padding: 0.5rem 1rem !important;
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    background: transparent !important;
}
.forge-mode-tab:hover { color: var(--text-secondary) !important; }
.forge-mode-tab.active {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}

/* BUTTONS */
.forge-btn-primary {
    background: var(--accent) !important;
    color: var(--surface-0) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 6px !important;
}
.forge-btn-primary:hover { background: var(--accent-hover) !important; }
.forge-btn-primary:disabled { opacity: 0.5; }

.forge-preset {
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.875rem !important;
    font-size: 0.8125rem !important;
}
.forge-preset:hover {
    background: var(--surface-4) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}
.forge-preset-active {
    background: var(--accent-muted) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

.forge-enhance-btn {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
}
.forge-enhance-btn:hover {
    background: var(--surface-4) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* SETTINGS BAR - Bottom presets */
.forge-settings-bar {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1rem 1.5rem;
}
.forge-preset-group { min-width: 120px; }
.forge-preset-label {
    font-size: 0.625rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}
.forge-preset-options { display: flex; flex-direction: column; gap: 0.25rem; }
.forge-radio-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.8125rem;
}
.forge-radio-option:hover { background: var(--surface-3); color: var(--text-primary); }
.forge-radio-option.selected { color: var(--accent); }
.forge-radio-option .radio-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    border: 2px solid var(--border);
    background: transparent;
}
.forge-radio-option.selected .radio-dot {
    border-color: var(--accent);
    background: var(--accent);
}

/* INPUTS */
.forge-prompt textarea {
    font-size: 1rem !important;
    line-height: 1.6 !important;
    padding: 1rem !important;
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
}
.forge-prompt textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-muted) !important;
}

.q-field--dark .q-field__control {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
}
.q-field--dark .q-field__native { color: var(--text-primary) !important; }

/* TABS */
.q-tabs {
    background: var(--surface-2) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    border: 1px solid var(--border-subtle) !important;
}
.q-tab {
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    min-height: 36px !important;
}
.q-tab:hover { color: var(--text-secondary) !important; }
.q-tab--active {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}
.q-tab-panel { padding: 0 !important; }
.q-tabs__content--align-center .q-tab__indicator { display: none !important; }

/* DROPDOWNS */
.q-menu {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5) !important;
}
.q-item {
    border-radius: 4px !important;
    margin: 2px 4px !important;
    color: var(--text-secondary) !important;
}
.q-item:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}
.q-item__label { color: inherit !important; }
.forge-model-item { padding: 0.75rem 1rem !important; border-radius: 8px !important; margin: 0.25rem !important; }
.forge-model-item:hover { background: var(--surface-4) !important; }

/* SLIDERS */
.q-slider__track { background: var(--surface-4) !important; height: 4px !important; border-radius: 2px !important; }
.q-slider__inner { background: var(--accent) !important; border-radius: 2px !important; }
.q-slider__thumb { background: var(--text-primary) !important; border: none !important; width: 14px !important; height: 14px !important; }
.q-slider__focus-ring { background: var(--accent-muted) !important; }

/* PROGRESS */
.forge-progress { background: var(--surface-3) !important; border-radius: 4px !important; height: 6px !important; }
.forge-progress .q-linear-progress__track { background: transparent !important; }
.forge-progress .q-linear-progress__model { background: var(--accent) !important; }
.forge-progress-text { font-size: 0.8125rem; color: var(--text-secondary); font-weight: 500; }

/* TRANSPORT CONTROLS (Video) */
.forge-transport {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    background: var(--surface-2);
    border-radius: 6px;
    margin-top: 0.75rem;
}
.forge-transport-btn {
    background: transparent !important;
    color: var(--text-secondary) !important;
}
.forge-transport-btn:hover { color: var(--text-primary) !important; }
.forge-transport-btn.active { color: var(--accent) !important; }

/* SEED DISPLAY */
.forge-seed-display {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-family: monospace;
}

/* SOURCE UPLOAD */
.forge-source-upload {
    width: 120px;
    height: 120px;
    background: var(--surface-3);
    border: 2px dashed var(--border);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    overflow: hidden;
}
.forge-source-upload:hover { border-color: var(--accent); }

/* MODE INPUT AREAS */
.forge-mode-input-area {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}

/* ADVANCED TOGGLE */
.forge-advanced-toggle { background: transparent !important; }
.forge-advanced-toggle .q-expansion-item__container { background: transparent !important; }

/* EXPANSION PANELS */
.q-expansion-item {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
}
.q-expansion-item__container { background: transparent !important; }
.q-expansion-item--expanded { border-color: var(--border) !important; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--surface-4); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--border); }

/* TOOLTIP */
.q-tooltip {
    background: var(--surface-4) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    font-size: 0.75rem !important;
}

/* STATUS */
.forge-status-ready { background: #22c55e; }
.forge-status-error { background: #ef4444; }

/* ─────────────────────────────────────────────────────────────────────────────
   IMAGE PANEL - Enhanced Output-Centric Layout
   ───────────────────────────────────────────────────────────────────────────── */

/* Image container - slightly larger than video, dynamic aspect */
.forge-image-container {
    background: var(--surface-0) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden;
    max-width: 768px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
}
.forge-image-container img {
    max-width: 100%;
    max-height: 600px;
    width: auto;
    height: auto;
    display: block;
}

/* Quick actions bar below output */
.forge-quick-action-btn {
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.75rem !important;
    font-size: 0.8125rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.375rem !important;
}
.forge-quick-action-btn:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
    border-color: var(--border) !important;
}
.forge-quick-action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Image history items - square thumbnails */
.forge-history-item-img {
    display: inline-block;
    width: 60px;
    height: 60px;
    background: var(--surface-3);
    border: 2px solid transparent;
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.15s ease;
    margin-right: 0.5rem;
}
.forge-history-item-img:hover {
    border-color: var(--accent);
    transform: scale(1.05);
}
.forge-history-item-img.active {
    border-color: var(--accent);
}
.forge-history-item-img img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Video container enhancement */
.forge-video-container video {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* Frame upload for guided video generation */
.forge-frame-upload {
    width: 120px;
    height: 80px;
    background: var(--surface-3);
    border: 2px dashed var(--border);
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
}
.forge-frame-upload:hover {
    border-color: var(--accent);
    background: var(--accent-muted);
}
.forge-frame-upload img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 4px;
}
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INSPIRATION PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

INSPIRATION_PROMPTS = [
    "A cozy coffee shop on a rainy evening, warm light spilling through foggy windows",
    "An astronaut planting flowers on Mars, Earth visible in the pink sky",
    "A treehouse library with fairy lights, books floating in mid-air",
    "A fox wearing a detective's coat, investigating a mystery in autumn leaves",
    "Underwater city with bioluminescent buildings and swimming cars",
    "A grandmother robot teaching origami to curious children",
    "Mountain temple at sunrise, cherry blossoms drifting in golden light",
    "Steampunk hot air balloon festival above Victorian London",
    "A friendly dragon running a bakery, smoke curling from brick ovens",
    "Northern lights reflecting in a perfectly still arctic lake",
    "Cyberpunk ramen shop, neon signs reflecting in rain puddles",
    "A cat astronomer mapping constellations from a rooftop observatory",
]

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATION HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

generation_history = []

def add_to_history(path: str, prompt: str, model: str, seed: int = -1):
    """Add a generation to history."""
    generation_history.insert(0, {
        'path': path,
        'prompt': prompt,
        'model': model,
        'seed': seed,
        'timestamp': __import__('time').time()
    })
    if len(generation_history) > 20:
        generation_history.pop()

# ═══════════════════════════════════════════════════════════════════════════════
# THEME & STATE
# ═══════════════════════════════════════════════════════════════════════════════

def setup_theme():
    """Configure theme and inject custom CSS."""
    ui.add_head_html(CUSTOM_CSS)
    ui.add_head_html("""
    <script>
    document.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            const genBtn = document.querySelector('[data-forge-generate]');
            if (genBtn) genBtn.click();
        }
    });
    </script>
    """)
    ui.colors(
        primary='#06b6d4',
        secondary='#f59e0b',
        accent='#06b6d4',
        dark='#0a0a0b',
        positive='#22c55e',
        negative='#ef4444',
        info='#3b82f6',
        warning='#f59e0b',
    )
    ui.dark_mode().enable()

ALL_MODELS = {}

def init_models():
    """Discover models on system."""
    global ALL_MODELS
    ALL_MODELS = discover_all_models()
    total = sum(len(m) for m in ALL_MODELS.values())
    print(f"📦 Discovered {total} models")
    return total

def get_app_state():
    """Determine app state for onboarding."""
    total_models = sum(len(m) for m in ALL_MODELS.values())
    backend_ok, _ = check_backend()
    if total_models == 0:
        return "no_models"
    elif not backend_ok:
        return "no_backend"
    else:
        return "ready"

# ═══════════════════════════════════════════════════════════════════════════════
# WELCOME / ONBOARDING SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

def welcome_no_models():
    """Shown when no models are discovered."""
    with ui.column().classes('w-full max-w-2xl mx-auto items-center py-12'):
        ui.label('🔥').classes('text-6xl mb-4')
        ui.label('Welcome to Forge').classes('forge-title')
        ui.label('Your local AI creative studio').classes('forge-subtitle mb-8')

        with ui.card().classes('w-full forge-card p-6'):
            ui.label('📦 No AI models found').classes('text-xl text-white font-semibold mb-4')
            ui.label('Forge automatically discovers models in these folders:').classes('forge-hint mb-3')

            with ui.column().classes('gap-1 mb-4 bg-zinc-800 rounded-lg p-3'):
                for path in MODEL_SEARCH_PATHS:
                    ui.label(f'• {path}').classes('text-zinc-400 text-sm font-mono')

            ui.label('To get started, download a model:').classes('forge-hint mb-3')

            with ui.card().classes('w-full bg-cyan-950/50 border border-cyan-800 p-4 mb-4'):
                ui.label('Recommended first model').classes('text-cyan-300 text-sm font-semibold mb-2')
                ui.label('DreamShaper XL').classes('text-white text-lg font-semibold')
                ui.label('Artistic images with dreamy, painterly style. 6.5 GB.').classes('text-zinc-400 text-sm')
                ui.link('Download from CivitAI →', 'https://civitai.com/models/112902/dreamshaper-xl').classes('text-cyan-400 text-sm mt-2')

            with ui.row().classes('gap-3'):
                ui.button('Rescan for models', on_click=lambda: ui.navigate.to('/')).props('outline').classes('text-zinc-300')

def welcome_no_backend():
    """Shown when models exist but ComfyUI isn't running."""
    with ui.column().classes('w-full max-w-2xl mx-auto items-center py-12'):
        ui.label('🔥').classes('text-6xl mb-4')
        ui.label('Almost ready!').classes('forge-title')
        ui.label('Forge found your models, but ComfyUI needs to be running').classes('forge-subtitle mb-8')

        total = sum(len(m) for m in ALL_MODELS.values())
        ui.label(f'✓ Found {total} models on your system').classes('text-green-400 mb-6')

        comfyui_path = Path.home() / "Documents" / "AI-Projects" / "ComfyUI"
        if not comfyui_path.exists():
            comfyui_path = Path.home() / "ComfyUI"

        with ui.card().classes('w-full forge-card p-6'):
            ui.label('Start ComfyUI Backend').classes('text-xl text-white font-semibold mb-4')

            async def start_comfyui():
                import subprocess
                status_label.set_text('Starting ComfyUI...')
                start_btn.disable()
                try:
                    subprocess.Popen(
                        ['python3', 'main.py'],
                        cwd=str(comfyui_path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    for i in range(30):
                        await asyncio.sleep(1)
                        status_label.set_text(f'Waiting for ComfyUI... ({i+1}s)')
                        backend_ok, _ = check_backend()
                        if backend_ok:
                            ui.notify('ComfyUI is ready!', type='positive')
                            ui.navigate.to('/')
                            return
                    status_label.set_text('ComfyUI taking longer than expected...')
                    start_btn.enable()
                except Exception as e:
                    status_label.set_text(f'Error: {e}')
                    start_btn.enable()

            start_btn = ui.button('🚀 Start ComfyUI', on_click=start_comfyui).classes('forge-btn-primary w-full mb-4')
            status_label = ui.label('').classes('text-zinc-400 text-sm')

            ui.separator().classes('my-4')
            ui.label('Or start manually:').classes('forge-hint mb-3')
            with ui.card().classes('w-full bg-zinc-800 p-4 mb-4'):
                ui.label(f'cd {comfyui_path} && python main.py').classes('text-green-400 font-mono text-sm')

            ui.button('Check again', on_click=lambda: ui.navigate.to('/')).props('outline').classes('text-zinc-300')

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

def app_header():
    """Compact header with live status indicator."""
    with ui.row().classes('w-full max-w-5xl mx-auto justify-between items-center py-3 px-2'):
        with ui.row().classes('items-center gap-3'):
            ui.label('🔥').classes('text-2xl')
            with ui.column().classes('gap-0'):
                ui.label('Forge').classes('text-lg font-bold text-white leading-tight')
                available = SYSTEM.get_available_memory_gb()
                pressure = SYSTEM.get_memory_pressure()
                pressure_colors = {"low": "text-green-400", "medium": "text-yellow-400", "high": "text-orange-400", "critical": "text-red-400"}
                mem_label = ui.label(f'{SYSTEM.chip} • {available:.0f}GB free').classes(f'text-xs {pressure_colors.get(pressure, "text-zinc-500")}')

                def update_memory_display():
                    avail = SYSTEM.get_available_memory_gb()
                    press = SYSTEM.get_memory_pressure()
                    mem_label.set_text(f'{SYSTEM.chip} • {avail:.0f}GB free')
                    mem_label.classes(remove='text-green-400 text-yellow-400 text-orange-400 text-red-400 text-zinc-500')
                    mem_label.classes(add=pressure_colors.get(press, "text-zinc-500"))

                ui.timer(10.0, update_memory_display)

        with ui.row().classes('items-center gap-2'):
            status_icon = ui.icon('circle', color='gray').classes('text-xs')
            status_label = ui.label('Checking...').classes('text-sm text-zinc-400')

            async def update_status():
                backend_ok, msg = check_backend()
                if backend_ok:
                    status_icon._props['color'] = 'green'
                    status_label.set_text('Ready')
                    status_label.classes(remove='text-zinc-400 text-red-400', add='text-green-400')
                else:
                    status_icon._props['color'] = 'red'
                    status_label.set_text('Offline')
                    status_label.classes(remove='text-zinc-400 text-green-400', add='text-red-400')
                status_icon.update()

            ui.timer(0.1, update_status, once=True)
            ui.timer(10.0, update_status)

def update_history_strip(refs, state):
    """Update the horizontal history strip with recent images."""
    if 'history_container' not in refs:
        return
    refs['history_container'].clear()

    with refs['history_container']:
        for item in generation_history[:15]:
            def show_image(path=item['path'], prompt=item['prompt'], seed=item.get('seed', 0)):
                refs['output_img'].set_source(path)
                refs['output_img'].classes(remove='hidden')
                refs['placeholder_col'].set_visibility(False)
                state['last_output'] = path
                state['last_seed'] = seed
                refs['seed_display'].set_text(f'Seed: {seed}')
                refs['seed_display'].classes(remove='hidden')
                ui.notify(f'"{prompt[:40]}..."' if len(prompt) > 40 else f'"{prompt}"', position='top', timeout=2000)

            with ui.element('div').classes('forge-history-item').on('click', show_image):
                ui.image(item['path']).classes('w-full h-full object-cover')

# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE GENERATION PANEL - Professional Centered Layout
# ═══════════════════════════════════════════════════════════════════════════════

def image_generation_panel():
    """Image generation with centered hero area layout."""
    models = [m for m in ALL_MODELS.get("image", []) if m.available_on_system()]

    if not models:
        with ui.column().classes('items-center justify-center py-12 gap-6 max-w-lg mx-auto'):
            ui.icon('image', size='64px').classes('text-zinc-600')
            ui.label('No image models found').classes('text-zinc-400 text-xl')
            ui.label('Download a model to start creating').classes('text-zinc-500 text-sm')

            with ui.card().classes('w-full forge-card p-5 mt-2'):
                ui.label('QUICK START').classes('forge-section-header mb-4')
                with ui.column().classes('gap-3'):
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('bolt', size='24px').classes('text-amber-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('DreamShaper 8').classes('font-medium text-white')
                            ui.label('2GB • Fast & versatile').classes('text-zinc-400 text-xs')
                        ui.link('Download', 'https://civitai.com/api/download/models/128713', new_tab=True).classes('text-cyan-400 text-sm')
                ui.separator().classes('my-3')
                ui.label('Place .safetensors in: ComfyUI/models/checkpoints/').classes('text-zinc-500 text-xs')
        return

    # State
    state = {
        'mode': 'generate',
        'model': models[0],
        'width': 1024, 'height': 1024,
        'steps': 30, 'cfg': 7,
        'dim_preset': 0, 'quality_preset': 1,
        'last_seed': None, 'last_output': None,
        'variation_source': None, 'variation_strength': 0.65,
        'upscale_source': None, 'upscale_factor': 4,
        'inpaint_image': None, 'inpaint_mask': None,
    }
    refs = {}

    def set_mode(mode_id):
        state['mode'] = mode_id
        for mid, btn in refs['mode_tab_buttons'].items():
            if mid == mode_id:
                btn.classes(add='active')
            else:
                btn.classes(remove='active')
        refs['variations_section'].set_visibility(mode_id == 'variations')
        refs['inpaint_section'].set_visibility(mode_id == 'inpaint')
        refs['upscale_section'].set_visibility(mode_id == 'upscale')

    with ui.column().classes('w-full gap-4'):
        # ─────────────────────────────────────────────────────────────────────
        # COMMAND BAR (Top) - Model + Prompt + Enhance + Create
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full forge-command-bar items-center gap-3'):
            def on_model_select(m):
                state['model'] = m
                refs['model_btn'].text = m.name

            with ui.dropdown_button(models[0].name, auto_close=True).classes('shrink-0').props('no-caps dropdown-icon=expand_more color=dark dense') as refs['model_btn']:
                for m in models:
                    with ui.item(on_click=lambda m=m: on_model_select(m)).classes('forge-model-item'):
                        with ui.column().classes('gap-0.5 py-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(m.name).classes('text-white font-medium')
                                ui.badge(m.family).props('color=primary outline dense')
                                ui.label(f'{m.size_gb:.1f}GB').classes('text-zinc-500 text-xs')

            refs['prompt'] = ui.input(placeholder='Describe what you want to create...').classes('flex-1 forge-command-prompt').props('dense outlined')

            def set_random_prompt():
                import random
                refs['prompt'].value = random.choice(INSPIRATION_PROMPTS)
                ui.notify('✨ Try this idea!', type='positive', position='top', timeout=1500)

            ui.button('🎲', on_click=set_random_prompt).props('flat dense').tooltip('Random inspiration')

            def do_enhance():
                original = refs['prompt'].value or ''
                if not original.strip():
                    ui.notify('Write something first!', type='warning')
                    return
                enhanced = enhance_prompt(original)
                refs['prompt'].value = enhanced
                ui.notify('✨ Enhanced!', type='positive', position='top', timeout=1500)

            ui.button('✨', on_click=do_enhance).props('flat dense').classes('forge-enhance-btn').tooltip('Enhance prompt')

            refs['gen_btn'] = ui.button('Create', on_click=lambda: do_generate()).props('no-caps').classes('forge-btn-primary')
            refs['gen_btn']._props['data-forge-generate'] = 'true'

        # ─────────────────────────────────────────────────────────────────────
        # HERO AREA (Center) - Image Display + Quick Actions
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-hero-area w-full'):
            with ui.element('div').classes('forge-image-container'):
                refs['placeholder_col'] = ui.column().classes('items-center gap-2')
                with refs['placeholder_col']:
                    ui.icon('image', size='48px').classes('text-zinc-600')
                    ui.label('Your creation will appear here').classes('text-zinc-500 text-sm')

                refs['output_img'] = ui.image('').classes('hidden')

            # Quick actions bar
            with ui.row().classes('forge-quick-actions items-center gap-2'):
                refs['seed_display'] = ui.label('').classes('forge-seed-display hidden')

                async def copy_seed():
                    if state['last_seed']:
                        await ui.run_javascript(f'navigator.clipboard.writeText("{state["last_seed"]}")')
                        ui.notify(f'Seed {state["last_seed"]} copied!', type='positive', position='top', timeout=1500)

                refs['copy_seed_btn'] = ui.button('📋 Copy Seed', on_click=copy_seed).props('flat dense no-caps').classes('forge-quick-action-btn hidden').tooltip('Copy seed')

                async def download_image():
                    if state['last_output']:
                        await ui.run_javascript(f'''
                            const a = document.createElement("a");
                            a.href = "{state["last_output"]}";
                            a.download = "forge_image.png";
                            a.click();
                        ''')

                refs['download_btn'] = ui.button('⬇ Download', on_click=download_image).props('flat dense no-caps').classes('forge-quick-action-btn hidden').tooltip('Download')

            # Progress bar
            with ui.column().classes('w-full max-w-lg gap-1 mt-3'):
                refs['progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full forge-progress')
                refs['progress'].set_visibility(False)
                refs['progress_text'] = ui.label('').classes('forge-progress-text text-center w-full')
                refs['progress_text'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # HISTORY STRIP - Horizontal scroll of recent images
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-history-strip w-full') as history_strip:
            refs['history_container'] = history_strip
            if not generation_history:
                ui.label('Recent creations will appear here').classes('text-zinc-500 text-xs')

        # ─────────────────────────────────────────────────────────────────────
        # MODE TABS - Generate, Variations, Inpaint, Upscale
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('forge-mode-tabs'):
            refs['mode_tab_buttons'] = {}
            for mode_id, mode_label, _ in IMAGE_MODES:
                btn = ui.button(mode_label, on_click=lambda m=mode_id: set_mode(m)).props('flat no-caps')
                btn.classes('forge-mode-tab' + (' active' if mode_id == 'generate' else ''))
                refs['mode_tab_buttons'][mode_id] = btn

        # ─────────────────────────────────────────────────────────────────────
        # MODE-SPECIFIC INPUT AREAS
        # ─────────────────────────────────────────────────────────────────────

        # Variations mode inputs
        with ui.column().classes('w-full forge-mode-input-area') as variations_section:
            refs['variations_section'] = variations_section
            ui.label('SOURCE IMAGE').classes('forge-section-header mb-3')
            with ui.row().classes('items-start gap-6'):
                with ui.column().classes('items-center gap-2'):
                    refs['variation_source'] = ui.element('div').classes('forge-source-upload')
                    with refs['variation_source']:
                        refs['variation_source_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['variation_source_placeholder'] = ui.column().classes('items-center')
                        with refs['variation_source_placeholder']:
                            ui.icon('add_photo_alternate', size='32px').classes('text-zinc-500')
                            ui.label('Upload').classes('text-zinc-500 text-xs')

                    async def handle_variation_upload(e):
                        if e.content:
                            import tempfile, base64
                            content = e.content.read()
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                                f.write(content)
                                state['variation_source'] = f.name
                            refs['variation_source_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
                            refs['variation_source_preview'].classes(remove='hidden')
                            refs['variation_source_placeholder'].set_visibility(False)
                            ui.notify('Source image loaded', type='positive')

                    refs['variation_upload'] = ui.upload(on_upload=handle_variation_upload, auto_upload=True).props('accept=image/* flat dense').classes('hidden')
                    refs['variation_source'].on('click', lambda: refs['variation_upload'].run_method('pickFiles'))

                with ui.column().classes('gap-2 flex-1'):
                    ui.label('Variation Strength').classes('text-zinc-400 text-xs')
                    with ui.row().classes('items-center gap-3'):
                        refs['variation_strength'] = ui.slider(min=0.3, max=1.0, value=0.65, step=0.05).classes('flex-1')
                        refs['variation_strength_label'] = ui.label('0.65').classes('text-zinc-300 text-xs w-10')
                        refs['variation_strength'].on('update:model-value', lambda e: refs['variation_strength_label'].set_text(f'{e.args:.2f}'))
                    ui.label('Low = subtle changes, High = major changes').classes('text-zinc-500 text-xs')
        refs['variations_section'].set_visibility(False)

        # Inpaint mode inputs
        with ui.column().classes('w-full forge-mode-input-area') as inpaint_section:
            refs['inpaint_section'] = inpaint_section
            ui.label('INPAINT EDITOR').classes('forge-section-header mb-3')
            ui.label('Upload an image and draw on it to mask areas for regeneration').classes('text-zinc-500 text-sm')
        refs['inpaint_section'].set_visibility(False)

        # Upscale mode inputs
        with ui.column().classes('w-full forge-mode-input-area') as upscale_section:
            refs['upscale_section'] = upscale_section
            ui.label('UPSCALE').classes('forge-section-header mb-3')
            with ui.row().classes('items-start gap-6'):
                with ui.column().classes('items-center gap-2'):
                    refs['upscale_source'] = ui.element('div').classes('forge-source-upload')
                    with refs['upscale_source']:
                        refs['upscale_source_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['upscale_source_placeholder'] = ui.column().classes('items-center')
                        with refs['upscale_source_placeholder']:
                            ui.icon('add_photo_alternate', size='32px').classes('text-zinc-500')
                            ui.label('Upload').classes('text-zinc-500 text-xs')

                    async def handle_upscale_upload(e):
                        if e.content:
                            import tempfile, base64
                            content = e.content.read()
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                                f.write(content)
                                state['upscale_source'] = f.name
                            refs['upscale_source_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
                            refs['upscale_source_preview'].classes(remove='hidden')
                            refs['upscale_source_placeholder'].set_visibility(False)
                            ui.notify('Image loaded for upscale', type='positive')

                    refs['upscale_upload'] = ui.upload(on_upload=handle_upscale_upload, auto_upload=True).props('accept=image/* flat dense').classes('hidden')
                    refs['upscale_source'].on('click', lambda: refs['upscale_upload'].run_method('pickFiles'))

                with ui.column().classes('gap-3'):
                    ui.label('Scale').classes('text-zinc-400 text-xs')
                    def select_scale(scale):
                        state['upscale_factor'] = scale
                        refs['scale_2x'].props('color=primary' if scale == 2 else 'color=dark')
                        refs['scale_4x'].props('color=primary' if scale == 4 else 'color=dark')
                    with ui.row().classes('gap-2'):
                        refs['scale_2x'] = ui.button('2×', on_click=lambda: select_scale(2)).props('dense no-caps color=dark')
                        refs['scale_4x'] = ui.button('4×', on_click=lambda: select_scale(4)).props('dense no-caps color=primary')
        refs['upscale_section'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # SETTINGS BAR (Bottom) - Size and Quality presets
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full forge-settings-bar gap-8'):
            # SIZE presets
            with ui.column().classes('forge-preset-group'):
                ui.label('SIZE').classes('forge-preset-label')
                refs['size_options'] = {}

                def select_size(idx):
                    state['dim_preset'] = idx
                    name, w, h, _ = DIMENSION_PRESETS[idx]
                    state['width'] = w
                    state['height'] = h
                    for i, opt in refs['size_options'].items():
                        if i == idx:
                            opt.classes(add='selected')
                        else:
                            opt.classes(remove='selected')
                    refs['custom_size_row'].set_visibility(name == 'Custom')

                with ui.column().classes('forge-preset-options'):
                    for i, (name, w, h, hint) in enumerate(DIMENSION_PRESETS):
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 0 else '')) as opt:
                            opt.on('click', lambda i=i: select_size(i))
                            ui.element('div').classes('radio-dot')
                            with ui.row().classes('items-center gap-2'):
                                ui.label(name).classes('text-zinc-200')
                                ui.label(f'{w}×{h}').classes('text-zinc-500 text-xs')
                            opt.tooltip(hint)
                        refs['size_options'][i] = opt

                with ui.row().classes('gap-2 items-center mt-2') as custom_row:
                    refs['custom_size_row'] = custom_row
                    refs['custom_width'] = ui.number(value=1024, min=256, max=2048, step=8).classes('w-20').props('dense outlined')
                    ui.label('×').classes('text-zinc-400')
                    refs['custom_height'] = ui.number(value=1024, min=256, max=2048, step=8).classes('w-20').props('dense outlined')
                    def apply_custom():
                        state['width'] = int(refs['custom_width'].value)
                        state['height'] = int(refs['custom_height'].value)
                    ui.button('Apply', on_click=apply_custom).props('dense no-caps size=sm')
                refs['custom_size_row'].set_visibility(False)

            # QUALITY presets
            with ui.column().classes('forge-preset-group'):
                ui.label('QUALITY').classes('forge-preset-label')
                refs['quality_options'] = {}

                def select_quality(idx):
                    state['quality_preset'] = idx
                    _, steps, cfg, _ = QUALITY_PRESETS[idx]
                    state['steps'] = steps
                    state['cfg'] = cfg
                    for i, opt in refs['quality_options'].items():
                        if i == idx:
                            opt.classes(add='selected')
                        else:
                            opt.classes(remove='selected')

                with ui.column().classes('forge-preset-options'):
                    for i, (name, steps, cfg, hint) in enumerate(QUALITY_PRESETS):
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 1 else '')) as opt:
                            opt.on('click', lambda i=i: select_quality(i))
                            ui.element('div').classes('radio-dot')
                            ui.label(name).tooltip(f'{steps} steps, CFG {cfg} - {hint}')
                        refs['quality_options'][i] = opt

            ui.element('div').classes('flex-1')  # Spacer

            # Advanced settings
            with ui.expansion('▾ Advanced', value=False).classes('forge-advanced-toggle').props('dense'):
                with ui.row().classes('gap-6 p-3'):
                    with ui.column().classes('gap-2'):
                        ui.label('Seed').classes('text-zinc-400 text-xs')
                        refs['seed'] = ui.number(value=-1).classes('w-28').props('dense outlined')
                        ui.label('-1 = random').classes('text-zinc-500 text-xs')
                    with ui.column().classes('gap-2'):
                        ui.label('Steps').classes('text-zinc-400 text-xs')
                        refs['steps_slider'] = ui.slider(min=10, max=60, value=30).classes('w-32')
                    with ui.column().classes('gap-2'):
                        ui.label('CFG').classes('text-zinc-400 text-xs')
                        refs['cfg_slider'] = ui.slider(min=1, max=15, value=7, step=0.5).classes('w-32')

    # ═══════════════════════════════════════════════════════════════════════════════
    # GENERATE FUNCTION
    # ═══════════════════════════════════════════════════════════════════════════════

    async def do_generate():
        mode = state['mode']
        prompt = refs['prompt'].value

        if mode == 'generate' and not prompt:
            ui.notify('Please describe what you want to create', type='warning')
            return
        if mode == 'variations' and not state['variation_source']:
            ui.notify('Please upload a source image', type='warning')
            return
        if mode == 'upscale' and not state['upscale_source']:
            ui.notify('Please upload an image to upscale', type='warning')
            return

        refs['gen_btn'].disable()
        refs['gen_btn'].text = '⏳ Creating...'
        refs['progress'].set_visibility(True)
        refs['progress_text'].set_visibility(True)

        import time as time_module
        start_time = time_module.time()
        is_generating = True

        steps = state['steps']
        cfg = state['cfg']
        seed = int(refs['seed'].value) if refs['seed'].value else -1

        estimated_total = steps * 0.8 + 5

        async def update_progress():
            nonlocal is_generating
            while is_generating:
                elapsed = time_module.time() - start_time
                progress = min(0.95, elapsed / estimated_total)
                remaining = max(0, estimated_total - elapsed)
                refs['progress'].set_value(progress)
                refs['progress_text'].set_text(f'⏳ {int(elapsed)}s elapsed • ~{int(remaining)}s remaining')
                await asyncio.sleep(0.5)

        progress_task = asyncio.create_task(update_progress())

        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        state['last_seed'] = seed

        try:
            if mode == 'generate':
                output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: generate_image(
                        prompt_text=prompt,
                        model_name=state['model'].name,
                        width=state['width'],
                        height=state['height'],
                        steps=steps,
                        cfg=cfg,
                        seed=seed,
                    )
                )
            elif mode == 'variations':
                output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: generate_img2img(
                        prompt_text=prompt or 'variation',
                        model_name=state['model'].name,
                        input_image_path=state['variation_source'],
                        denoise_strength=state['variation_strength'],
                        steps=steps,
                        cfg=cfg,
                        seed=seed,
                    )
                )
            elif mode == 'upscale':
                output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: upscale_image(
                        input_image_path=state['upscale_source'],
                        upscaler_model='4x-UltraSharp',
                    )
                )
            else:
                output_path, status_msg = None, 'Mode not implemented'

            is_generating = False
            elapsed = time_module.time() - start_time

            if output_path:
                state['last_output'] = output_path
                refs['placeholder_col'].set_visibility(False)
                refs['output_img'].classes(remove='hidden')
                refs['output_img'].set_source(output_path)
                refs['progress'].set_value(1.0)
                refs['progress_text'].set_text(f'✓ Complete in {int(elapsed)}s')

                refs['seed_display'].set_text(f'Seed: {seed}')
                refs['seed_display'].classes(remove='hidden')
                refs['copy_seed_btn'].classes(remove='hidden')
                refs['download_btn'].classes(remove='hidden')

                ui.notify('Image created!', type='positive')
                add_to_history(output_path, prompt or f'[{mode}]', state['model'].name, seed)
                update_history_strip(refs, state)
            else:
                refs['progress_text'].set_text(f'✗ {status_msg}')
                ui.notify(status_msg, type='negative')
        except Exception as e:
            is_generating = False
            refs['progress_text'].set_text(f'✗ Error: {str(e)}')
            ui.notify(str(e), type='negative')
        finally:
            is_generating = False
            progress_task.cancel()
            refs['gen_btn'].enable()
            refs['gen_btn'].text = 'Create'
            await asyncio.sleep(2)
            refs['progress'].set_visibility(False)
            refs['progress_text'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO GENERATION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def video_generation_panel():
    """Video generation panel with centered layout."""
    video_models = [m for m in ALL_MODELS.get('video', []) if m.available_on_system()]

    if not video_models:
        with ui.column().classes('items-center justify-center py-12 gap-6 max-w-lg mx-auto'):
            ui.icon('movie', size='64px').classes('text-zinc-600')
            ui.label('No video models found').classes('text-zinc-400 text-xl')
            ui.label('Download a model to start creating videos').classes('text-zinc-500 text-sm')

            with ui.card().classes('w-full forge-card p-5 mt-2'):
                ui.label('QUICK START').classes('forge-section-header mb-4')
                with ui.column().classes('gap-3'):
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('star', size='24px').classes('text-amber-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('LTX-Video 0.9.1').classes('font-medium text-white')
                            ui.label('5GB • Works great on Mac').classes('text-zinc-400 text-xs')
                        ui.link('Download', 'https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.1.safetensors', new_tab=True).classes('text-cyan-400 text-sm')
                ui.separator().classes('my-3')
                ui.label('Place .safetensors in: ComfyUI/models/checkpoints/').classes('text-zinc-500 text-xs')
        return

    state = {
        'model': video_models[0],
        'width': 512, 'height': 320,
        'num_frames': 25,
        'steps': 30, 'cfg': 3.5,
        'last_output': None, 'last_seed': None,
        'loop_enabled': True,
    }
    refs = {}

    with ui.column().classes('w-full gap-4'):
        # Command bar
        with ui.row().classes('w-full forge-command-bar items-center gap-3'):
            def on_video_model_select(m):
                state['model'] = m
                refs['video_model_btn'].text = m.name

            with ui.dropdown_button(video_models[0].name, auto_close=True).classes('shrink-0').props('no-caps dropdown-icon=expand_more color=dark dense') as refs['video_model_btn']:
                for m in video_models:
                    with ui.item(on_click=lambda m=m: on_video_model_select(m)).classes('forge-model-item'):
                        ui.label(m.name).classes('text-white font-medium')

            refs['video_prompt'] = ui.input(placeholder='Describe the video you want to create...').classes('flex-1 forge-command-prompt').props('dense outlined')

            def do_enhance_video():
                original = refs['video_prompt'].value or ''
                if not original.strip():
                    ui.notify('Write something first!', type='warning')
                    return
                enhanced = enhance_prompt(original, style="cinematic")
                refs['video_prompt'].value = enhanced
                ui.notify('✨ Enhanced!', type='positive', position='top', timeout=1500)

            ui.button('✨', on_click=do_enhance_video).props('flat dense').classes('forge-enhance-btn').tooltip('Enhance')

            refs['video_gen_btn'] = ui.button('Create', on_click=lambda: do_generate_video()).props('no-caps').classes('forge-btn-primary')

        # Hero area for video
        with ui.element('div').classes('forge-hero-area w-full'):
            with ui.element('div').classes('forge-video-container'):
                refs['video_placeholder'] = ui.column().classes('items-center gap-2')
                with refs['video_placeholder']:
                    ui.icon('movie', size='48px').classes('text-zinc-600')
                    ui.label('Your video will appear here').classes('text-zinc-500 text-sm')

                refs['output_video'] = ui.video('').classes('w-full h-full object-contain hidden').props('loop')

            # Transport controls
            with ui.row().classes('forge-transport items-center'):
                async def video_play_pause():
                    await ui.run_javascript('''
                        const video = document.querySelector('.forge-video-container video');
                        if (video) { video.paused ? video.play() : video.pause(); }
                    ''')

                ui.button(icon='play_arrow', on_click=video_play_pause).props('flat dense').classes('forge-transport-btn').tooltip('Play/Pause')

                refs['video_seed_display'] = ui.label('').classes('forge-seed-display hidden ml-auto')

            # Progress
            with ui.column().classes('w-full max-w-lg gap-1 mt-3'):
                refs['video_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full forge-progress')
                refs['video_progress'].set_visibility(False)
                refs['video_progress_text'] = ui.label('').classes('forge-progress-text text-center w-full')
                refs['video_progress_text'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # VIDEO HISTORY STRIP
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-history-strip w-full') as video_history:
            refs['video_history_container'] = video_history
            ui.label('Recent videos will appear here').classes('text-zinc-500 text-xs')

        # Settings bar
        with ui.row().classes('w-full forge-settings-bar gap-8'):
            with ui.column().classes('forge-preset-group'):
                ui.label('SIZE').classes('forge-preset-label')
                refs['video_size_btns'] = []
                with ui.row().classes('gap-2'):
                    for i, (name, w, h, _) in enumerate(VIDEO_SIZE_PRESETS):
                        def select_video_size(idx=i, ww=w, hh=h):
                            state['width'] = ww
                            state['height'] = hh
                            for j, btn in enumerate(refs['video_size_btns']):
                                btn.props('color=primary' if j == idx else 'color=dark')
                        btn = ui.button(name, on_click=select_video_size).props(f'dense no-caps {"color=primary" if i == 0 else "color=dark"}')
                        refs['video_size_btns'].append(btn)

            with ui.column().classes('forge-preset-group'):
                ui.label('DURATION').classes('forge-preset-label')
                refs['video_dur_btns'] = []
                with ui.row().classes('gap-2'):
                    for i, (name, frames, _) in enumerate(VIDEO_DURATION_PRESETS):
                        def select_dur(idx=i, f=frames):
                            state['num_frames'] = f
                            for j, btn in enumerate(refs['video_dur_btns']):
                                btn.props('color=primary' if j == idx else 'color=dark')
                        btn = ui.button(name, on_click=select_dur).props(f'dense no-caps {"color=primary" if i == 0 else "color=dark"}')
                        refs['video_dur_btns'].append(btn)

            with ui.column().classes('forge-preset-group'):
                ui.label('QUALITY').classes('forge-preset-label')
                refs['video_qual_btns'] = []
                with ui.row().classes('gap-2'):
                    for i, (name, steps, cfg, _) in enumerate(VIDEO_QUALITY_PRESETS):
                        def select_qual(idx=i, s=steps, c=cfg):
                            state['steps'] = s
                            state['cfg'] = c
                            for j, btn in enumerate(refs['video_qual_btns']):
                                btn.props('color=primary' if j == idx else 'color=dark')
                        btn = ui.button(name, on_click=select_qual).props(f'dense no-caps {"color=primary" if i == 1 else "color=dark"}')
                        refs['video_qual_btns'].append(btn)

    async def do_generate_video():
        prompt = refs['video_prompt'].value
        if not prompt:
            ui.notify('Please describe the video', type='warning')
            return

        refs['video_gen_btn'].disable()
        refs['video_gen_btn'].text = '⏳ Creating...'
        refs['video_progress'].set_visibility(True)
        refs['video_progress_text'].set_visibility(True)

        import time as time_module
        start_time = time_module.time()
        estimated_total = state['steps'] * 3 + 30
        is_generating = True

        async def update_progress():
            nonlocal is_generating
            while is_generating:
                elapsed = time_module.time() - start_time
                progress = min(0.95, elapsed / estimated_total)
                remaining = max(0, estimated_total - elapsed)
                refs['video_progress'].set_value(progress)
                refs['video_progress_text'].set_text(f'⏳ {int(elapsed)}s • ~{int(remaining)}s remaining')
                await asyncio.sleep(0.5)

        progress_task = asyncio.create_task(update_progress())

        import random
        seed = random.randint(0, 2**32 - 1)
        state['last_seed'] = seed

        try:
            output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate_video(
                    prompt_text=prompt,
                    model_name=state['model'].name,
                    width=state['width'],
                    height=state['height'],
                    num_frames=state['num_frames'],
                    steps=state['steps'],
                    cfg=state['cfg'],
                    seed=seed,
                )
            )

            is_generating = False
            elapsed = time_module.time() - start_time

            if output_path:
                state['last_output'] = output_path
                refs['video_placeholder'].set_visibility(False)
                refs['output_video'].classes(remove='hidden')
                refs['output_video'].set_source(output_path)
                refs['video_progress'].set_value(1.0)
                refs['video_progress_text'].set_text(f'✓ Complete in {int(elapsed)}s')
                refs['video_seed_display'].set_text(f'Seed: {seed}')
                refs['video_seed_display'].classes(remove='hidden')
                ui.notify('Video created!', type='positive')
            else:
                refs['video_progress_text'].set_text(f'✗ {status_msg}')
                ui.notify(status_msg, type='negative')
        except Exception as e:
            is_generating = False
            refs['video_progress_text'].set_text(f'✗ Error')
            ui.notify(str(e), type='negative')
        finally:
            is_generating = False
            progress_task.cancel()
            refs['video_gen_btn'].enable()
            refs['video_gen_btn'].text = 'Create'
            await asyncio.sleep(2)
            refs['video_progress'].set_visibility(False)
            refs['video_progress_text'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE GENERATION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def voice_generation_panel():
    """Voice generation with Chatterbox TTS."""
    state = {'speed': 1.0, 'voice_sample': None}
    refs = {}

    with ui.column().classes('w-full max-w-2xl mx-auto gap-6 py-6'):
        ui.label('🗣️ Voice Generation').classes('forge-title')
        ui.label('Text-to-speech with expression tags').classes('forge-subtitle mb-4')

        with ui.card().classes('w-full forge-card p-6'):
            ui.label('TEXT').classes('forge-section-header')
            refs['text'] = ui.textarea(placeholder='Enter text to speak... Use tags like [laugh], [sigh], [gasp] for expressions').classes('w-full forge-prompt').props('outlined autogrow rows=4')

            ui.label('EXPRESSION TAGS').classes('forge-section-header mt-4')
            with ui.row().classes('gap-2 flex-wrap'):
                for tag in VOICE_EXPRESSION_TAGS:
                    def add_tag(t=tag):
                        refs['text'].value = (refs['text'].value or '') + f' [{t}]'
                    ui.button(f'[{tag}]', on_click=add_tag).props('flat dense size=sm').classes('text-zinc-400')

            ui.label('SPEED').classes('forge-section-header mt-4')
            with ui.row().classes('items-center gap-4'):
                refs['speed'] = ui.slider(min=0.5, max=2.0, value=1.0, step=0.1).classes('flex-1')
                refs['speed_label'] = ui.label('1.0x').classes('text-zinc-300 w-12')
                refs['speed'].on('update:model-value', lambda e: refs['speed_label'].set_text(f'{e.args:.1f}x'))

        refs['voice_gen_btn'] = ui.button('🎤 Generate Voice', on_click=lambda: do_generate_voice()).classes('w-full forge-btn-primary')

        with ui.column().classes('w-full gap-2'):
            refs['voice_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full forge-progress')
            refs['voice_progress'].set_visibility(False)
            refs['voice_status'] = ui.label('').classes('text-zinc-400 text-sm')

        refs['audio_output'] = ui.audio('').classes('w-full hidden')

    async def do_generate_voice():
        text = refs['text'].value
        if not text:
            ui.notify('Enter some text first', type='warning')
            return

        refs['voice_gen_btn'].disable()
        refs['voice_progress'].set_visibility(True)
        refs['voice_status'].set_text('Generating speech...')

        try:
            output_path, status = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate_speech(
                    text=text,
                    speed=refs['speed'].value,
                )
            )

            if output_path:
                refs['audio_output'].set_source(output_path)
                refs['audio_output'].classes(remove='hidden')
                refs['voice_status'].set_text('✓ Voice generated!')
                ui.notify('Voice generated!', type='positive')
            else:
                refs['voice_status'].set_text(f'✗ {status}')
                ui.notify(status, type='negative')
        except Exception as e:
            refs['voice_status'].set_text(f'✗ Error')
            ui.notify(str(e), type='negative')
        finally:
            refs['voice_gen_btn'].enable()
            refs['voice_progress'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC GENERATION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def music_generation_panel():
    """Music generation panel."""
    state = {'duration': 15, 'style': None}
    refs = {}

    with ui.column().classes('w-full max-w-2xl mx-auto gap-6 py-6'):
        ui.label('🎵 Music Generation').classes('forge-title')
        ui.label('Create music from text descriptions').classes('forge-subtitle mb-4')

        with ui.card().classes('w-full forge-card p-6'):
            ui.label('DESCRIPTION').classes('forge-section-header')
            refs['music_prompt'] = ui.textarea(placeholder='Describe the music you want... e.g., "upbeat electronic dance track with synths"').classes('w-full forge-prompt').props('outlined autogrow rows=3')

            ui.label('STYLE').classes('forge-section-header mt-4')
            with ui.row().classes('gap-2 flex-wrap'):
                for tag in MUSIC_STYLE_TAGS[:8]:
                    def add_style(t=tag):
                        refs['music_prompt'].value = (refs['music_prompt'].value or '') + f' {t}'
                    ui.button(tag, on_click=add_style).props('flat dense size=sm').classes('text-zinc-400')

            ui.label('DURATION').classes('forge-section-header mt-4')
            refs['duration_btns'] = []
            with ui.row().classes('gap-2'):
                for dur, label in MUSIC_DURATION_PRESETS:
                    def select_dur(d=dur, idx=MUSIC_DURATION_PRESETS.index((dur, label))):
                        state['duration'] = d
                        for j, btn in enumerate(refs['duration_btns']):
                            btn.props('color=primary' if j == idx else 'color=dark')
                    btn = ui.button(label, on_click=select_dur).props(f'dense no-caps {"color=primary" if dur == 15 else "color=dark"}')
                    refs['duration_btns'].append(btn)

        refs['music_gen_btn'] = ui.button('🎵 Generate Music', on_click=lambda: do_generate_music()).classes('w-full forge-btn-primary')

        with ui.column().classes('w-full gap-2'):
            refs['music_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full forge-progress')
            refs['music_progress'].set_visibility(False)
            refs['music_status'] = ui.label('').classes('text-zinc-400 text-sm')

        refs['music_output'] = ui.audio('').classes('w-full hidden')

    async def do_generate_music():
        prompt = refs['music_prompt'].value
        if not prompt:
            ui.notify('Describe the music you want', type='warning')
            return

        refs['music_gen_btn'].disable()
        refs['music_progress'].set_visibility(True)
        refs['music_status'].set_text('Generating music...')

        try:
            output_path, status = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate_music(
                    prompt_text=prompt,
                    duration=state['duration'],
                )
            )

            if output_path:
                refs['music_output'].set_source(output_path)
                refs['music_output'].classes(remove='hidden')
                refs['music_status'].set_text('✓ Music generated!')
                ui.notify('Music generated!', type='positive')
            else:
                refs['music_status'].set_text(f'✗ {status}')
                ui.notify(status, type='negative')
        except Exception as e:
            refs['music_status'].set_text(f'✗ Error')
            ui.notify(str(e), type='negative')
        finally:
            refs['music_gen_btn'].enable()
            refs['music_progress'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

@ui.page('/')
def main_page():
    """Main application page."""
    setup_theme()
    init_models()

    app_state = get_app_state()

    if app_state == "no_models":
        welcome_no_models()
        return

    if app_state == "no_backend":
        welcome_no_backend()
        return

    # Main app layout
    with ui.column().classes('w-full min-h-screen'):
        app_header()

        with ui.column().classes('w-full max-w-5xl mx-auto px-4 flex-1'):
            with ui.tabs().classes('w-full').props('align=center') as tabs:
                image_tab = ui.tab('Image', icon='image')
                video_tab = ui.tab('Video', icon='movie')
                voice_tab = ui.tab('Voice', icon='mic')
                music_tab = ui.tab('Music', icon='music_note')

            with ui.tab_panels(tabs, value=image_tab).classes('w-full flex-1'):
                with ui.tab_panel(image_tab):
                    image_generation_panel()
                with ui.tab_panel(video_tab):
                    video_generation_panel()
                with ui.tab_panel(voice_tab):
                    voice_generation_panel()
                with ui.tab_panel(music_tab):
                    music_generation_panel()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title=f'{APP_NAME} - Local AI Creative Suite',
        port=7861,
        reload=False,
        show=True,
    )
