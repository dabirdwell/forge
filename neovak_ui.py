"""
💡 NeoVak - Local AI Creative Suite
Version 1.2.0

A unified interface for AI image, video, voice, and music generation.
Think "LM Studio for multimedia generation."

Uses NiceGUI with retro-futuristic aesthetic inspired by vacuum tube technology.
Backend logic in neovak_backend.py.
"""

from nicegui import ui, app
from pathlib import Path
import asyncio

from neovak_backend import (
    SYSTEM, OUTPUT_DIR, MODEL_SEARCH_PATHS,
    Model, discover_all_models,
    check_backend, generate_image, generate_video, enhance_prompt,
    estimate_memory_required,
    # Voice generation
    generate_speech, get_voice_model_status, load_voice_models, unload_voice_models,
    get_voice_presets, resolve_voice_preset, VOICE_EXPRESSION_TAGS, VOICES_DIR,
    # Music generation (ACE-Step 1.5)
    generate_music, check_acestep_backend, MUSIC_DURATION_PRESETS, MUSIC_STYLE_TAGS,
    ACESTEP_URL, ACESTEP_DIR,
    SONG_STRUCTURE_TEMPLATES, MOOD_GRID_LABELS, mood_to_tags,
    estimate_duration_from_lyrics, mix_audio,
    # Sound effects generation
    generate_sfx, get_sfx_model_status, load_sfx_model, unload_sfx_model,
    SFX_DURATION_PRESETS, SFX_CATEGORIES, SFX_STYLE_TAGS,
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
    # Lumina's World
    IMAGE_SURPRISE_PROMPTS, IMAGE_STYLE_PRESETS, get_random_image_prompt,
    VIDEO_SURPRISE_PROMPTS, get_random_video_prompt,
    VOICE_QUICK_TEXTS, SFX_QUICK_PROMPTS, TAB_SUBTITLES,
    # Video chain generation
    extract_last_frame, extract_first_frame, concatenate_videos,
    generate_video_from_image, generate_video_chain, continue_video_chain,
)
from acestep_client import (
    format_input as acestep_format_input,
    get_random_sample, generate_music_batch, get_model_inventory,
    embed_album_art, get_lora_status, load_lora, unload_lora,
    set_lora_scale, toggle_lora,
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "NeoVak"
APP_VERSION = "1.2.0"

# Image mode presets - (id, label, tooltip)
IMAGE_MODES = [
    ("generate", "Generate", "Create new images from text descriptions. Describe what you want and the AI will paint it."),
    ("variations", "Variations", "Upload an existing image and create alternate versions. Great for exploring different styles or compositions."),
    ("inpaint", "Inpaint", "Edit specific areas of an image. Paint a mask over what you want to change, describe the replacement."),
    ("upscale", "Upscale", "Increase resolution and enhance details of existing images. Makes small images larger without blur."),
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

# Simplified presets - named for USE CASE with aspect ratio display
# Format: (name, width, height, hint, aspect_ratio)
DIMENSION_PRESETS = [
    ("Square", 1024, 1024, "Profile pics, icons, social posts", "1:1"),
    ("Portrait", 832, 1216, "People, characters, vertical art", "2:3"),
    ("Landscape", 1216, 832, "Scenes, environments, banners", "3:2"),
    ("Wide", 1344, 768, "Cinematic, desktop wallpapers", "16:9"),
    ("Tall", 768, 1344, "Phone wallpapers, stories", "9:16"),
    ("Custom", 1024, 1024, "Set your own dimensions", "—"),
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
   NEOVAK v1.2.0 - Edison Steampunk Aesthetic
   Warm tungsten glow, aged brass, patinated copper
   Inspired by Edison's Menlo Park laboratory
   ═══════════════════════════════════════════════════════════════════════════════ */

/* COLOR SYSTEM - Edison tungsten & aged brass */
:root {
    /* Edison filament glow - warm tungsten orange */
    --accent: #d4912a;
    --accent-hover: #e8a445;
    --accent-muted: rgba(212, 145, 42, 0.15);
    
    /* Tube states - filament temperature */
    --tube-cold: #3d3529;
    --tube-warm: #d4912a;
    --tube-hot: #f0c674;
    --filament-bright: #fff4e0;
    
    /* Copper & brass accents */
    --copper: #b87333;
    --brass: #c9a227;
    --patina: #4a7c6f;
    
    /* Aged surfaces - dark wood & iron */
    --surface-0: #0a0908;
    --surface-1: #12100e;
    --surface-2: #1a1714;
    --surface-3: #221f1a;
    --surface-4: #2a2620;
    
    /* Borders - oxidized metal */
    --border: #3d3529;
    --border-subtle: #2a2620;
    
    /* Text - parchment tones */
    --text-primary: #f5f0e8;
    --text-secondary: #b8a992;
    --text-muted: #7a6f5f;
}

/* BASE */
* {
    transition: background-color 0.15s ease, border-color 0.15s ease,
                color 0.15s ease, opacity 0.15s ease;
}
.nicegui-content { background: var(--surface-1) !important; }

/* TYPOGRAPHY */
.neovak-title { font-size: 1.5rem; font-weight: 600; color: var(--text-primary); }
.neovak-subtitle { font-size: 0.875rem; color: var(--text-secondary); }
.neovak-section { font-size: 0.6875rem; font-weight: 500; text-transform: uppercase;
                 letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 0.75rem; }
.neovak-section-header { font-size: 0.6875rem; font-weight: 600; text-transform: uppercase;
                        letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 0.75rem; }
.neovak-label { font-size: 0.8125rem; font-weight: 500; color: var(--text-secondary); }
.neovak-hint { font-size: 0.75rem; color: var(--text-muted); }

/* PANELS */
.neovak-card {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
}
.neovak-card:hover { border-color: var(--border) !important; }
.neovak-card-elevated {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

/* COMMAND BAR - Top bar with model + prompt + actions */
.neovak-command-bar {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
}
.neovak-command-prompt input {
    background: transparent !important;
    border: none !important;
    color: var(--text-primary) !important;
    font-size: 0.9375rem !important;
}
.neovak-command-prompt .q-field__control { background: transparent !important; border: none !important; }

/* HERO AREA - Centered output display */
.neovak-hero-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.5rem;
    min-height: 400px;
}
.neovak-hero-container {
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
.neovak-hero-container img { max-width: 100%; max-height: 100%; object-fit: contain; }

/* VIDEO CONTAINER */
.neovak-video-container {
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
.neovak-quick-actions {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    background: var(--surface-2);
    border-radius: 6px;
    margin-top: 0.75rem;
}
.neovak-quick-actions button {
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-secondary) !important;
}
.neovak-quick-actions button:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}

/* HISTORY STRIP - Horizontal thumbnails */
.neovak-history-strip {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    overflow-x: auto;
    max-width: 100%;
}
.neovak-history-item {
    width: 64px;
    height: 64px;
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    border: 2px solid transparent;
    flex-shrink: 0;
    opacity: 0.8;
}
.neovak-history-item:hover {
    opacity: 1;
    border-color: var(--accent);
}
.neovak-history-item img { width: 100%; height: 100%; object-fit: cover; }

/* MODE TABS */
.neovak-mode-tabs {
    display: flex;
    gap: 0.25rem;
    background: var(--surface-2);
    padding: 4px;
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
}
.neovak-mode-tab {
    padding: 0.5rem 1rem !important;
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    background: transparent !important;
}
.neovak-mode-tab:hover { color: var(--text-secondary) !important; }
.neovak-mode-tab.active {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}

/* BUTTONS */
.neovak-btn-primary {
    background: var(--accent) !important;
    color: var(--surface-0) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 6px !important;
}
.neovak-btn-primary:hover { background: var(--accent-hover) !important; }
.neovak-btn-primary:disabled { opacity: 0.5; }

.neovak-preset {
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.875rem !important;
    font-size: 0.8125rem !important;
}
.neovak-preset:hover {
    background: var(--surface-4) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}
.neovak-preset-active {
    background: var(--accent-muted) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

.neovak-enhance-btn {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
}
.neovak-enhance-btn:hover {
    background: var(--surface-4) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* SETTINGS BAR - Bottom presets */
.neovak-settings-bar {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1rem 1.5rem;
}
.neovak-preset-group { min-width: 120px; }
.neovak-preset-label {
    font-size: 0.625rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}
.neovak-preset-options { display: flex; flex-direction: column; gap: 0.25rem; }

/* VISUAL ASPECT RATIO SELECTOR */
.neovak-aspect-selector {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.neovak-aspect-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    background: var(--surface-2);
    border: 2px solid transparent;
    transition: all 0.2s ease;
    min-width: 64px;
}
.neovak-aspect-option:hover {
    background: var(--surface-3);
    border-color: var(--border);
}
.neovak-aspect-option.selected {
    border-color: var(--accent);
    background: var(--accent-muted);
}
.neovak-aspect-shape {
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.neovak-aspect-shape-inner {
    background: var(--surface-4);
    border: 1px solid var(--border);
    border-radius: 2px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.neovak-aspect-option.selected .neovak-aspect-shape-inner {
    background: var(--accent);
    border-color: var(--accent);
    box-shadow: 0 0 8px var(--accent-muted);
}
.neovak-aspect-name {
    font-size: 0.6875rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.neovak-aspect-option.selected .neovak-aspect-name {
    color: var(--accent);
}
.neovak-aspect-dims {
    font-size: 0.625rem;
    color: var(--text-muted);
    font-family: 'SF Mono', Monaco, monospace;
}

.neovak-radio-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.8125rem;
}
.neovak-radio-option:hover { background: var(--surface-3); color: var(--text-primary); }
.neovak-radio-option.selected { color: var(--accent); }
.neovak-radio-option .radio-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    border: 2px solid var(--border);
    background: transparent;
}
.neovak-radio-option.selected .radio-dot {
    border-color: var(--accent);
    background: var(--accent);
}

/* INPUTS */
.neovak-prompt textarea {
    font-size: 1rem !important;
    line-height: 1.6 !important;
    padding: 1rem !important;
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
}
.neovak-prompt textarea:focus {
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
.neovak-model-item { padding: 0.75rem 1rem !important; border-radius: 8px !important; margin: 0.25rem !important; }
.neovak-model-item:hover { background: var(--surface-4) !important; }

/* SLIDERS */
.q-slider__track { background: var(--surface-4) !important; height: 4px !important; border-radius: 2px !important; }
.q-slider__inner { background: var(--accent) !important; border-radius: 2px !important; }
.q-slider__thumb { background: var(--text-primary) !important; border: none !important; width: 14px !important; height: 14px !important; }
.q-slider__focus-ring { background: var(--accent-muted) !important; }

/* SLIDER WITH VALUE INPUT - Combined control */
.neovak-slider-control {
    display: flex;
    align-items: center;
    gap: 12px;
}
.neovak-slider-control .q-slider { flex: 1; }
.neovak-slider-value {
    width: 56px;
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 4px !important;
    padding: 4px 8px !important;
    font-size: 0.8125rem !important;
    font-family: 'SF Mono', Monaco, monospace !important;
    color: var(--accent) !important;
    text-align: center !important;
}
.neovak-slider-value:focus {
    border-color: var(--accent) !important;
    outline: none !important;
    box-shadow: 0 0 0 2px var(--accent-muted) !important;
}

/* Control labels with hint */
.neovak-control-label {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
}
.neovak-control-name {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-secondary);
}
.neovak-control-hint {
    font-size: 0.6875rem;
    color: var(--text-muted);
    font-style: italic;
}
.neovak-tooltip-icon {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--surface-4);
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.625rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: help;
}

/* PROGRESS */
.neovak-progress { background: var(--surface-3) !important; border-radius: 4px !important; height: 6px !important; }
.neovak-progress .q-linear-progress__track { background: transparent !important; }
.neovak-progress .q-linear-progress__model { background: var(--accent) !important; }

/* ═══════════════════════════════════════════════════════════════════════════════
   NEOVAK TUBE STATUS INDICATORS - Phase 2
   Vacuum tube-inspired status lights that show model/generation state
   ═══════════════════════════════════════════════════════════════════════════════ */

.neovak-tube {
    width: 8px;
    height: 24px;
    border-radius: 4px;
    background: var(--tube-cold);
    transition: all 0.5s ease;
    position: relative;
    overflow: hidden;
}

/* Inner glow effect */
.neovak-tube::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    bottom: 2px;
    border-radius: 2px;
    background: transparent;
    transition: all 0.5s ease;
}

/* Cold state - dark, inactive */
.neovak-tube.cold {
    background: var(--tube-cold);
    box-shadow: none;
}

/* Warming state - transitioning to active */
.neovak-tube.warming {
    background: var(--tube-warm);
    opacity: 0.7;
    animation: tube-warmup 1.5s ease-in-out;
}

/* Warm state - ready, idle */
.neovak-tube.warm {
    background: var(--tube-warm);
    box-shadow: 0 0 8px rgba(212, 145, 42, 0.5);
}

.neovak-tube.warm::after {
    background: linear-gradient(180deg, rgba(240, 198, 116, 0.3) 0%, transparent 100%);
}

/* Hot/Active state - generating */
.neovak-tube.hot {
    background: var(--tube-hot);
    box-shadow: 0 0 16px rgba(240, 198, 116, 0.6), 0 0 32px rgba(212, 145, 42, 0.4);
    animation: tube-pulse 1.2s ease-in-out infinite;
}

.neovak-tube.hot::after {
    background: linear-gradient(180deg, rgba(255, 244, 224, 0.5) 0%, rgba(240, 198, 116, 0.2) 50%, transparent 100%);
}

/* Error state - flicker */
.neovak-tube.error {
    background: #ef4444;
    animation: tube-flicker 0.3s ease-in-out 3;
}

/* Tube animations */
@keyframes tube-warmup {
    0% { opacity: 0.3; background: var(--tube-cold); }
    50% { opacity: 0.6; }
    100% { opacity: 1; background: var(--tube-warm); }
}

@keyframes tube-pulse {
    0%, 100% { 
        opacity: 0.85;
        box-shadow: 0 0 12px rgba(240, 198, 116, 0.5), 0 0 24px rgba(212, 145, 42, 0.3);
    }
    50% { 
        opacity: 1;
        box-shadow: 0 0 20px rgba(240, 198, 116, 0.7), 0 0 40px rgba(212, 145, 42, 0.5);
    }
}

@keyframes tube-flicker {
    0%, 100% { opacity: 1; }
    25% { opacity: 0.4; }
    50% { opacity: 0.8; }
    75% { opacity: 0.3; }
}

/* Tube container for multiple tubes */
.neovak-tube-bank {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 4px 8px;
    background: var(--surface-3);
    border-radius: 6px;
    border: 1px solid var(--border-subtle);
}

/* Tube with label */
.neovak-tube-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
}

.neovak-tube-label {
    font-size: 0.625rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}
.neovak-progress-text { font-size: 0.8125rem; color: var(--text-secondary); font-weight: 500; }

/* TRANSPORT CONTROLS (Video) */
.neovak-transport {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    background: var(--surface-2);
    border-radius: 6px;
    margin-top: 0.75rem;
}
.neovak-transport-btn {
    background: transparent !important;
    color: var(--text-secondary) !important;
}
.neovak-transport-btn:hover { color: var(--text-primary) !important; }
.neovak-transport-btn.active { color: var(--accent) !important; }

/* SEED DISPLAY */
.neovak-seed-display {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-family: monospace;
}

/* SOURCE UPLOAD */
.neovak-source-upload {
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
.neovak-source-upload:hover { border-color: var(--accent); }

/* MODE INPUT AREAS */
.neovak-mode-input-area {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}

/* ADVANCED TOGGLE */
.neovak-advanced-toggle { background: transparent !important; }
.neovak-advanced-toggle .q-expansion-item__container { background: transparent !important; }

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
.neovak-status-ready { background: #22c55e; }
.neovak-status-error { background: #ef4444; }

/* ─────────────────────────────────────────────────────────────────────────────
   IMAGE PANEL - Enhanced Output-Centric Layout
   ───────────────────────────────────────────────────────────────────────────── */

/* Image container - slightly larger than video, dynamic aspect */
.neovak-image-container {
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
.neovak-image-container img {
    max-width: 100%;
    max-height: 600px;
    width: auto;
    height: auto;
    display: block;
}

/* Quick actions bar below output */
.neovak-quick-action-btn {
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
.neovak-quick-action-btn:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
    border-color: var(--border) !important;
}
.neovak-quick-action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Image history items - square thumbnails */
.neovak-history-item-img {
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
.neovak-history-item-img:hover {
    border-color: var(--accent);
    transform: scale(1.05);
}
.neovak-history-item-img.active {
    border-color: var(--accent);
}
.neovak-history-item-img img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Video container enhancement */
.neovak-video-container video {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* Frame upload for guided video generation */
.neovak-frame-upload {
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
.neovak-frame-upload:hover {
    border-color: var(--accent);
    background: var(--accent-muted);
}
.neovak-frame-upload img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 4px;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   LUMINA'S WORLD — Design System Extensions
   Hexagonal progress, whisper pulse dots, tube warming, foam loading
   ═══════════════════════════════════════════════════════════════════════════════ */

/* Hexagonal progress indicator */
.neovak-hex-progress {
    background: repeating-linear-gradient(
        60deg,
        var(--surface-2) 0px,
        var(--surface-2) 10px,
        var(--surface-3) 10px,
        var(--surface-3) 20px
    );
    border-radius: 4px;
    overflow: hidden;
    height: 6px;
}
.neovak-hex-progress .bar {
    height: 100%;
    background: linear-gradient(90deg, var(--tube-warm), var(--tube-hot), var(--filament-bright));
    transition: width 0.3s ease;
}

/* Whisper pulse — ambient presence indicator */
@keyframes whisper-pulse {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1.0; transform: scale(1.15); }
}
.neovak-whisper-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--tube-warm);
    animation: whisper-pulse 3s ease-in-out infinite;
    display: inline-block;
    flex-shrink: 0;
}
.neovak-whisper-dot.cold {
    background: var(--tube-cold);
    animation: none;
}

/* Foam animation for loading/processing states */
@keyframes foam-drift {
    0% { background-position: 0% 0%; }
    100% { background-position: 100% 100%; }
}
.neovak-foam-loading {
    background: radial-gradient(circle at 20% 50%, var(--accent-muted) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, var(--accent-muted) 0%, transparent 50%),
                radial-gradient(circle at 50% 80%, var(--accent-muted) 0%, transparent 50%);
    background-size: 200% 200%;
    animation: foam-drift 4s ease-in-out infinite;
}

/* Lumina tab subtitle */
.neovak-tab-subtitle {
    font-size: 0.6875rem;
    font-style: italic;
    color: var(--text-muted);
    margin-top: 2px;
}

/* Style preset chips */
.neovak-style-chip {
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 16px !important;
    padding: 0.25rem 0.75rem !important;
    font-size: 0.75rem !important;
    cursor: pointer;
    transition: all 0.15s ease;
}
.neovak-style-chip:hover {
    background: var(--accent-muted) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
.neovak-style-chip.active {
    background: var(--accent-muted) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Sound board grid */
.neovak-soundboard-btn {
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
}
.neovak-soundboard-btn:hover {
    background: var(--surface-4) !important;
    border-color: var(--accent) !important;
}
.neovak-soundboard-btn:active {
    background: var(--accent-muted) !important;
    transform: scale(0.97);
}

/* Empty state card */
.neovak-empty-state {
    background: var(--accent-muted) !important;
    border: 1px solid rgba(212, 145, 42, 0.2) !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    text-align: center;
}

/* System status bar */
.neovak-status-bar {
    background: var(--surface-2);
    border-top: 1px solid var(--border-subtle);
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    font-size: 0.75rem;
    color: var(--text-muted);
}
.neovak-status-bar-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
}
.neovak-status-bar-separator {
    width: 1px;
    height: 16px;
    background: var(--border-subtle);
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
            const genBtn = document.querySelector('[data-neovak-generate]');
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
        ui.label('Welcome to NeoVak').classes('neovak-title')
        ui.label('Your local AI creative studio').classes('neovak-subtitle mb-8')

        with ui.card().classes('w-full neovak-card p-6'):
            ui.label('📦 No AI models found').classes('text-xl text-white font-semibold mb-4')
            ui.label('NeoVak automatically discovers models in these folders:').classes('neovak-hint mb-3')

            with ui.column().classes('gap-1 mb-4 bg-zinc-800 rounded-lg p-3'):
                for path in MODEL_SEARCH_PATHS:
                    ui.label(f'• {path}').classes('text-zinc-400 text-sm font-mono')

            ui.label('To get started, download a model:').classes('neovak-hint mb-3')

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
        ui.label('Almost ready!').classes('neovak-title')
        ui.label('NeoVak found your models, but ComfyUI needs to be running').classes('neovak-subtitle mb-8')

        total = sum(len(m) for m in ALL_MODELS.values())
        ui.label(f'✓ Found {total} models on your system').classes('text-green-400 mb-6')

        comfyui_path = Path.home() / "Documents" / "AI-Projects" / "ComfyUI"
        if not comfyui_path.exists():
            comfyui_path = Path.home() / "ComfyUI"

        with ui.card().classes('w-full neovak-card p-6'):
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

            start_btn = ui.button('🚀 Start ComfyUI', on_click=start_comfyui).classes('neovak-btn-primary w-full mb-4')
            status_label = ui.label('').classes('text-zinc-400 text-sm')

            ui.separator().classes('my-4')
            ui.label('Or start manually:').classes('neovak-hint mb-3')
            with ui.card().classes('w-full bg-zinc-800 p-4 mb-4'):
                ui.label(f'cd {comfyui_path} && python main.py').classes('text-green-400 font-mono text-sm')

            ui.button('Check again', on_click=lambda: ui.navigate.to('/')).props('outline').classes('text-zinc-300')

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

def app_header():
    """Header with Lumina branding and whisper dot status indicators."""
    with ui.row().classes('w-full max-w-5xl mx-auto justify-between items-center py-3 px-2'):
        with ui.row().classes('items-center gap-3'):
            with ui.column().classes('gap-0'):
                ui.label('NeoVak').classes('text-xl font-bold leading-tight').style('color: var(--text-primary); letter-spacing: 0.02em;')
                ui.label('Create images, video, voice, and music with AI \u2014 privately, on your Mac.').classes('text-xs').style('color: var(--text-muted); font-style: italic;')

        with ui.row().classes('items-center gap-3'):
            # Whisper dot status indicators
            header_refs = {}

            with ui.row().classes('items-center gap-1'):
                header_refs['comfyui_dot'] = ui.element('div').classes('neovak-whisper-dot cold')
                ui.label('ComfyUI').classes('text-xs').style('color: var(--text-muted);')

            with ui.row().classes('items-center gap-1'):
                header_refs['acestep_dot'] = ui.element('div').classes('neovak-whisper-dot cold')
                ui.label('ACE-Step').classes('text-xs').style('color: var(--text-muted);')

            available = SYSTEM.get_available_memory_gb()
            mem_label = ui.label(f'{available:.0f}GB free').classes('text-xs').style('color: var(--text-muted);')

            async def update_header_status():
                backend_ok, _ = check_backend()
                if backend_ok:
                    header_refs['comfyui_dot'].classes(remove='cold')
                else:
                    header_refs['comfyui_dot'].classes(add='cold')

                ace_ok, _ = await asyncio.get_event_loop().run_in_executor(None, check_acestep_backend)
                if ace_ok:
                    header_refs['acestep_dot'].classes(remove='cold')
                else:
                    header_refs['acestep_dot'].classes(add='cold')

                avail = SYSTEM.get_available_memory_gb()
                mem_label.set_text(f'{avail:.0f}GB free')

            ui.timer(0.1, update_header_status, once=True)
            ui.timer(15.0, update_header_status)

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

            with ui.element('div').classes('neovak-history-item').on('click', show_image):
                ui.image(item['path']).classes('w-full h-full object-cover')

# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE GENERATION PANEL - Professional Centered Layout
# ═══════════════════════════════════════════════════════════════════════════════

def image_generation_panel():
    """Image generation with centered hero area layout."""
    models = [m for m in ALL_MODELS.get("image", []) if m.available_on_system()]

    if not models:
        with ui.column().classes('items-center justify-center py-12 gap-6 max-w-lg mx-auto neovak-empty-state'):
            ui.icon('image', size='48px').style('color: var(--tube-warm);')
            ui.label('Your image studio is ready').classes('text-lg font-medium').style('color: var(--text-primary);')
            ui.label('Add an image model to begin creating.').style('color: var(--text-secondary);')
            with ui.card().classes('w-full neovak-card p-5 mt-2'):
                ui.label('QUICK START').classes('neovak-section-header mb-4')
                with ui.column().classes('gap-3'):
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('bolt', size='24px').classes('text-amber-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('DreamShaper 8').classes('font-medium text-white')
                            ui.label('2GB - Fast & versatile').classes('text-zinc-400 text-xs')
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
        with ui.row().classes('w-full neovak-command-bar items-center gap-3'):
            # Tube status indicator
            refs['tube'] = ui.element('div').classes('neovak-tube warm')
            
            def on_model_select(m):
                state['model'] = m
                refs['model_btn'].text = m.name

            with ui.dropdown_button(models[0].name, auto_close=True).classes('shrink-0').props('no-caps dropdown-icon=expand_more color=dark dense') as refs['model_btn']:
                for m in models:
                    with ui.item(on_click=lambda m=m: on_model_select(m)).classes('neovak-model-item'):
                        with ui.column().classes('gap-0.5 py-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(m.name).classes('text-white font-medium')
                                ui.badge(m.family).props('color=primary outline dense')
                                ui.label(f'{m.size_gb:.1f}GB').classes('text-zinc-500 text-xs')
                            if m.description:
                                ui.label(m.description).classes('text-zinc-400 text-xs')

            refs['prompt'] = ui.input(placeholder='Describe what you want to create...').classes('flex-1 neovak-command-prompt').props('dense outlined')

            def set_random_prompt():
                refs['prompt'].value = get_random_image_prompt()
                ui.notify('Surprise!', type='positive', position='top', timeout=1500)

            ui.button('Surprise Me', on_click=set_random_prompt).props('flat dense no-caps').classes('neovak-enhance-btn').tooltip('Random creative prompt')

            def do_enhance():
                original = refs['prompt'].value or ''
                if not original.strip():
                    ui.notify('Write something first!', type='warning')
                    return
                enhanced = enhance_prompt(original)
                refs['prompt'].value = enhanced
                ui.notify('✨ Enhanced!', type='positive', position='top', timeout=1500)

            ui.button('✨', on_click=do_enhance).props('flat dense').classes('neovak-enhance-btn').tooltip('Enhance prompt')

            refs['gen_btn'] = ui.button('Create', on_click=lambda: do_generate()).props('no-caps').classes('neovak-btn-primary')
            refs['gen_btn']._props['data-neovak-generate'] = 'true'

        # ─────────────────────────────────────────────────────────────────────
        # STYLE PRESETS - Clickable chips that append to prompt
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('gap-2 flex-wrap px-1'):
            ui.label('STYLE').classes('neovak-section-header mb-0 self-center mr-1')
            for style_name, style_suffix in IMAGE_STYLE_PRESETS.items():
                def apply_style(name=style_name, suffix=style_suffix):
                    current = refs['prompt'].value or ''
                    if suffix not in current:
                        refs['prompt'].value = f'{current}, {suffix}' if current else suffix
                        ui.notify(f'{name} style applied', type='positive', position='top', timeout=1500)
                ui.button(style_name, on_click=apply_style).props('flat dense no-caps size=sm').classes('neovak-style-chip')

        # ─────────────────────────────────────────────────────────────────────
        # HERO AREA (Center) - Image Display + Quick Actions
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('neovak-hero-area w-full'):
            with ui.element('div').classes('neovak-image-container'):
                refs['placeholder_col'] = ui.column().classes('items-center gap-2')
                with refs['placeholder_col']:
                    ui.icon('image', size='48px').classes('text-zinc-600')
                    ui.label('Your creation will appear here').classes('text-zinc-500 text-sm')

                refs['output_img'] = ui.image('').classes('hidden')

            # Quick actions bar
            with ui.row().classes('neovak-quick-actions items-center gap-2'):
                refs['seed_display'] = ui.label('').classes('neovak-seed-display hidden')

                async def copy_seed():
                    if state['last_seed']:
                        await ui.run_javascript(f'navigator.clipboard.writeText("{state["last_seed"]}")')
                        ui.notify(f'Seed {state["last_seed"]} copied!', type='positive', position='top', timeout=1500)

                refs['copy_seed_btn'] = ui.button('📋 Copy Seed', on_click=copy_seed).props('flat dense no-caps').classes('neovak-quick-action-btn hidden').tooltip('Copy seed')

                async def download_image():
                    if state['last_output']:
                        await ui.run_javascript(f'''
                            const a = document.createElement("a");
                            a.href = "{state["last_output"]}";
                            a.download = "neovak_image.png";
                            a.click();
                        ''')

                refs['download_btn'] = ui.button('⬇ Download', on_click=download_image).props('flat dense no-caps').classes('neovak-quick-action-btn hidden').tooltip('Download')

                def do_regenerate():
                    if state['last_seed'] is not None:
                        refs['seed'].value = state['last_seed']
                        do_generate()

                refs['regen_btn'] = ui.button('Re-generate', on_click=lambda: do_regenerate()).props('flat dense no-caps').classes('neovak-quick-action-btn hidden').tooltip('Same seed + prompt')

                def do_vary():
                    refs['seed'].value = -1
                    do_generate()

                refs['vary_btn'] = ui.button('Vary', on_click=lambda: do_vary()).props('flat dense no-caps').classes('neovak-quick-action-btn hidden').tooltip('Same prompt, new seed')

                def do_animate_this():
                    if state['last_output']:
                        app.storage.general['animate_source'] = state['last_output']
                        ui.notify('Image saved for animation. Switch to Video tab and use Image-to-Video mode.', type='positive', timeout=4000)

                refs['animate_btn'] = ui.button('Animate', on_click=do_animate_this).props('flat dense no-caps').classes('neovak-quick-action-btn hidden').tooltip('Send to Video tab for I2V')

            # Progress bar
            with ui.column().classes('w-full max-w-lg gap-1 mt-3'):
                refs['progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full neovak-progress')
                refs['progress'].set_visibility(False)
                refs['progress_text'] = ui.label('').classes('neovak-progress-text text-center w-full')
                refs['progress_text'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # HISTORY STRIP - Horizontal scroll of recent images
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('neovak-history-strip w-full') as history_strip:
            refs['history_container'] = history_strip
            if not generation_history:
                ui.label('Recent creations will appear here').classes('text-zinc-500 text-xs')

        # ─────────────────────────────────────────────────────────────────────
        # MODE TABS - Generate, Variations, Inpaint, Upscale
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('neovak-mode-tabs'):
            refs['mode_tab_buttons'] = {}
            for mode_id, mode_label, mode_tooltip in IMAGE_MODES:
                btn = ui.button(mode_label, on_click=lambda m=mode_id: set_mode(m)).props('flat no-caps')
                btn.classes('neovak-mode-tab' + (' active' if mode_id == 'generate' else ''))
                btn.tooltip(mode_tooltip)
                refs['mode_tab_buttons'][mode_id] = btn

        # ─────────────────────────────────────────────────────────────────────
        # MODE-SPECIFIC INPUT AREAS
        # ─────────────────────────────────────────────────────────────────────

        # Variations mode inputs
        with ui.column().classes('w-full neovak-mode-input-area') as variations_section:
            refs['variations_section'] = variations_section
            ui.label('SOURCE IMAGE').classes('neovak-section-header mb-3')
            with ui.row().classes('items-start gap-6'):
                with ui.column().classes('items-center gap-2'):
                    refs['variation_source'] = ui.element('div').classes('neovak-source-upload')
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

                with ui.column().classes('gap-1 flex-1'):
                    with ui.row().classes('items-center gap-1'):
                        ui.label('Variation Strength').classes('neovak-control-name')
                        ui.icon('help_outline', size='14px').classes('text-zinc-500 cursor-help').tooltip(
                            'Controls how much the new image differs from the original. '
                            'Low (0.3-0.5) = subtle refinements, keeps most details. '
                            'High (0.7-1.0) = dramatic changes, reimagines the image.'
                        )
                    with ui.row().classes('neovak-slider-control'):
                        refs['variation_strength'] = ui.slider(min=0.3, max=1.0, value=0.65, step=0.05).classes('flex-1')
                        refs['variation_strength_input'] = ui.number(value=0.65, min=0.1, max=1.0, step=0.05).classes('neovak-slider-value').props('dense borderless')
                    
                    def sync_var_from_slider(e):
                        refs['variation_strength_input'].value = float(e.args)
                    def sync_var_from_input(e):
                        val = max(0.1, min(1.0, float(e.value or 0.65)))
                        refs['variation_strength'].value = val
                    refs['variation_strength'].on('update:model-value', sync_var_from_slider)
                    refs['variation_strength_input'].on('update:model-value', sync_var_from_input)
                    ui.label('0.5=refine, 0.8=reimagine').classes('neovak-control-hint')
        refs['variations_section'].set_visibility(False)

        # Inpaint mode inputs
        with ui.column().classes('w-full neovak-mode-input-area') as inpaint_section:
            refs['inpaint_section'] = inpaint_section
            ui.label('INPAINT EDITOR').classes('neovak-section-header mb-3')
            ui.label('Upload an image and draw on it to mask areas for regeneration').classes('text-zinc-500 text-sm')
        refs['inpaint_section'].set_visibility(False)

        # Upscale mode inputs
        with ui.column().classes('w-full neovak-mode-input-area') as upscale_section:
            refs['upscale_section'] = upscale_section
            ui.label('UPSCALE').classes('neovak-section-header mb-3')
            with ui.row().classes('items-start gap-6'):
                with ui.column().classes('items-center gap-2'):
                    refs['upscale_source'] = ui.element('div').classes('neovak-source-upload')
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
        with ui.row().classes('w-full neovak-settings-bar gap-8'):
            # SIZE presets - Visual aspect ratio selector
            with ui.column().classes('neovak-preset-group'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label('CANVAS').classes('neovak-preset-label mb-0')
                    ui.icon('help_outline', size='14px').classes('text-zinc-500 cursor-help').tooltip(
                        'Choose the shape and size of your image. '
                        'Square works for most uses. Portrait is better for people. '
                        'Landscape and Wide work well for scenes and wallpapers.'
                    )
                refs['size_options'] = {}
                
                # Shape preview dimensions (normalized to max 32px)
                SHAPE_SIZES = {
                    "1:1": (32, 32),
                    "2:3": (24, 36),
                    "3:2": (36, 24),
                    "16:9": (40, 22),
                    "9:16": (22, 40),
                    "—": (28, 28),  # Custom
                }

                def select_size(idx):
                    state['dim_preset'] = idx
                    name, w, h, _, _ = DIMENSION_PRESETS[idx]
                    state['width'] = w
                    state['height'] = h
                    for i, opt in refs['size_options'].items():
                        if i == idx:
                            opt.classes(add='selected')
                        else:
                            opt.classes(remove='selected')
                    refs['custom_size_row'].set_visibility(name == 'Custom')

                with ui.row().classes('neovak-aspect-selector'):
                    for i, (name, w, h, hint, aspect) in enumerate(DIMENSION_PRESETS):
                        shape_w, shape_h = SHAPE_SIZES.get(aspect, (28, 28))
                        with ui.element('div').classes('neovak-aspect-option' + (' selected' if i == 0 else '')) as opt:
                            opt.on('click', lambda i=i: select_size(i))
                            # Visual shape preview
                            with ui.element('div').classes('neovak-aspect-shape').style(f'width: 44px; height: 44px;'):
                                ui.element('div').classes('neovak-aspect-shape-inner').style(f'width: {shape_w}px; height: {shape_h}px;')
                            ui.label(name).classes('neovak-aspect-name')
                            if name != 'Custom':
                                ui.label(f'{w}×{h}').classes('neovak-aspect-dims')
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
            with ui.column().classes('neovak-preset-group'):
                ui.label('QUALITY').classes('neovak-preset-label')
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

                with ui.column().classes('neovak-preset-options'):
                    for i, (name, steps, cfg, hint) in enumerate(QUALITY_PRESETS):
                        with ui.element('div').classes('neovak-radio-option' + (' selected' if i == 1 else '')) as opt:
                            opt.on('click', lambda i=i: select_quality(i))
                            ui.element('div').classes('radio-dot')
                            ui.label(name).tooltip(f'{steps} steps, CFG {cfg} - {hint}')
                        refs['quality_options'][i] = opt

            ui.element('div').classes('flex-1')  # Spacer

            # Advanced settings - Power controls with human-readable names
            with ui.expansion('▾ Fine-Tune', value=False).classes('neovak-advanced-toggle').props('dense'):
                with ui.row().classes('gap-6 p-4 flex-wrap'):
                    # SEED - Reproducibility control
                    with ui.column().classes('gap-1'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label('Seed').classes('neovak-control-name')
                            ui.icon('help_outline', size='14px').classes('text-zinc-500 cursor-help').tooltip(
                                'The random seed determines the starting point for generation. '
                                'Use the same seed + prompt to recreate an exact image. '
                                '-1 means random (different each time).'
                            )
                        refs['seed'] = ui.number(value=-1).classes('w-28').props('dense outlined')
                        ui.label('−1 = surprise me').classes('neovak-control-hint')
                    
                    # STEPS - Quality/detail control
                    with ui.column().classes('gap-1 min-w-48'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label('Refinement').classes('neovak-control-name')
                            ui.icon('help_outline', size='14px').classes('text-zinc-500 cursor-help').tooltip(
                                'How many passes the AI makes to refine your image. '
                                'More steps = finer details but slower. '
                                '15-20 for drafts, 30-40 for quality, 50+ for maximum detail.'
                            )
                        with ui.row().classes('neovak-slider-control'):
                            refs['steps_slider'] = ui.slider(min=10, max=60, value=30).classes('flex-1')
                            refs['steps_input'] = ui.number(value=30, min=10, max=100).classes('neovak-slider-value').props('dense borderless')
                        
                        def sync_steps_from_slider(e):
                            refs['steps_input'].value = int(e.args)
                            state['steps'] = int(e.args)
                        def sync_steps_from_input(e):
                            val = max(10, min(100, int(e.value or 30)))
                            refs['steps_slider'].value = min(60, val)
                            state['steps'] = val
                        refs['steps_slider'].on('update:model-value', sync_steps_from_slider)
                        refs['steps_input'].on('update:model-value', sync_steps_from_input)
                        ui.label('10=fast draft, 50+=fine art').classes('neovak-control-hint')
                    
                    # CFG - Prompt adherence control  
                    with ui.column().classes('gap-1 min-w-48'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label('Prompt Strength').classes('neovak-control-name')
                            ui.icon('help_outline', size='14px').classes('text-zinc-500 cursor-help').tooltip(
                                'How strictly the AI follows your prompt vs being creative. '
                                'Low (1-5) = artistic freedom, may surprise you. '
                                'Medium (6-8) = balanced, recommended. '
                                'High (9-15) = literal interpretation, can look artificial.'
                            )
                        with ui.row().classes('neovak-slider-control'):
                            refs['cfg_slider'] = ui.slider(min=1, max=15, value=7, step=0.5).classes('flex-1')
                            refs['cfg_input'] = ui.number(value=7, min=1, max=20, step=0.5).classes('neovak-slider-value').props('dense borderless')
                        
                        def sync_cfg_from_slider(e):
                            refs['cfg_input'].value = float(e.args)
                            state['cfg'] = float(e.args)
                        def sync_cfg_from_input(e):
                            val = max(1, min(20, float(e.value or 7)))
                            refs['cfg_slider'].value = min(15, val)
                            state['cfg'] = val
                        refs['cfg_slider'].on('update:model-value', sync_cfg_from_slider)
                        refs['cfg_input'].on('update:model-value', sync_cfg_from_input)
                        ui.label('7=balanced, lower=creative').classes('neovak-control-hint')

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
        refs['gen_btn'].text = 'Warming tubes...'
        refs['gen_btn'].classes(add='neovak-warming')
        refs['progress'].set_visibility(True)
        refs['progress_text'].set_visibility(True)

        # Tube goes hot during generation
        refs['tube'].classes(remove='cold warm error', add='hot')
        await asyncio.sleep(0.8)
        refs['gen_btn'].text = 'Creating...'
        refs['gen_btn'].classes(remove='neovak-warming')

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
                refs['regen_btn'].classes(remove='hidden')
                refs['vary_btn'].classes(remove='hidden')
                refs['animate_btn'].classes(remove='hidden')

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
            # Tube flickers on error
            refs['tube'].classes(remove='hot warm', add='error')
        finally:
            is_generating = False
            progress_task.cancel()
            refs['gen_btn'].enable()
            refs['gen_btn'].text = 'Create'
            # Tube returns to warm (ready) state
            refs['tube'].classes(remove='hot error', add='warm')
            await asyncio.sleep(2)
            refs['progress'].set_visibility(False)
            refs['progress_text'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO GENERATION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def video_generation_panel():
    """Video generation panel with centered layout, I2V mode, history, surprise me."""
    video_models = [m for m in ALL_MODELS.get('video', []) if m.available_on_system()]

    if not video_models:
        with ui.column().classes('items-center justify-center py-12 gap-6 max-w-lg mx-auto neovak-empty-state'):
            ui.icon('movie', size='48px').style('color: var(--tube-warm);')
            ui.label('Your video studio is ready').classes('text-lg font-medium').style('color: var(--text-primary);')
            ui.label('Add a video model to begin creating.').style('color: var(--text-secondary);')
            with ui.card().classes('w-full neovak-card p-5 mt-2'):
                ui.label('QUICK START').classes('neovak-section-header mb-4')
                with ui.column().classes('gap-3'):
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('star', size='24px').classes('text-amber-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('LTX-Video 0.9.1').classes('font-medium text-white')
                            ui.label('5GB - Works great on Mac').classes('text-zinc-400 text-xs')
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
        'mode': 'text2video',
        'i2v_source': None,
        'i2v_strength': 0.75,
        'history': [],
    }
    refs = {}

    with ui.column().classes('w-full gap-4'):
        # Command bar
        with ui.row().classes('w-full neovak-command-bar items-center gap-3'):
            refs['tube'] = ui.element('div').classes('neovak-tube warm')

            def on_video_model_select(m):
                state['model'] = m
                refs['video_model_btn'].text = m.name

            with ui.dropdown_button(video_models[0].name, auto_close=True).classes('shrink-0').props('no-caps dropdown-icon=expand_more color=dark dense') as refs['video_model_btn']:
                for m in video_models:
                    with ui.item(on_click=lambda m=m: on_video_model_select(m)).classes('neovak-model-item'):
                        ui.label(m.name).classes('text-white font-medium')

            refs['video_prompt'] = ui.input(placeholder='Describe the video you want to create...').classes('flex-1 neovak-command-prompt').props('dense outlined')

            def set_random_video_prompt():
                refs['video_prompt'].value = get_random_video_prompt()
                ui.notify('Surprise!', type='positive', position='top', timeout=1500)

            ui.button('Surprise Me', on_click=set_random_video_prompt).props('flat dense no-caps').classes('neovak-enhance-btn').tooltip('Random motion prompt')

            def do_enhance_video():
                original = refs['video_prompt'].value or ''
                if not original.strip():
                    ui.notify('Write something first!', type='warning')
                    return
                enhanced = enhance_prompt(original, style="cinematic")
                refs['video_prompt'].value = enhanced
                ui.notify('Enhanced!', type='positive', position='top', timeout=1500)

            ui.button('Enhance', on_click=do_enhance_video).props('flat dense no-caps').classes('neovak-enhance-btn').tooltip('Enhance prompt')

            refs['video_gen_btn'] = ui.button('Create', on_click=lambda: do_generate_video()).props('no-caps').classes('neovak-btn-primary')

        # ── Mode toggle: Text→Video / Image→Video / Chain ──
        with ui.row().classes('neovak-mode-tabs'):
            refs['video_mode_btns'] = {}
            for mode_id, mode_label in [('text2video', 'Text \u2192 Video'), ('img2video', 'Image \u2192 Video'), ('chain', 'Chain')]:
                def set_video_mode(m=mode_id):
                    state['mode'] = m
                    for mid, btn in refs['video_mode_btns'].items():
                        if mid == m:
                            btn.classes(add='active')
                        else:
                            btn.classes(remove='active')
                    refs['i2v_section'].set_visibility(m == 'img2video')
                    refs['chain_section'].set_visibility(m == 'chain')
                btn = ui.button(mode_label, on_click=set_video_mode).props('flat no-caps')
                btn.classes('neovak-mode-tab' + (' active' if mode_id == 'text2video' else ''))
                refs['video_mode_btns'][mode_id] = btn

        # I2V mode inputs
        with ui.column().classes('w-full neovak-mode-input-area') as i2v_section:
            refs['i2v_section'] = i2v_section
            ui.label('SOURCE IMAGE').classes('neovak-section-header mb-3')
            with ui.row().classes('items-start gap-6'):
                with ui.column().classes('items-center gap-2'):
                    refs['i2v_source_el'] = ui.element('div').classes('neovak-source-upload')
                    with refs['i2v_source_el']:
                        refs['i2v_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['i2v_placeholder'] = ui.column().classes('items-center')
                        with refs['i2v_placeholder']:
                            ui.icon('add_photo_alternate', size='32px').classes('text-zinc-500')
                            ui.label('Upload').classes('text-zinc-500 text-xs')

                    async def handle_i2v_upload(e):
                        if e.content:
                            import tempfile, base64
                            content = e.content.read()
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                                f.write(content)
                                state['i2v_source'] = f.name
                            refs['i2v_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
                            refs['i2v_preview'].classes(remove='hidden')
                            refs['i2v_placeholder'].set_visibility(False)
                            ui.notify('Source image loaded', type='positive')

                    refs['i2v_upload'] = ui.upload(on_upload=handle_i2v_upload, auto_upload=True).props('accept=image/* flat dense').classes('hidden')
                    refs['i2v_source_el'].on('click', lambda: refs['i2v_upload'].run_method('pickFiles'))

                with ui.column().classes('gap-1 flex-1'):
                    ui.label('Image Influence').classes('neovak-control-name')
                    with ui.row().classes('neovak-slider-control'):
                        refs['i2v_strength'] = ui.slider(min=0.3, max=1.0, value=0.75, step=0.05).classes('flex-1')
                        refs['i2v_strength_input'] = ui.number(value=0.75, min=0.1, max=1.0, step=0.05).classes('neovak-slider-value').props('dense borderless')
                    def sync_i2v_s(e): refs['i2v_strength_input'].value = float(e.args)
                    def sync_i2v_i(e):
                        val = max(0.1, min(1.0, float(e.value or 0.75)))
                        refs['i2v_strength'].value = val
                    refs['i2v_strength'].on('update:model-value', sync_i2v_s)
                    refs['i2v_strength_input'].on('update:model-value', sync_i2v_i)
                    ui.label('How much the image influences the video').classes('neovak-control-hint')

            # Auto-load from "Animate This" in image tab
            animate_src = app.storage.general.get('animate_source')
            if animate_src:
                import base64
                try:
                    with open(animate_src, 'rb') as f:
                        content = f.read()
                    state['i2v_source'] = animate_src
                    refs['i2v_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
                    refs['i2v_preview'].classes(remove='hidden')
                    refs['i2v_placeholder'].set_visibility(False)
                    state['mode'] = 'img2video'
                    refs['video_mode_btns']['img2video'].classes(add='active')
                    refs['video_mode_btns']['text2video'].classes(remove='active')
                    i2v_section.set_visibility(True)
                    app.storage.general.pop('animate_source', None)
                except Exception:
                    pass

        refs['i2v_section'].set_visibility(state['mode'] == 'img2video')

        # ── Chain mode: Storyboard interface ──
        with ui.column().classes('w-full neovak-mode-input-area') as chain_section:
            refs['chain_section'] = chain_section
            ui.label('STORYBOARD').classes('neovak-section-header mb-3')

            state['chain_segments'] = [
                {'prompt': '', 'seed': -1},
                {'prompt': '', 'seed': -1},
            ]
            state['chain_clips'] = []
            state['chain_continue_from'] = None
            refs['chain_segment_container'] = None

            def _rebuild_chain_segments():
                if refs['chain_segment_container'] is None:
                    return
                refs['chain_segment_container'].clear()
                with refs['chain_segment_container']:
                    for idx, seg in enumerate(state['chain_segments']):
                        is_first = (idx == 0 and state['chain_continue_from'] is None)
                        mode_label = 'text-to-video' if is_first else 'last frame \u2192 first frame'
                        with ui.card().classes('w-full neovak-card p-4'):
                            with ui.row().classes('items-center gap-2 mb-2'):
                                ui.label(f'Segment {idx + 1}').classes('font-medium').style('color: var(--text-primary); font-size: 0.875rem;')
                                ui.label(f'({mode_label})').classes('text-xs').style('color: var(--text-muted); font-style: italic;')
                                if len(state['chain_clips']) > idx:
                                    ui.icon('check_circle', size='16px').style('color: var(--accent);')
                            prompt_input = ui.textarea(
                                placeholder=f'Describe segment {idx + 1}...',
                                value=seg.get('prompt', '')
                            ).classes('w-full').props('dense outlined rows=2').style('color: var(--text-primary); background: var(--surface-0);')
                            def on_prompt_change(e, i=idx):
                                state['chain_segments'][i]['prompt'] = e.value
                            prompt_input.on('update:model-value', on_prompt_change)
                            with ui.row().classes('items-center gap-3 mt-1'):
                                ui.label('Seed').classes('text-xs').style('color: var(--text-muted);')
                                seed_input = ui.number(value=seg.get('seed', -1), min=-1, step=1).classes('neovak-slider-value').props('dense borderless').style('width: 100px;')
                                def on_seed_change(e, i=idx):
                                    state['chain_segments'][i]['seed'] = int(e.value or -1)
                                seed_input.on('update:model-value', on_seed_change)

            with ui.column().classes('w-full gap-3') as seg_container:
                refs['chain_segment_container'] = seg_container

            _rebuild_chain_segments()

            # Continue-from indicator
            refs['chain_continue_label'] = ui.label('').classes('text-xs hidden').style('color: var(--accent);')

            with ui.row().classes('items-center gap-3 mt-2'):
                def add_chain_segment():
                    state['chain_segments'].append({'prompt': '', 'seed': -1})
                    _rebuild_chain_segments()
                    _update_chain_info()

                def remove_chain_segment():
                    if len(state['chain_segments']) > 1:
                        state['chain_segments'].pop()
                        _rebuild_chain_segments()
                        _update_chain_info()

                ui.button('+ Add Segment', on_click=add_chain_segment).props('flat dense no-caps').classes('neovak-enhance-btn')
                ui.button('- Remove Last', on_click=remove_chain_segment).props('flat dense no-caps').classes('neovak-enhance-btn')

            with ui.row().classes('items-center gap-4 mt-2'):
                refs['chain_info'] = ui.label('').classes('text-xs').style('color: var(--text-secondary);')

            def _update_chain_info():
                n = len(state['chain_segments'])
                fps = 24.0
                est_dur = n * (state['num_frames'] / fps)
                refs['chain_info'].set_text(f'Segments: {n} | Est. duration: ~{est_dur:.1f}s | Frames/segment: {state["num_frames"]}')

            _update_chain_info()

            refs['chain_gen_btn'] = ui.button('Generate Chain', on_click=lambda: do_generate_chain()).props('no-caps').classes('neovak-btn-primary mt-3')

            with ui.column().classes('w-full gap-1 mt-2'):
                refs['chain_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full neovak-progress')
                refs['chain_progress'].set_visibility(False)
                refs['chain_progress_text'] = ui.label('').classes('neovak-progress-text text-center w-full')
                refs['chain_progress_text'].set_visibility(False)

            refs['chain_output_area'] = ui.column().classes('w-full gap-3 mt-3')
            refs['chain_output_area'].set_visibility(False)

        refs['chain_section'].set_visibility(state['mode'] == 'chain')

        # Hero area for video
        with ui.element('div').classes('neovak-hero-area w-full'):
            with ui.element('div').classes('neovak-video-container'):
                refs['video_placeholder'] = ui.column().classes('items-center gap-2')
                with refs['video_placeholder']:
                    ui.icon('movie', size='48px').classes('text-zinc-600')
                    ui.label('Your video will appear here').classes('text-zinc-500 text-sm')

                refs['output_video'] = ui.video('').classes('w-full h-full object-contain hidden')

            # Transport controls
            with ui.row().classes('neovak-transport items-center'):
                async def video_play_pause():
                    await ui.run_javascript('''
                        const video = document.querySelector('.neovak-video-container video');
                        if (video) { video.paused ? video.play() : video.pause(); }
                    ''')

                ui.button(icon='play_arrow', on_click=video_play_pause).props('flat dense').classes('neovak-transport-btn').tooltip('Play/Pause')

                def toggle_loop():
                    state['loop_enabled'] = not state['loop_enabled']
                    loop_prop = 'loop' if state['loop_enabled'] else ''
                    refs['output_video'].props(loop_prop)
                    refs['loop_btn'].classes(add='active' if state['loop_enabled'] else '', remove='' if state['loop_enabled'] else 'active')
                    ui.notify(f'Loop {"on" if state["loop_enabled"] else "off"}', position='top', timeout=1000)

                refs['loop_btn'] = ui.button(icon='loop', on_click=toggle_loop).props('flat dense').classes('neovak-transport-btn active').tooltip('Toggle loop')
                refs['output_video'].props('loop')

                refs['video_seed_display'] = ui.label('').classes('neovak-seed-display hidden ml-auto')

            # Progress
            with ui.column().classes('w-full max-w-lg gap-1 mt-3'):
                refs['video_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full neovak-progress')
                refs['video_progress'].set_visibility(False)
                refs['video_progress_text'] = ui.label('').classes('neovak-progress-text text-center w-full')
                refs['video_progress_text'].set_visibility(False)

        # ── Video history strip ──
        with ui.element('div').classes('neovak-history-strip w-full') as video_history:
            refs['video_history_container'] = video_history
            ui.label('Recent videos will appear here').classes('text-zinc-500 text-xs')

        # Settings bar
        with ui.row().classes('w-full neovak-settings-bar gap-8'):
            with ui.column().classes('neovak-preset-group'):
                ui.label('SIZE').classes('neovak-preset-label')
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

            with ui.column().classes('neovak-preset-group'):
                ui.label('DURATION').classes('neovak-preset-label')
                refs['video_dur_btns'] = []
                with ui.row().classes('gap-2'):
                    for i, (name, frames, _) in enumerate(VIDEO_DURATION_PRESETS):
                        def select_dur(idx=i, f=frames):
                            state['num_frames'] = f
                            for j, btn in enumerate(refs['video_dur_btns']):
                                btn.props('color=primary' if j == idx else 'color=dark')
                        btn = ui.button(name, on_click=select_dur).props(f'dense no-caps {"color=primary" if i == 0 else "color=dark"}')
                        refs['video_dur_btns'].append(btn)

            with ui.column().classes('neovak-preset-group'):
                ui.label('QUALITY').classes('neovak-preset-label')
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

    def _add_video_to_history(path, prompt):
        entry = {'path': path, 'prompt': prompt}
        state['history'].insert(0, entry)
        if len(state['history']) > 10:
            state['history'].pop()
        refs['video_history_container'].clear()
        with refs['video_history_container']:
            for item in state['history']:
                def load_video(p=item['path'], pr=item['prompt']):
                    refs['video_placeholder'].set_visibility(False)
                    refs['output_video'].classes(remove='hidden')
                    refs['output_video'].set_source(p)
                    state['last_output'] = p
                    ui.notify(f'"{pr[:40]}..."' if len(pr) > 40 else f'"{pr}"', position='top', timeout=2000)

                def continue_from_video(p=item['path'], pr=item['prompt']):
                    state['mode'] = 'chain'
                    for mid, btn in refs['video_mode_btns'].items():
                        btn.classes(add='active' if mid == 'chain' else '', remove='' if mid == 'chain' else 'active')
                    refs['i2v_section'].set_visibility(False)
                    refs['chain_section'].set_visibility(True)
                    state['chain_continue_from'] = p
                    state['chain_segments'] = [{'prompt': '', 'seed': -1}]
                    refs['chain_continue_label'].set_text(f'Continuing from: {pr[:50]}')
                    refs['chain_continue_label'].classes(remove='hidden')
                    _rebuild_chain_segments()
                    _update_chain_info()
                    ui.notify('Chain mode: add prompts to extend this video', type='info')

                with ui.column().classes('neovak-history-item items-center gap-1').style('width: 80px; min-height: 50px; cursor: pointer;'):
                    with ui.element('div').on('click', load_video).style('display: flex; align-items: center; justify-content: center; width: 100%; height: 40px;'):
                        ui.icon('play_circle', size='24px').style('color: var(--tube-warm);')
                    ui.button(icon='add_link', on_click=continue_from_video).props('flat dense round size=xs').classes('neovak-transport-btn').tooltip('Continue from this').style('font-size: 0.6rem;')

    async def do_generate_video():
        prompt = refs['video_prompt'].value
        if not prompt:
            ui.notify('Please describe the video', type='warning')
            return
        if state['mode'] == 'img2video' and not state['i2v_source']:
            ui.notify('Please upload a source image', type='warning')
            return

        refs['video_gen_btn'].disable()
        refs['video_gen_btn'].text = 'Warming tubes...'
        refs['video_gen_btn'].classes(add='neovak-warming')
        refs['video_progress'].set_visibility(True)
        refs['video_progress_text'].set_visibility(True)

        refs['tube'].classes(remove='cold warm error', add='hot')
        await asyncio.sleep(0.8)
        refs['video_gen_btn'].text = 'Creating...'
        refs['video_gen_btn'].classes(remove='neovak-warming')

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
                refs['video_progress_text'].set_text(f'{int(elapsed)}s elapsed - ~{int(remaining)}s remaining')
                await asyncio.sleep(0.5)

        progress_task = asyncio.create_task(update_progress())

        import random
        seed = random.randint(0, 2**32 - 1)
        state['last_seed'] = seed

        try:
            if state['mode'] == 'img2video' and state['i2v_source']:
                i2v_strength = refs['i2v_strength'].value
                output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: generate_video_from_image(
                        prompt_text=prompt,
                        model_name=state['model'].name,
                        image_path=state['i2v_source'],
                        width=state['width'],
                        height=state['height'],
                        num_frames=state['num_frames'],
                        steps=state['steps'],
                        cfg=state['cfg'],
                        seed=seed,
                        strength=i2v_strength,
                    )
                )
            else:
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
                refs['video_progress_text'].set_text(f'Complete in {int(elapsed)}s')
                refs['video_seed_display'].set_text(f'Seed: {seed}')
                refs['video_seed_display'].classes(remove='hidden')
                ui.notify('Video created!', type='positive')
                _add_video_to_history(output_path, prompt)
            else:
                refs['video_progress_text'].set_text(f'{status_msg}')
                ui.notify(status_msg, type='negative')
        except Exception as e:
            is_generating = False
            refs['video_progress_text'].set_text('Error')
            ui.notify(str(e), type='negative')
            refs['tube'].classes(remove='hot warm', add='error')
        finally:
            is_generating = False
            progress_task.cancel()
            refs['video_gen_btn'].enable()
            refs['video_gen_btn'].text = 'Create'
            refs['tube'].classes(remove='hot error', add='warm')
            await asyncio.sleep(2)
            refs['video_progress'].set_visibility(False)
            refs['video_progress_text'].set_visibility(False)

    async def do_generate_chain():
        valid_segments = [s for s in state['chain_segments'] if s.get('prompt', '').strip()]
        if not valid_segments:
            ui.notify('Add prompts to at least one segment', type='warning')
            return

        refs['chain_gen_btn'].disable()
        refs['chain_gen_btn'].text = 'Warming tubes...'
        refs['chain_gen_btn'].classes(add='neovak-warming')
        refs['chain_progress'].set_visibility(True)
        refs['chain_progress_text'].set_visibility(True)
        refs['chain_progress'].set_value(0)

        refs['tube'].classes(remove='cold warm error', add='hot')
        await asyncio.sleep(0.8)
        refs['chain_gen_btn'].text = 'Generating chain...'
        refs['chain_gen_btn'].classes(remove='neovak-warming')

        import time as time_module
        start_time = time_module.time()

        def chain_progress_cb(pct, msg):
            try:
                refs['chain_progress'].set_value(pct / 100.0)
                refs['chain_progress_text'].set_text(msg)
            except Exception:
                pass

        try:
            continue_from = state.get('chain_continue_from')

            if continue_from:
                final_path, status_msg, new_clips = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: continue_video_chain(
                        existing_video_path=continue_from,
                        segments=valid_segments,
                        model_name=state['model'].name,
                        width=state['width'], height=state['height'],
                        num_frames=state['num_frames'],
                        steps=state['steps'], cfg=state['cfg'],
                        progress_callback=chain_progress_cb,
                    )
                )
                all_clips = [continue_from] + new_clips
            else:
                final_path, status_msg, clips = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: generate_video_chain(
                        segments=valid_segments,
                        model_name=state['model'].name,
                        width=state['width'], height=state['height'],
                        num_frames=state['num_frames'],
                        steps=state['steps'], cfg=state['cfg'],
                        progress_callback=chain_progress_cb,
                    )
                )
                all_clips = clips

            elapsed = time_module.time() - start_time
            state['chain_clips'] = all_clips

            if final_path:
                state['last_output'] = final_path
                refs['video_placeholder'].set_visibility(False)
                refs['output_video'].classes(remove='hidden')
                refs['output_video'].set_source(final_path)
                refs['chain_progress'].set_value(1.0)
                refs['chain_progress_text'].set_text(f'Chain complete in {int(elapsed)}s — {status_msg}')
                ui.notify('Video chain created!', type='positive')
                _add_video_to_history(final_path, f'[Chain {len(all_clips)}seg] {valid_segments[0]["prompt"][:30]}')

                refs['chain_output_area'].set_visibility(True)
                refs['chain_output_area'].clear()
                with refs['chain_output_area']:
                    ui.label('INDIVIDUAL CLIPS').classes('neovak-section-header')
                    with ui.row().classes('gap-3 flex-wrap'):
                        for ci, clip_path in enumerate(all_clips):
                            with ui.card().classes('neovak-card p-2').style('width: 200px;'):
                                ui.label(f'Clip {ci + 1}').classes('text-xs font-medium').style('color: var(--text-secondary);')
                                clip_video = ui.video(clip_path).classes('w-full').props('controls loop').style('max-height: 120px;')
                _rebuild_chain_segments()
            else:
                refs['chain_progress_text'].set_text(status_msg)
                ui.notify(status_msg, type='negative')

        except Exception as e:
            refs['chain_progress_text'].set_text('Error')
            ui.notify(str(e), type='negative')
            refs['tube'].classes(remove='hot warm', add='error')
        finally:
            refs['chain_gen_btn'].enable()
            refs['chain_gen_btn'].text = 'Generate Chain'
            refs['tube'].classes(remove='hot error', add='warm')
            await asyncio.sleep(2)
            refs['chain_progress'].set_visibility(False)
            refs['chain_progress_text'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE GENERATION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def voice_generation_panel():
    """Voice generation with Chatterbox TTS — presets, emotion slider, quick texts, history."""
    all_models = discover_all_models()
    speech_models = all_models.get('speech', [])

    if not speech_models:
        speech_models = [Model(name="Chatterbox TTS", path=Path("."), family="chatterbox", size_gb=2.0,
                              tier_required="lite", media_type="speech",
                              description="Expressive text-to-speech with emotion tags. Downloads automatically on first use (~2GB).")]

    state = {'speed': 1.0, 'voice_sample': None, 'model': speech_models[0], 'emotion': 0.5, 'history': []}
    refs = {}

    with ui.column().classes('w-full max-w-2xl mx-auto gap-6 py-6'):
        ui.label('Voice Generation').classes('neovak-title')
        ui.label(TAB_SUBTITLES['voice']).classes('neovak-tab-subtitle')
        ui.label('Text-to-speech with expression tags').classes('neovak-subtitle mb-4')

        with ui.card().classes('w-full neovak-card p-6'):
            # Model info
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.label('MODEL').classes('neovak-section-header mb-0')
            with ui.row().classes('items-center gap-3 p-3 rounded-lg').style('background: var(--surface-2);'):
                ui.icon('record_voice_over', size='24px').classes('text-amber-500')
                with ui.column().classes('gap-0.5 flex-1'):
                    if len(speech_models) > 1:
                        def on_speech_model_select(m):
                            state['model'] = m
                            refs['speech_model_btn'].text = m.name
                        with ui.dropdown_button(speech_models[0].name, auto_close=True).props('no-caps dropdown-icon=expand_more color=dark dense') as refs['speech_model_btn']:
                            for m in speech_models:
                                with ui.item(on_click=lambda m=m: on_speech_model_select(m)).classes('neovak-model-item'):
                                    with ui.column().classes('gap-0.5 py-1'):
                                        with ui.row().classes('items-center gap-2'):
                                            ui.label(m.name).classes('text-white font-medium')
                                            ui.badge(m.family).props('color=primary outline dense')
                                        if m.description:
                                            ui.label(m.description).classes('text-zinc-400 text-xs')
                    else:
                        m = speech_models[0]
                        with ui.row().classes('items-center gap-2'):
                            ui.label(m.name).classes('text-white font-medium')
                            ui.badge(m.family).props('color=primary outline dense')
                            if m.size_gb > 0:
                                ui.label(f'~{m.size_gb:.1f}GB').classes('text-zinc-500 text-xs')
                        if m.description:
                            ui.label(m.description).classes('text-zinc-400 text-xs')

            # Voice presets gallery
            voice_presets = get_voice_presets()
            if voice_presets:
                ui.label('VOICE PRESETS').classes('neovak-section-header mt-4')
                with ui.row().classes('gap-2 flex-wrap'):
                    for preset_name in voice_presets:
                        def select_preset(name=preset_name):
                            path = resolve_voice_preset(name)
                            if path:
                                state['voice_sample'] = path
                                ui.notify(f'Voice: {name}', type='positive', position='top', timeout=1500)
                        ui.button(preset_name, on_click=select_preset).props('flat dense no-caps size=sm').classes('neovak-style-chip')

            # Quick text templates
            ui.label('QUICK TEXTS').classes('neovak-section-header mt-4')
            with ui.row().classes('gap-2 flex-wrap'):
                for tpl_name, tpl_text in VOICE_QUICK_TEXTS.items():
                    def fill_text(t=tpl_text, n=tpl_name):
                        refs['text'].value = t
                        ui.notify(f'Loaded: {n}', type='info', position='top', timeout=1500)
                    ui.button(tpl_name, on_click=fill_text).props('flat dense no-caps size=sm').classes('neovak-style-chip')

            ui.label('TEXT').classes('neovak-section-header mt-4')
            refs['text'] = ui.textarea(placeholder='Enter text to speak... Use tags like [laugh], [sigh], [gasp] for expressions').classes('w-full neovak-prompt').props('outlined autogrow rows=4')

            ui.label('EXPRESSION TAGS').classes('neovak-section-header mt-4')
            with ui.row().classes('gap-2 flex-wrap'):
                for tag_text, tag_desc in VOICE_EXPRESSION_TAGS:
                    def add_tag(t=tag_text):
                        refs['text'].value = (refs['text'].value or '') + f' {t}'
                    ui.button(tag_text, on_click=add_tag).props('flat dense size=sm').classes('text-zinc-400').tooltip(tag_desc)

            # Expression level (emotion slider)
            with ui.column().classes('gap-1 mt-4'):
                ui.label('EXPRESSION LEVEL').classes('neovak-section-header')
                with ui.row().classes('neovak-slider-control items-center'):
                    ui.label('Neutral').classes('neovak-control-hint')
                    refs['emotion'] = ui.slider(min=0.0, max=1.0, value=0.5, step=0.05).classes('flex-1')
                    ui.label('Expressive').classes('neovak-control-hint')
                    refs['emotion_input'] = ui.number(value=0.5, min=0.0, max=1.0, step=0.05).classes('neovak-slider-value').props('dense borderless')
                def sync_emo_s(e):
                    refs['emotion_input'].value = float(e.args)
                    state['emotion'] = float(e.args)
                def sync_emo_i(e):
                    val = max(0.0, min(1.0, float(e.value or 0.5)))
                    refs['emotion'].value = val
                    state['emotion'] = val
                refs['emotion'].on('update:model-value', sync_emo_s)
                refs['emotion_input'].on('update:model-value', sync_emo_i)

            # Speed control
            with ui.column().classes('gap-1 mt-4'):
                with ui.row().classes('items-center gap-1'):
                    ui.label('Speed').classes('neovak-control-name')
                with ui.row().classes('neovak-slider-control'):
                    refs['speed'] = ui.slider(min=0.5, max=2.0, value=1.0, step=0.1).classes('flex-1')
                    refs['speed_input'] = ui.number(value=1.0, min=0.25, max=3.0, step=0.1).classes('neovak-slider-value').props('dense borderless')
                def sync_speed_from_slider(e):
                    refs['speed_input'].value = float(e.args)
                def sync_speed_from_input(e):
                    val = max(0.25, min(3.0, float(e.value or 1.0)))
                    refs['speed'].value = min(2.0, max(0.5, val))
                refs['speed'].on('update:model-value', sync_speed_from_slider)
                refs['speed_input'].on('update:model-value', sync_speed_from_input)
                ui.label('1.0x=natural, type up to 3x').classes('neovak-control-hint')

        refs['voice_gen_btn'] = ui.button('Generate Voice', on_click=lambda: do_generate_voice()).classes('w-full neovak-btn-primary')

        with ui.column().classes('w-full gap-2'):
            refs['voice_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full neovak-progress')
            refs['voice_progress'].set_visibility(False)
            refs['voice_status'] = ui.label('').classes('text-zinc-400 text-sm')

        refs['audio_output'] = ui.audio('').classes('w-full hidden')

        # Voice history
        with ui.column().classes('w-full'):
            ui.label('HISTORY').classes('neovak-section-header')
            refs['voice_history_row'] = ui.column().classes('gap-2 w-full')

    async def do_generate_voice():
        text = refs['text'].value
        if not text:
            ui.notify('Enter some text first', type='warning')
            return

        refs['voice_gen_btn'].disable()
        refs['voice_gen_btn'].text = 'Warming tubes...'
        refs['voice_gen_btn'].classes(add='neovak-warming')
        refs['voice_progress'].set_visibility(True)
        refs['voice_status'].set_text('Generating speech...')

        await asyncio.sleep(0.8)
        refs['voice_gen_btn'].text = 'Creating...'
        refs['voice_gen_btn'].classes(remove='neovak-warming')

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
                refs['voice_status'].set_text('Voice generated!')
                ui.notify('Voice generated!', type='positive')

                preview = text[:40] + '...' if len(text) > 40 else text
                state['history'].insert(0, {'path': output_path, 'text': preview})
                if len(state['history']) > 10:
                    state['history'].pop()
                with refs['voice_history_row']:
                    def play_clip(p=output_path):
                        refs['audio_output'].set_source(p)
                        refs['audio_output'].classes(remove='hidden')
                    with ui.row().classes('items-center gap-2 p-2 rounded').style('background: var(--surface-2);'):
                        ui.button(icon='play_arrow', on_click=play_clip).props('flat dense').style('color: var(--tube-warm);')
                        ui.label(preview).classes('text-zinc-400 text-sm flex-1')
            else:
                refs['voice_status'].set_text(f'{status}')
                ui.notify(status, type='negative')
        except Exception as e:
            refs['voice_status'].set_text('Error')
            ui.notify(str(e), type='negative')
        finally:
            refs['voice_gen_btn'].enable()
            refs['voice_gen_btn'].text = 'Generate Voice'
            refs['voice_progress'].set_visibility(False)

# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC GENERATION PANEL (ACE-Step 1.5)
# ═══════════════════════════════════════════════════════════════════════════════

def music_generation_panel():
    """Music generation panel powered by ACE-Step 1.5."""

    state = {
        'duration': 120,
        'seed': -1,
        'thinking': True,
        'infer_step': 30,
        'guidance_scale': 15.0,
        'guidance_scale_text': 0.0,
        'guidance_scale_lyric': 0.0,
        'lm_model': '',
        'mode': 'create',
        'history': [],
        'last_output_path': None,
        'audio_upload_path': None,
        'repaint_start': 0.0,
        'repaint_end': 0.0,
    }
    refs = {}

    with ui.column().classes('w-full max-w-2xl mx-auto gap-6 py-6'):
        ui.label('Music Generation').classes('neovak-title')
        ui.label(TAB_SUBTITLES['music']).classes('neovak-tab-subtitle')
        ui.label('Create full songs from style tags + lyrics with ACE-Step 1.5').classes('neovak-subtitle mb-4')

        # ACE-Step status bar
        with ui.card().classes('w-full neovak-card p-4'):
            with ui.row().classes('items-center gap-3 w-full'):
                refs['status_icon'] = ui.icon('circle').classes('text-zinc-500')
                refs['status_label'] = ui.label('Checking ACE-Step...').classes('text-zinc-400 text-sm flex-1')
                refs['start_btn'] = ui.button('Start Server', on_click=lambda: ui.notify(
                    f'Run: cd {ACESTEP_DIR} && ./start_api_server_macos.sh', type='info', timeout=8000
                )).props('flat dense size=sm').classes('text-zinc-400')

        async def refresh_status():
            ok, msg = await asyncio.get_event_loop().run_in_executor(None, check_acestep_backend)
            if ok:
                refs['status_icon'].classes(remove='text-zinc-500 text-red-400', add='text-green-400')
                refs['status_label'].set_text(msg)
                refs['start_btn'].set_visibility(False)
            else:
                refs['status_icon'].classes(remove='text-zinc-500 text-green-400', add='text-red-400')
                refs['status_label'].set_text(msg)
                refs['start_btn'].set_visibility(True)

        ui.timer(0.1, refresh_status, once=True)

        # ── Mode toggle: Create / Cover / Repaint ──
        with ui.card().classes('w-full neovak-card p-4'):
            ui.label('MODE').classes('neovak-section-header')
            with ui.row().classes('gap-2'):
                refs['mode_btns'] = []
                for mode_id, mode_label in [('create', 'Create'), ('cover', 'Cover'), ('repaint', 'Repaint')]:
                    def set_mode(m=mode_id, idx=len(refs.get('mode_btns', []))):
                        state['mode'] = m
                        for j, b in enumerate(refs['mode_btns']):
                            b.props('color=primary' if j == idx else 'color=dark')
                        refs['audio_upload_card'].set_visibility(m in ('cover', 'repaint'))
                        refs['repaint_range_row'].set_visibility(m == 'repaint')
                    btn = ui.button(mode_label, on_click=set_mode).props(
                        f'dense no-caps {"color=primary" if mode_id == "create" else "color=dark"}'
                    )
                    refs['mode_btns'].append(btn)

        # ── Audio upload for Cover / Repaint ──
        with ui.card().classes('w-full neovak-card p-4') as refs['audio_upload_card']:
            ui.label('SOURCE AUDIO').classes('neovak-section-header')
            ui.label('Upload the audio file to cover or repaint').classes('text-zinc-500 text-xs')

            async def handle_audio_upload(e):
                upload_dir = OUTPUT_DIR / "uploads"
                upload_dir.mkdir(exist_ok=True)
                dest = upload_dir / e.name
                with open(dest, 'wb') as f:
                    f.write(e.content.read())
                state['audio_upload_path'] = str(dest)
                ui.notify(f'Uploaded: {e.name}', type='positive')

            ui.upload(on_upload=handle_audio_upload, auto_upload=True).props(
                'accept=".mp3,.wav,.flac,.ogg,.m4a" flat bordered'
            ).classes('w-full')

            with ui.row().classes('gap-4 mt-2') as refs['repaint_range_row']:
                rp_start = ui.number('Repaint start (s)', value=0.0, min=0, step=0.5).classes('w-36')
                rp_start.on('update:model-value', lambda e: state.update(repaint_start=float(e.args)))
                rp_end = ui.number('Repaint end (s)', value=0.0, min=0, step=0.5).classes('w-36')
                rp_end.on('update:model-value', lambda e: state.update(repaint_end=float(e.args)))
                ui.label('0 = end of track').classes('text-zinc-500 text-xs self-center')

        refs['audio_upload_card'].set_visibility(False)
        refs['repaint_range_row'].set_visibility(False)

        # ── Mood Compass (3x3 grid) ──
        with ui.card().classes('w-full neovak-card p-4'):
            ui.label('MOOD COMPASS').classes('neovak-section-header')
            ui.label('Click a mood to fill style tags').classes('text-zinc-500 text-xs mb-2')
            with ui.grid(columns=3).classes('gap-1 w-full'):
                for label, energy, valence in MOOD_GRID_LABELS:
                    def set_mood(e=energy, v=valence, lbl=label):
                        tags = mood_to_tags(e, v)
                        refs['caption'].value = tags
                        ui.notify(f'{lbl}: {tags}', type='info')
                    ui.button(label, on_click=set_mood).props('dense no-caps color=dark').classes('w-full')

        # Main input card
        with ui.card().classes('w-full neovak-card p-6'):
            ui.label('STYLE TAGS').classes('neovak-section-header')
            refs['caption'] = ui.textarea(
                placeholder='indie pop, acoustic guitar, warm vocals, dreamy atmosphere'
            ).classes('w-full neovak-prompt').props('outlined autogrow rows=2')

            with ui.row().classes('gap-1 flex-wrap mt-2'):
                for tag in MUSIC_STYLE_TAGS:
                    def add_tag(t=tag):
                        cur = refs['caption'].value or ''
                        if cur and not cur.endswith(', '):
                            cur = cur.rstrip(', ') + ', '
                        refs['caption'].value = cur + t
                    ui.button(tag, on_click=add_tag).props('flat dense size=sm').classes('text-zinc-400')

            ui.label('LYRICS (optional)').classes('neovak-section-header mt-4')
            refs['lyrics'] = ui.textarea(
                placeholder='[Verse]\nWalking down this road\nCarrying this heavy load\n\n[Chorus]\nBut we keep on moving'
            ).classes('w-full neovak-prompt').props('outlined autogrow rows=5')

            with ui.row().classes('gap-2 mt-1'):
                for marker in ['[Verse]', '[Chorus]', '[Bridge]', '[Outro]', '[Instrumental]']:
                    def insert_marker(m=marker):
                        cur = refs['lyrics'].value or ''
                        if cur and not cur.endswith('\n'):
                            cur += '\n'
                        refs['lyrics'].value = cur + m + '\n'
                    ui.button(marker, on_click=insert_marker).props('flat dense size=sm').classes('text-zinc-400')

            # Song structure templates
            ui.label('TEMPLATES').classes('neovak-section-header mt-3')
            with ui.row().classes('gap-1 flex-wrap'):
                for tpl_name, tpl_text in SONG_STRUCTURE_TEMPLATES.items():
                    def apply_template(t=tpl_text, n=tpl_name):
                        refs['lyrics'].value = t
                        ui.notify(f'Loaded: {n}', type='info')
                    ui.button(tpl_name, on_click=apply_template).props('flat dense size=sm no-caps').classes('text-zinc-400')

            # Duration estimate from lyrics
            refs['duration_estimate'] = ui.label('').classes('text-zinc-500 text-xs mt-1')

            def update_duration_estimate():
                lyrics_val = refs['lyrics'].value or ''
                if lyrics_val.strip():
                    est = estimate_duration_from_lyrics(lyrics_val)
                    mins, secs = divmod(est, 60)
                    refs['duration_estimate'].set_text(f'Estimated: ~{mins}:{secs:02d}')

                    def use_estimate():
                        state['duration'] = est
                        for j, btn in enumerate(refs['duration_btns']):
                            btn.props('color=dark')
                        ui.notify(f'Duration set to {est}s', type='info')

                    refs['use_estimate_link'].on('click', use_estimate)
                    refs['use_estimate_link'].set_visibility(True)
                else:
                    refs['duration_estimate'].set_text('')
                    refs['use_estimate_link'].set_visibility(False)

            refs['lyrics'].on('blur', update_duration_estimate)
            refs['use_estimate_link'] = ui.link('Use estimate', '').props('flat').classes('text-amber-400 text-xs')
            refs['use_estimate_link'].set_visibility(False)

            # Expand with AI + Surprise Me row
            async def do_expand():
                caption = refs['caption'].value
                if not caption:
                    ui.notify('Enter some style tags first', type='warning')
                    return
                refs['expand_btn'].disable()
                ui.notify('Expanding with AI...', type='info')
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: acestep_format_input(ACESTEP_URL, caption, refs['lyrics'].value or '')
                )
                if 'error' in result:
                    ui.notify(f'Expand failed: {result["error"]}', type='negative')
                else:
                    refs['caption'].value = result['caption']
                    if result['lyrics']:
                        refs['lyrics'].value = result['lyrics']
                    ui.notify('Expanded!', type='positive')
                refs['expand_btn'].enable()

            async def do_surprise():
                refs['surprise_btn'].disable()
                ui.notify('Rolling the dice...', type='info')
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: get_random_sample(ACESTEP_URL)
                    )
                    desc = result.get('description', result.get('caption', ''))
                    if desc:
                        refs['caption'].value = desc
                    lyrics_val = result.get('lyrics', '')
                    if lyrics_val:
                        refs['lyrics'].value = lyrics_val
                    dur = result.get('duration')
                    if dur:
                        try:
                            state['duration'] = int(float(dur))
                        except (ValueError, TypeError):
                            pass
                    lang = result.get('vocal_language', '')
                    instrumental = result.get('instrumental', False)
                    hint = 'instrumental' if instrumental else f'vocals ({lang})' if lang else ''
                    ui.notify(f'Got it! {hint}' if hint else 'Got a random sample!', type='positive')
                except Exception as e:
                    ui.notify(f'Surprise failed: {e}', type='negative')
                refs['surprise_btn'].enable()

            with ui.row().classes('gap-2 mt-2'):
                refs['expand_btn'] = ui.button('Expand with AI', on_click=do_expand).props('flat dense no-caps').classes('text-amber-400')
                refs['surprise_btn'] = ui.button('Surprise Me', on_click=do_surprise).props('flat dense no-caps').classes('text-amber-300')

            ui.label('DURATION').classes('neovak-section-header mt-4')
            refs['duration_btns'] = []
            with ui.row().classes('gap-2'):
                for i, (label, dur, desc) in enumerate(MUSIC_DURATION_PRESETS):
                    default_selected = (dur == 120)
                    def select_dur(d=dur, idx=i):
                        state['duration'] = d
                        for j, btn in enumerate(refs['duration_btns']):
                            btn.props('color=primary' if j == idx else 'color=dark')
                    btn = ui.button(label, on_click=select_dur).props(
                        f'dense no-caps {"color=primary" if default_selected else "color=dark"}'
                    )
                    btn.tooltip(desc)
                    refs['duration_btns'].append(btn)

            # Advanced settings (collapsible)
            with ui.expansion('Advanced Settings').classes('w-full mt-4'):
                with ui.column().classes('gap-3 py-2'):
                    with ui.row().classes('items-center gap-4'):
                        seed_input = ui.number('Seed', value=-1, min=-1, step=1).classes('w-32')
                        seed_input.on('update:model-value', lambda e: state.update(seed=int(e.args)))
                        refs['seed_input'] = seed_input
                        thinking_switch = ui.switch('Thinking (LM planner)', value=True)
                        thinking_switch.on('update:model-value', lambda e: state.update(thinking=e.args))
                    with ui.row().classes('items-center gap-4'):
                        steps_input = ui.number('Inference steps', value=30, min=1, max=100, step=1).classes('w-32')
                        steps_input.on('update:model-value', lambda e: state.update(infer_step=int(e.args)))
                        guidance_input = ui.number('Guidance scale', value=15.0, min=0, max=30, step=0.5).classes('w-32')
                        guidance_input.on('update:model-value', lambda e: state.update(guidance_scale=float(e.args)))
                    with ui.row().classes('items-center gap-4'):
                        gt_input = ui.number('Guidance (text)', value=0.0, min=0, max=10, step=0.5).classes('w-32')
                        gt_input.on('update:model-value', lambda e: state.update(guidance_scale_text=float(e.args)))
                        gl_input = ui.number('Guidance (lyric)', value=0.0, min=0, max=10, step=0.5).classes('w-32')
                        gl_input.on('update:model-value', lambda e: state.update(guidance_scale_lyric=float(e.args)))

                    # LM Model Switcher (Feature 5)
                    ui.label('LM QUALITY').classes('neovak-section-header mt-2')
                    refs['lm_select'] = ui.select(
                        options={'': 'Default (server)', 'acestep-5Hz-lm-1.7B': 'Standard (1.7B)', 'acestep-5Hz-lm-4B': 'Premium (4B)'},
                        value='',
                        on_change=lambda e: state.update(lm_model=e.value),
                    ).classes('w-full').props('outlined dense')
                    ui.label('Larger models produce better song structures but take longer').classes('text-zinc-500 text-xs')

                    # LoRA Management (Feature 11)
                    ui.label('LORA').classes('neovak-section-header mt-3')
                    refs['lora_path'] = ui.input('LoRA path (.safetensors)').classes('w-full').props('outlined dense')
                    refs['lora_status'] = ui.label('No LoRA loaded').classes('text-zinc-500 text-xs')

                    with ui.row().classes('gap-2 items-center'):
                        async def do_load_lora():
                            path = refs['lora_path'].value
                            if not path:
                                ui.notify('Enter a LoRA path', type='warning')
                                return
                            ok, msg = await asyncio.get_event_loop().run_in_executor(
                                None, lambda: load_lora(ACESTEP_URL, path)
                            )
                            if ok:
                                refs['lora_status'].set_text(f'Loaded: {path.split("/")[-1]}')
                                ui.notify('LoRA loaded', type='positive')
                            else:
                                ui.notify(f'Failed: {msg}', type='negative')

                        async def do_unload_lora():
                            ok, msg = await asyncio.get_event_loop().run_in_executor(
                                None, lambda: unload_lora(ACESTEP_URL)
                            )
                            if ok:
                                refs['lora_status'].set_text('No LoRA loaded')
                                ui.notify('LoRA unloaded', type='positive')
                            else:
                                ui.notify(f'Failed: {msg}', type='negative')

                        ui.button('Load', on_click=do_load_lora).props('dense no-caps color=dark')
                        ui.button('Unload', on_click=do_unload_lora).props('dense no-caps color=dark')
                        refs['lora_toggle'] = ui.switch('Enabled', value=False)
                        refs['lora_toggle'].on('update:model-value',
                            lambda e: asyncio.ensure_future(asyncio.get_event_loop().run_in_executor(
                                None, lambda: toggle_lora(ACESTEP_URL, e.args))))

                    refs['lora_scale'] = ui.slider(min=0.0, max=1.0, step=0.05, value=1.0).classes('w-full')
                    ui.label('LoRA Scale').classes('text-zinc-500 text-xs')
                    refs['lora_scale'].on('update:model-value',
                        lambda e: asyncio.ensure_future(asyncio.get_event_loop().run_in_executor(
                            None, lambda: set_lora_scale(ACESTEP_URL, float(e.args)))))

        # Generate + Lucky 4 buttons
        with ui.row().classes('w-full gap-2'):
            refs['gen_btn'] = ui.button('Generate Music', on_click=lambda: do_generate()).classes('flex-1 neovak-btn-primary')
            refs['lucky4_btn'] = ui.button('Lucky 4', on_click=lambda: do_lucky4()).props('no-caps color=amber').classes('').tooltip('Generate 4 variations')

        # Progress
        with ui.column().classes('w-full gap-2'):
            refs['progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full neovak-progress')
            refs['progress'].set_visibility(False)
            refs['status'] = ui.label('').classes('text-zinc-400 text-sm')

        # Seed Explorer grid (Feature 4)
        with ui.card().classes('w-full neovak-card p-4 hidden') as refs['batch_card']:
            ui.label('SEED EXPLORER').classes('neovak-section-header')
            refs['batch_grid'] = ui.grid(columns=2).classes('gap-2 w-full')

        # Output player
        with ui.card().classes('w-full neovak-card p-4 hidden') as refs['output_card']:
            refs['audio_player'] = ui.audio('').classes('w-full')
            with ui.row().classes('items-center gap-3 mt-2'):
                refs['output_info'] = ui.label('').classes('text-zinc-400 text-sm flex-1')
                refs['seed_label'] = ui.label('').classes('text-zinc-500 text-xs')
                refs['download_link'] = ui.link('Download', '').classes('text-amber-400 text-sm')

            # Album art upload (Feature 10)
            with ui.row().classes('gap-2 mt-2 items-center'):
                async def handle_art_upload(e):
                    if not state.get('last_output_path'):
                        ui.notify('Generate music first', type='warning')
                        return
                    art_dir = OUTPUT_DIR / "uploads"
                    art_dir.mkdir(exist_ok=True)
                    art_path = art_dir / e.name
                    with open(art_path, 'wb') as f:
                        f.write(e.content.read())
                    ok = embed_album_art(state['last_output_path'], str(art_path))
                    if ok:
                        ui.notify('Album art embedded!', type='positive')
                    else:
                        ui.notify('Failed to embed art (mutagen needed)', type='negative')

                ui.upload(on_upload=handle_art_upload, auto_upload=True).props(
                    'accept=".png,.jpg,.jpeg" label="Upload Cover Art" flat bordered dense'
                ).classes('max-w-xs')

        # Voice + Music Mixer (Feature 9)
        with ui.card().classes('w-full neovak-card p-4 hidden') as refs['mixer_card']:
            ui.label('VOICE + MUSIC MIXER').classes('neovak-section-header')
            refs['mixer_voice_path'] = None

            async def handle_voice_upload(e):
                upload_dir = OUTPUT_DIR / "uploads"
                upload_dir.mkdir(exist_ok=True)
                dest = upload_dir / e.name
                with open(dest, 'wb') as f:
                    f.write(e.content.read())
                refs['mixer_voice_path'] = str(dest)
                ui.notify(f'Voice loaded: {e.name}', type='positive')

            ui.upload(on_upload=handle_voice_upload, auto_upload=True).props(
                'accept=".mp3,.wav,.flac,.ogg,.m4a" label="Upload Voice Track" flat bordered'
            ).classes('w-full')

            with ui.row().classes('gap-4 mt-2 items-center'):
                refs['music_vol'] = ui.slider(min=0, max=100, step=5, value=30).classes('flex-1')
                ui.label('Music %').classes('text-zinc-500 text-xs')
                refs['voice_vol'] = ui.slider(min=0, max=100, step=5, value=100).classes('flex-1')
                ui.label('Voice %').classes('text-zinc-500 text-xs')

            async def do_mix():
                if not state.get('last_output_path'):
                    ui.notify('Generate music first', type='warning')
                    return
                if not refs.get('mixer_voice_path'):
                    ui.notify('Upload a voice track', type='warning')
                    return
                ui.notify('Mixing...', type='info')
                music_vol = refs['music_vol'].value / 100.0
                voice_vol = refs['voice_vol'].value / 100.0
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: mix_audio(
                        state['last_output_path'], refs['mixer_voice_path'],
                        music_volume=music_vol, voice_volume=voice_vol
                    )
                )
                if result:
                    refs['audio_player'].set_source(app.add_media_file(local_file=result))
                    refs['output_card'].classes(remove='hidden')
                    ui.notify('Mixed!', type='positive')
                else:
                    ui.notify('Mix failed (is ffmpeg installed?)', type='negative')

            ui.button('Mix', on_click=do_mix).props('no-caps color=amber').classes('w-full mt-2')

        # History strip
        with ui.column().classes('w-full'):
            ui.label('HISTORY').classes('neovak-section-header')
            refs['history_row'] = ui.row().classes('gap-2 flex-wrap')

    def _show_output(output_path, status_msg, caption):
        """Helper to display a generated track."""
        state['last_output_path'] = output_path
        refs['audio_player'].set_source(app.add_media_file(local_file=output_path))
        refs['output_card'].classes(remove='hidden')
        refs['mixer_card'].classes(remove='hidden')
        refs['output_info'].set_text(status_msg.split(' | ')[0] if ' | ' in status_msg else status_msg)
        seed_part = [p for p in status_msg.split(' | ') if 'seed' in p]
        refs['seed_label'].set_text(seed_part[0] if seed_part else '')
        refs['download_link'].props(f'href="{output_path}"')

        entry = {
            'path': output_path,
            'caption': caption,
            'duration': state['duration'],
            'status': status_msg,
        }
        state['history'].append(entry)
        with refs['history_row']:
            idx = len(state['history']) - 1
            def load_history(i=idx):
                h = state['history'][i]
                state['last_output_path'] = h['path']
                refs['audio_player'].set_source(app.add_media_file(local_file=h['path']))
                refs['output_card'].classes(remove='hidden')
                refs['output_info'].set_text(h['status'].split(' | ')[0])
            dur_label = f"{state['duration']}s"
            ui.button(f'{dur_label}', on_click=load_history).props('dense no-caps color=dark').tooltip(caption[:60])

    def _build_generate_kwargs():
        """Build kwargs for generate_music from current UI state."""
        caption = refs['caption'].value
        mode = state['mode']
        task_type = 'text2music'
        audio_path = ''
        if mode == 'cover':
            task_type = 'cover'
            audio_path = state.get('audio_upload_path', '') or ''
        elif mode == 'repaint':
            task_type = 'repaint'
            audio_path = state.get('audio_upload_path', '') or ''
        return dict(
            prompt=caption,
            lyrics=refs['lyrics'].value or '',
            duration=state['duration'],
            seed=state['seed'],
            thinking=state['thinking'],
            infer_step=state['infer_step'],
            guidance_scale=state['guidance_scale'],
            guidance_scale_text=state['guidance_scale_text'],
            guidance_scale_lyric=state['guidance_scale_lyric'],
            lm_model=state['lm_model'],
            audio_path=audio_path,
            repaint_start=state['repaint_start'],
            repaint_end=state['repaint_end'],
            task_type=task_type,
        )

    async def do_generate():
        caption = refs['caption'].value
        if not caption:
            ui.notify('Enter style tags first', type='warning')
            return
        mode = state['mode']
        if mode in ('cover', 'repaint') and not state.get('audio_upload_path'):
            ui.notify('Upload source audio first', type='warning')
            return

        refs['gen_btn'].disable()
        refs['progress'].set_visibility(True)
        refs['progress'].set_value(0)
        refs['status'].set_text('Submitting to ACE-Step...')

        try:
            kwargs = _build_generate_kwargs()
            output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                None, lambda: generate_music(**kwargs)
            )

            if output_path:
                _show_output(output_path, status_msg, caption)
                refs['status'].set_text('Done!')
                ui.notify('Music generated!', type='positive')
            else:
                refs['status'].set_text(f'Failed: {status_msg}')
                ui.notify(status_msg, type='negative')
        except Exception as e:
            refs['status'].set_text(f'Error: {e}')
            ui.notify(str(e), type='negative')
        finally:
            refs['gen_btn'].enable()
            refs['progress'].set_visibility(False)

    async def do_lucky4():
        caption = refs['caption'].value
        if not caption:
            ui.notify('Enter style tags first', type='warning')
            return

        refs['lucky4_btn'].disable()
        refs['gen_btn'].disable()
        refs['progress'].set_visibility(True)
        refs['progress'].set_value(0)
        refs['status'].set_text('Generating 4 variations...')

        try:
            from acestep_client import generate_music_batch as _batch
            results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _batch(
                    url=ACESTEP_URL,
                    caption=caption,
                    lyrics=refs['lyrics'].value or '',
                    duration=state['duration'],
                    batch_size=4,
                    thinking=state['thinking'],
                    infer_step=state['infer_step'],
                    guidance_scale=state['guidance_scale'],
                    guidance_scale_text=state['guidance_scale_text'],
                    guidance_scale_lyric=state['guidance_scale_lyric'],
                    lm_model=state['lm_model'],
                )
            )

            refs['batch_card'].classes(remove='hidden')
            refs['batch_grid'].clear()

            valid_count = sum(1 for r in results if r.get('path'))
            if valid_count == 0:
                refs['status'].set_text(f'Batch failed: {results[0].get("status", "unknown")}')
                ui.notify('Batch generation failed', type='negative')
            else:
                with refs['batch_grid']:
                    for r in results:
                        if not r.get('path'):
                            continue
                        with ui.card().classes('neovak-card p-3'):
                            ui.label(f'Seed: {r["seed"]}').classes('text-zinc-400 text-xs font-mono')
                            ui.audio(app.add_media_file(local_file=r['path'])).classes('w-full')
                            ui.label(r['status']).classes('text-zinc-500 text-xs')

                            def use_this(path=r['path'], seed=r['seed'], st=r['status']):
                                _show_output(path, st, caption)
                                state['seed'] = int(seed) if seed else -1
                                refs['seed_input'].value = state['seed']
                                ui.notify(f'Using seed {seed}', type='positive')

                            ui.button('Use This', on_click=use_this).props('dense no-caps color=amber').classes('w-full mt-1')

                refs['status'].set_text(f'Done! {valid_count} variations')
                ui.notify(f'{valid_count} variations ready', type='positive')
        except Exception as e:
            refs['status'].set_text(f'Error: {e}')
            ui.notify(str(e), type='negative')
        finally:
            refs['lucky4_btn'].enable()
            refs['gen_btn'].enable()
            refs['progress'].set_visibility(False)


# ═══════════════════════════════════════════════════════════════════════════════
# SOUND EFFECTS GENERATION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def sfx_generation_panel():
    """Sound effects generation — sound board, quick prompts by category, 3-variation generator."""

    state = {
        'duration': 2.0,
        'category': None,
        'variations': 1,
        'soundboard': [],
    }
    refs = {}

    sfx_status = get_sfx_model_status()

    with ui.column().classes('w-full max-w-2xl mx-auto gap-6 py-6'):
        ui.label('Sound Effects').classes('neovak-title')
        ui.label(TAB_SUBTITLES['sfx']).classes('neovak-tab-subtitle')
        ui.label('Generate sound effects from text descriptions').classes('neovak-subtitle mb-4')

        if not sfx_status['available']:
            with ui.card().classes('w-full neovak-card p-6 border-amber-500/30'):
                ui.label('AudioGen Not Installed').classes('text-amber-400 font-medium mb-2')
                ui.label('Sound effects generation requires AudioCraft or AudioLDM2.').classes('text-zinc-400 text-sm mb-3')
                with ui.element('pre').classes('bg-zinc-900 p-3 rounded text-xs text-zinc-300 overflow-x-auto'):
                    ui.label('pip install audiocraft  # Recommended')
                ui.label('After installing, restart NeoVak.').classes('text-zinc-500 text-xs mt-2')

        with ui.card().classes('w-full neovak-card p-6'):
            # Category selector with quick prompts
            ui.label('CATEGORY').classes('neovak-section-header')
            with ui.row().classes('gap-2 flex-wrap mb-2'):
                for cat_id, cat_info in SFX_CATEGORIES.items():
                    def select_category(c=cat_id, info=cat_info):
                        state['category'] = c
                        import random
                        example = random.choice(info['examples'])
                        refs['sfx_prompt'].value = example
                        _update_quick_prompts(c)
                        ui.notify(f'Category: {info["label"]}', type='info')
                    ui.button(cat_info['label'], on_click=select_category).props('flat dense size=sm').classes('text-zinc-400 hover:text-amber-400')

            # Quick prompts by category (populated dynamically)
            refs['quick_prompts_row'] = ui.row().classes('gap-2 flex-wrap mb-3')

            def _update_quick_prompts(cat_key):
                refs['quick_prompts_row'].clear()
                prompts = SFX_QUICK_PROMPTS.get(cat_key, [])
                if not prompts:
                    cat_name_map = {c: info['label'] for c, info in SFX_CATEGORIES.items()}
                    display_name = cat_name_map.get(cat_key, cat_key)
                    prompts = SFX_QUICK_PROMPTS.get(display_name, [])
                with refs['quick_prompts_row']:
                    for p in prompts:
                        def fill_prompt(prompt=p):
                            refs['sfx_prompt'].value = prompt
                        ui.button(p, on_click=fill_prompt).props('flat dense no-caps size=sm').classes('neovak-style-chip')

            # Show default quick prompts
            for cat_name, prompts in SFX_QUICK_PROMPTS.items():
                with refs['quick_prompts_row']:
                    for p in prompts[:2]:
                        def fill_prompt(prompt=p):
                            refs['sfx_prompt'].value = prompt
                        ui.button(p, on_click=fill_prompt).props('flat dense no-caps size=sm').classes('neovak-style-chip')
                break

            ui.label('DESCRIPTION').classes('neovak-section-header')
            refs['sfx_prompt'] = ui.textarea(
                placeholder='Describe the sound... e.g., "thunder rolling in the distance"'
            ).classes('w-full neovak-prompt').props('outlined autogrow rows=2')

            # Duration
            ui.label('DURATION').classes('neovak-section-header mt-4')
            refs['sfx_dur_btns'] = []
            with ui.row().classes('gap-2'):
                for i, (label, dur, desc) in enumerate(SFX_DURATION_PRESETS):
                    def select_dur(d=dur, idx=i):
                        state['duration'] = d
                        for j, btn in enumerate(refs['sfx_dur_btns']):
                            btn.props('color=primary' if j == idx else 'color=dark')
                    is_default = (dur == 2.0)
                    btn = ui.button(label, on_click=select_dur).props(f'dense no-caps {"color=primary" if is_default else "color=dark"}')
                    btn.tooltip(desc)
                    refs['sfx_dur_btns'].append(btn)

            # Style modifiers
            ui.label('STYLE').classes('neovak-section-header mt-4')
            with ui.row().classes('gap-2 flex-wrap'):
                for tag, desc in SFX_STYLE_TAGS:
                    def add_style(t=tag):
                        current = refs['sfx_prompt'].value or ''
                        if t not in current.lower():
                            refs['sfx_prompt'].value = f'{current}, {t}' if current else t
                    btn = ui.button(tag, on_click=add_style).props('flat dense size=sm').classes('text-zinc-400')
                    btn.tooltip(desc)

            # Variations selector
            ui.label('VARIATIONS').classes('neovak-section-header mt-4')
            refs['sfx_var_btns'] = []
            with ui.row().classes('gap-2 items-center'):
                for n in [1, 2, 3, 4]:
                    def set_var(v=n):
                        state['variations'] = v
                        for j, btn in enumerate(refs['sfx_var_btns']):
                            btn.props('color=primary' if j + 1 == v else 'color=dark')
                    btn = ui.button(str(n), on_click=set_var).props(f'dense {"color=primary" if n == 1 else "color=dark"}').classes('w-10')
                    refs['sfx_var_btns'].append(btn)
                ui.label('Generate multiple variations').classes('text-zinc-500 text-xs ml-2')

            # Generate 3 Variations quick button
            def do_gen_3():
                state['variations'] = 3
                for j, btn in enumerate(refs['sfx_var_btns']):
                    btn.props('color=primary' if j + 1 == 3 else 'color=dark')
                do_generate_sfx()
            ui.button('Generate 3 Variations', on_click=lambda: do_gen_3()).props('flat dense no-caps').classes('neovak-enhance-btn mt-2').tooltip('Quick: generate 3 versions')

        # Generate button
        refs['sfx_gen_btn'] = ui.button('Generate Sound Effect', on_click=lambda: do_generate_sfx()).classes('w-full neovak-btn-primary')
        if not sfx_status['available']:
            refs['sfx_gen_btn'].disable()

        with ui.column().classes('w-full gap-2'):
            refs['sfx_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full neovak-progress')
            refs['sfx_progress'].set_visibility(False)
            refs['sfx_status'] = ui.label('').classes('text-zinc-400 text-sm')

        # Output audio players
        refs['sfx_outputs'] = ui.column().classes('w-full gap-3')

        # Sound Board — persistent grid of generated sounds
        with ui.column().classes('w-full'):
            ui.label('SOUND BOARD').classes('neovak-section-header')
            refs['soundboard_grid'] = ui.grid(columns=3).classes('gap-2 w-full')

    async def do_generate_sfx():
        prompt = refs['sfx_prompt'].value
        if not prompt:
            ui.notify('Describe the sound you want', type='warning')
            return

        refs['sfx_gen_btn'].disable()
        refs['sfx_gen_btn'].text = 'Warming tubes...'
        refs['sfx_gen_btn'].classes(add='neovak-warming')
        refs['sfx_progress'].set_visibility(True)
        refs['sfx_status'].set_text('Generating sound effect...')
        refs['sfx_outputs'].clear()

        await asyncio.sleep(0.8)
        refs['sfx_gen_btn'].text = 'Creating...'
        refs['sfx_gen_btn'].classes(remove='neovak-warming')

        def progress_cb(pct, msg):
            refs['sfx_progress'].set_value(pct / 100)
            refs['sfx_status'].set_text(msg)

        try:
            output_paths, status = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: generate_sfx(
                    prompt=prompt,
                    duration=state['duration'],
                    num_variations=state['variations'],
                    progress_callback=progress_cb,
                )
            )

            if output_paths:
                with refs['sfx_outputs']:
                    for i, path in enumerate(output_paths):
                        with ui.card().classes('w-full neovak-card p-3'):
                            with ui.row().classes('items-center gap-3'):
                                ui.label(f'Variation {i+1}').classes('text-amber-400 text-sm font-medium')
                                ui.audio(path).classes('flex-1')
                                ui.button(icon='download', on_click=lambda p=path: ui.download(p)).props('flat dense').classes('text-zinc-400')

                # Add to sound board
                for path in output_paths:
                    short_desc = prompt[:20] + ('...' if len(prompt) > 20 else '')
                    state['soundboard'].append({'path': path, 'desc': short_desc})
                    with refs['soundboard_grid']:
                        async def play_sound(p=path):
                            await ui.run_javascript(f'''
                                new Audio("{p}").play();
                            ''')
                        with ui.element('div').classes('neovak-soundboard-btn').on('click', play_sound):
                            ui.icon('play_circle', size='20px').style('color: var(--tube-warm);')
                            ui.label(short_desc).classes('text-zinc-400 text-xs mt-1')

                refs['sfx_status'].set_text(f'Generated {len(output_paths)} sound effect(s)!')
                ui.notify('Sound effects generated!', type='positive')
            else:
                refs['sfx_status'].set_text(f'{status}')
                ui.notify(status, type='negative')

        except Exception as e:
            refs['sfx_status'].set_text(f'Error: {str(e)}')
            ui.notify(str(e), type='negative')

        finally:
            refs['sfx_gen_btn'].enable()
            refs['sfx_gen_btn'].text = 'Generate Sound Effect'
            refs['sfx_progress'].set_visibility(False)


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
                image_tab = ui.tab('Image Generation', icon='image')
                video_tab = ui.tab('Video Generation', icon='movie')
                voice_tab = ui.tab('Voice Generation', icon='mic')
                sfx_tab = ui.tab('Sound Effects', icon='graphic_eq')
                music_tab = ui.tab('Music Generation', icon='music_note')

            with ui.tab_panels(tabs, value=image_tab).classes('w-full flex-1'):
                with ui.tab_panel(image_tab):
                    image_generation_panel()
                with ui.tab_panel(video_tab):
                    video_generation_panel()
                with ui.tab_panel(voice_tab):
                    voice_generation_panel()
                with ui.tab_panel(sfx_tab):
                    sfx_generation_panel()
                with ui.tab_panel(music_tab):
                    music_generation_panel()

        # ── System Status Bar ──
        with ui.element('div').classes('neovak-status-bar w-full'):
            status_refs = {}

            with ui.element('div').classes('neovak-status-bar-item'):
                status_refs['comfyui_dot'] = ui.element('div').classes('neovak-whisper-dot cold')
                status_refs['comfyui_label'] = ui.label('ComfyUI: Checking...')

            ui.element('div').classes('neovak-status-bar-separator')

            with ui.element('div').classes('neovak-status-bar-item'):
                status_refs['acestep_dot'] = ui.element('div').classes('neovak-whisper-dot cold')
                status_refs['acestep_label'] = ui.label('ACE-Step: Checking...')

            ui.element('div').classes('neovak-status-bar-separator')

            with ui.element('div').classes('neovak-status-bar-item'):
                status_refs['voice_dot'] = ui.element('div').classes('neovak-whisper-dot cold')
                status_refs['voice_label'] = ui.label('Voice: Checking...')

            ui.element('div').classes('neovak-status-bar-separator')

            status_refs['ram_label'] = ui.label('')

            async def update_status_bar():
                backend_ok, _ = check_backend()
                if backend_ok:
                    status_refs['comfyui_dot'].classes(remove='cold')
                    status_refs['comfyui_label'].set_text('ComfyUI: Connected')
                else:
                    status_refs['comfyui_dot'].classes(add='cold')
                    status_refs['comfyui_label'].set_text('ComfyUI: Offline')

                ace_ok, _ = await asyncio.get_event_loop().run_in_executor(None, check_acestep_backend)
                if ace_ok:
                    status_refs['acestep_dot'].classes(remove='cold')
                    status_refs['acestep_label'].set_text('ACE-Step: Connected')
                else:
                    status_refs['acestep_dot'].classes(add='cold')
                    status_refs['acestep_label'].set_text('ACE-Step: Offline')

                voice_status = get_voice_model_status()
                if voice_status.get('loaded'):
                    status_refs['voice_dot'].classes(remove='cold')
                    status_refs['voice_label'].set_text('Voice: Ready')
                else:
                    status_refs['voice_dot'].classes(add='cold')
                    status_refs['voice_label'].set_text('Voice: Ready')

                avail = SYSTEM.get_available_memory_gb()
                total = SYSTEM.ram_gb
                used = total - avail
                status_refs['ram_label'].set_text(f'RAM: {used:.0f}/{total} GB')

            ui.timer(0.1, update_status_bar, once=True)
            ui.timer(15.0, update_status_bar)

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
