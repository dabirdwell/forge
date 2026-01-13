"""
🔥 Forge - Local AI Creative Suite
Version 1.0.0

A unified interface for AI image and video generation, running entirely local.
Think "LM Studio for multimedia generation."

Uses NiceGUI with custom styling for a polished creative tool experience.
Backend logic in forge_backend.py.
"""

from nicegui import ui, app
from pathlib import Path
import asyncio

from forge_backend import (
    SYSTEM, OUTPUT_DIR, MODEL_SEARCH_PATHS,
    Model, LoRA, discover_all_models, discover_loras,
    check_backend, generate_image, generate_video, generate_video_from_image, enhance_prompt,
    RecommendedModel, get_recommended_models
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "Forge"
APP_VERSION = "1.0.0"

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
    ("Standard", 30, 7, "Balanced quality"),
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
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════

CUSTOM_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════════════════
   FORGE v1.0.0 - Professional Tool Aesthetic
   Inspired by Affinity Photo / Apple Keynote
   Clean, restrained, functional
   ═══════════════════════════════════════════════════════════════════════════════ */

/* ─────────────────────────────────────────────────────────────────────────────
   COLOR SYSTEM
   Primary: Cyan (#06b6d4) - used sparingly for actions and focus
   Surface: Gray scale from #000 to #1a1a1a
   Text: White (#fff) to muted (#666)
   ───────────────────────────────────────────────────────────────────────────── */

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

/* ─────────────────────────────────────────────────────────────────────────────
   BASE
   ───────────────────────────────────────────────────────────────────────────── */
* { 
    transition: background-color 0.15s ease, 
                border-color 0.15s ease, 
                color 0.15s ease,
                opacity 0.15s ease;
}

.nicegui-content {
    background: var(--surface-1) !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   TYPOGRAPHY - Clear hierarchy
   ───────────────────────────────────────────────────────────────────────────── */
.forge-title { 
    font-size: 1.5rem; 
    font-weight: 600; 
    color: var(--text-primary);
    letter-spacing: -0.01em;
}
.forge-subtitle { 
    font-size: 0.875rem; 
    color: var(--text-secondary);
    font-weight: 400;
}
.forge-section { 
    font-size: 0.6875rem; 
    font-weight: 500; 
    text-transform: uppercase; 
    letter-spacing: 0.08em; 
    color: var(--text-muted); 
    margin-bottom: 0.75rem;
}
.forge-label { 
    font-size: 0.8125rem; 
    font-weight: 500; 
    color: var(--text-secondary);
}
.forge-hint { 
    font-size: 0.75rem; 
    color: var(--text-muted);
}

/* ─────────────────────────────────────────────────────────────────────────────
   PANELS - Clean tool panels
   ───────────────────────────────────────────────────────────────────────────── */
.forge-card {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
}
.forge-card:hover {
    border-color: var(--border) !important;
}

.forge-card-elevated {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   INPUTS - Professional form controls
   ───────────────────────────────────────────────────────────────────────────── */
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
    outline: none !important;
}
.forge-prompt textarea::placeholder {
    color: var(--text-muted) !important;
}

/* Input fields */
.q-field--dark .q-field__control {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
}
.q-field--dark .q-field__control:hover {
    border-color: var(--border) !important;
}
.q-field--focused .q-field__control {
    border-color: var(--accent) !important;
}
.q-field--dark .q-field__native {
    color: var(--text-primary) !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   BUTTONS - Accent color for primary actions only
   ───────────────────────────────────────────────────────────────────────────── */
.forge-btn-primary {
    background: var(--accent) !important;
    color: var(--surface-0) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 6px !important;
    border: none !important;
    box-shadow: none !important;
}
.forge-btn-primary:hover {
    background: var(--accent-hover) !important;
}
.forge-btn-primary:active {
    opacity: 0.9;
}
.forge-btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Secondary buttons - subtle */
.forge-preset {
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.875rem !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
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

/* ─────────────────────────────────────────────────────────────────────────────
   TABS - Clean segmented control
   ───────────────────────────────────────────────────────────────────────────── */
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
.q-tab:hover {
    color: var(--text-secondary) !important;
}
.q-tab--active {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}
.q-tab-panel {
    padding: 0 !important;
}
.q-tabs__content--align-center .q-tab__indicator {
    display: none !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   DROPDOWNS
   ───────────────────────────────────────────────────────────────────────────── */
.q-menu {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5) !important;
}
.q-item {
    border-radius: 4px !important;
    margin: 2px 4px !important;
    min-height: 36px !important;
    color: var(--text-secondary) !important;
}
.q-item:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}
.q-item--active {
    background: var(--accent-muted) !important;
    color: var(--accent) !important;
}
.q-item__label { 
    color: inherit !important; 
}

/* ─────────────────────────────────────────────────────────────────────────────
   SLIDERS
   ───────────────────────────────────────────────────────────────────────────── */
.q-slider__track { 
    background: var(--surface-4) !important; 
    border-radius: 2px !important;
    height: 4px !important;
}
.q-slider__inner { 
    background: var(--accent) !important;
    border-radius: 2px !important;
}
.q-slider__thumb { 
    background: var(--text-primary) !important;
    border: none !important;
    width: 14px !important;
    height: 14px !important;
}
.q-slider__thumb:hover {
    transform: scale(1.1);
}
.q-slider__focus-ring { 
    background: var(--accent-muted) !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   PROGRESS
   ───────────────────────────────────────────────────────────────────────────── */
.forge-progress {
    background: var(--surface-3) !important;
    border-radius: 4px !important;
    height: 6px !important;
    overflow: hidden;
}
.forge-progress .q-linear-progress__track { 
    background: transparent !important;
}
.forge-progress .q-linear-progress__model { 
    background: var(--accent) !important;
}
.forge-progress-text {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    font-weight: 500;
}

/* ─────────────────────────────────────────────────────────────────────────────
   EXPANSION PANELS
   ───────────────────────────────────────────────────────────────────────────── */
.q-expansion-item { 
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    margin-bottom: 8px !important;
}
.q-expansion-item__container { 
    background: transparent !important;
}
.q-expansion-item--expanded { 
    border-color: var(--border) !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   GALLERY
   ───────────────────────────────────────────────────────────────────────────── */
.forge-gallery-item {
    width: 72px;
    height: 72px;
    border-radius: 6px;
    object-fit: cover;
    cursor: pointer;
    border: 2px solid transparent;
    opacity: 0.8;
}
.forge-gallery-item:hover {
    opacity: 1;
    border-color: var(--accent);
}

/* ─────────────────────────────────────────────────────────────────────────────
   SPECIAL ELEMENTS
   ───────────────────────────────────────────────────────────────────────────── */

/* Section panel - groups related controls */
.forge-section-panel {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}
.forge-section-panel:hover {
    border-color: var(--border) !important;
}

/* Section header inside panel */
.forge-section-header {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
}

/* Enhance button */
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

/* Inspiration chip */
.forge-inspire {
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    cursor: pointer;
}
.forge-inspire:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Aspect ratio preview */
.forge-aspect-preview {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    transition: width 0.25s ease, height 0.25s ease !important;
}

/* Empty state */
.forge-empty-state {
    background: var(--surface-2) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}
.forge-empty-state:hover {
    border-color: var(--text-muted) !important;
}

/* Tooltip */
.q-tooltip { 
    background: var(--surface-4) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    font-size: 0.75rem !important;
    padding: 0.375rem 0.625rem !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: var(--surface-4);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--border);
}

/* Welcome card */
.forge-welcome {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Status indicators */
.forge-status-ready {
    background: #22c55e;
}
.forge-status-error {
    background: #ef4444;
}

/* ─────────────────────────────────────────────────────────────────────────────
   VIDEO PANEL v0.7 - Output-Centric Layout
   ───────────────────────────────────────────────────────────────────────────── */

/* Command bar - top of video panel */
.forge-command-bar {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
}

/* Model dropdown items with descriptions */
.forge-model-item {
    padding: 0.5rem 0.75rem !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    min-width: 280px;
}
.forge-model-item:last-child {
    border-bottom: none !important;
}
.forge-model-item:hover {
    background: var(--accent-muted) !important;
}

/* Hero area - centered output */
.forge-hero-area {
    background: var(--surface-1) !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    min-height: 400px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.forge-video-container {
    background: var(--surface-0) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden;
    max-width: 640px;
    width: 100%;
    aspect-ratio: 16/10;
}

.forge-video-container video {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* Transport controls */
.forge-transport {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--surface-2);
    border-radius: 8px;
    margin-top: 1rem;
}

.forge-transport-btn {
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
}
.forge-transport-btn:hover {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
    border-color: var(--border) !important;
}
.forge-transport-btn.active {
    background: var(--accent-muted) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

.forge-seed-display {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-muted);
    background: var(--surface-3);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

/* History strip - horizontal scroll */
.forge-history-strip {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    overflow-x: auto;
    white-space: nowrap;
}

.forge-history-item {
    display: inline-block;
    width: 80px;
    height: 50px;
    background: var(--surface-3);
    border: 2px solid transparent;
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    position: relative;
    transition: all 0.15s ease;
    margin-right: 0.5rem;
}
.forge-history-item:hover {
    border-color: var(--accent);
    transform: scale(1.05);
}
.forge-history-item.active {
    border-color: var(--accent);
}
.forge-history-item video,
.forge-history-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.forge-history-item .play-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    opacity: 0.8;
    font-size: 20px;
}

/* Mode tabs - segmented control */
.forge-mode-tabs {
    background: var(--surface-2) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    display: inline-flex;
    gap: 4px;
}

.forge-mode-tab {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    cursor: pointer;
    transition: all 0.15s ease;
}
.forge-mode-tab:hover {
    color: var(--text-secondary) !important;
    background: var(--surface-3) !important;
}
.forge-mode-tab.active {
    background: var(--surface-4) !important;
    color: var(--text-primary) !important;
}

/* Settings bar - compact presets */
.forge-settings-bar {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

.forge-preset-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.forge-preset-label {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
}

.forge-preset-options {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.forge-radio-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.8125rem;
}
.forge-radio-option:hover {
    color: var(--text-primary);
}
.forge-radio-option.selected {
    color: var(--accent);
}
.forge-radio-option .radio-dot {
    width: 14px;
    height: 14px;
    border: 2px solid var(--border);
    border-radius: 50%;
    position: relative;
}
.forge-radio-option.selected .radio-dot {
    border-color: var(--accent);
}
.forge-radio-option.selected .radio-dot::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 6px;
    height: 6px;
    background: var(--accent);
    border-radius: 50%;
}

/* Advanced settings expander */
.forge-advanced-toggle {
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    padding: 0.375rem 0.75rem !important;
    border-radius: 6px !important;
}
.forge-advanced-toggle:hover {
    border-color: var(--border) !important;
    color: var(--text-secondary) !important;
}

/* Mode-specific input areas */
.forge-mode-input-area {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

.forge-guide-frames {
    display: flex;
    align-items: center;
    gap: 1rem;
}

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

/* Command bar prompt input - inline single line */
.forge-command-prompt input {
    background: var(--surface-3) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.75rem !important;
    color: var(--text-primary) !important;
    font-size: 0.875rem !important;
}
.forge-command-prompt input:focus {
    border-color: var(--accent) !important;
    outline: none !important;
}
.forge-command-prompt input::placeholder {
    color: var(--text-muted) !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   IMAGE PANEL v0.7 - Output-Centric Layout
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

.forge-image-container.constrained {
    max-height: 600px;
}
.forge-image-container.constrained img {
    height: 100%;
    width: auto;
    margin: 0 auto;
}

/* Quick actions bar below image */
.forge-quick-actions {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--surface-2);
    border-radius: 8px;
    margin-top: 1rem;
}

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

/* Source image upload for variations/inpaint */
.forge-source-upload {
    width: 160px;
    height: 120px;
    background: var(--surface-3);
    border: 2px dashed var(--border);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
}
.forge-source-upload:hover {
    border-color: var(--accent);
    background: var(--accent-muted);
}
.forge-source-upload.has-image {
    border-style: solid;
    border-color: var(--border);
}
.forge-source-upload img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 6px;
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

# Simple in-memory history (persists during session)
generation_history = []  # Images
video_generation_history = []  # Videos

def add_to_history(path: str, prompt: str, model: str, seed: int = -1):
    """Add an image generation to history."""
    generation_history.insert(0, {
        'path': path,
        'prompt': prompt,
        'model': model,
        'seed': seed,
        'timestamp': __import__('time').time()
    })
    if len(generation_history) > 20:
        generation_history.pop()

def add_video_to_history(path: str, prompt: str, model: str, seed: int = -1):
    """Add a video generation to history."""
    video_generation_history.insert(0, {
        'path': path,
        'prompt': prompt,
        'model': model,
        'seed': seed,
        'timestamp': __import__('time').time()
    })
    if len(video_generation_history) > 20:
        video_generation_history.pop()

def update_gallery(refs):
    """Update the image gallery with recent generations."""
    if 'gallery_container' not in refs:
        return
    refs['gallery_container'].clear()
    
    with refs['gallery_container']:
        for item in generation_history[:8]:
            def show_image(path=item['path'], prompt=item['prompt']):
                refs['output_img'].set_source(path)
                refs['output_img'].classes(remove='hidden')
                refs['placeholder_col'].set_visibility(False)
                ui.notify(f'"{prompt[:50]}..."' if len(prompt) > 50 else f'"{prompt}"', position='top', timeout=2000)
            
            ui.image(item['path']).classes('forge-gallery-item').on('click', show_image).tooltip(item['prompt'][:60] + '...' if len(item['prompt']) > 60 else item['prompt'])

def update_video_gallery(refs):
    """Update the video gallery with recent generations."""
    if 'video_gallery_container' not in refs:
        return
    refs['video_gallery_container'].clear()
    
    with refs['video_gallery_container']:
        for item in video_generation_history[:6]:
            def show_video(path=item['path'], prompt=item['prompt']):
                refs['output_video'].set_source(path)
                refs['output_video'].classes(remove='hidden')
                refs['video_placeholder'].set_visibility(False)
                ui.notify(f'"{prompt[:50]}..."' if len(prompt) > 50 else f'"{prompt}"', position='top', timeout=2000)
            
            # Use first frame as thumbnail (or just a placeholder)
            with ui.element('div').classes('forge-gallery-item bg-zinc-800 flex items-center justify-center cursor-pointer').on('click', show_video):
                ui.icon('play_circle', size='24px').classes('text-zinc-500')
            # TODO: Generate actual video thumbnails

# ═══════════════════════════════════════════════════════════════════════════════
# THEME & STATE
# ═══════════════════════════════════════════════════════════════════════════════

def setup_theme():
    """Configure theme and inject custom CSS."""
    ui.add_head_html(CUSTOM_CSS)
    
    # Keyboard shortcuts
    ui.add_head_html("""
    <script>
    document.addEventListener('keydown', function(e) {
        // Cmd/Ctrl + Enter to generate
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            const genBtn = document.querySelector('[data-forge-generate]');
            if (genBtn) genBtn.click();
        }
    });
    </script>
    """)
    
    ui.colors(
        primary='#6366f1',
        secondary='#f59e0b',
        accent='#8b5cf6',
        dark='#0a0a0b',
        positive='#22c55e',
        negative='#ef4444',
        info='#3b82f6',
        warning='#f59e0b',
    )
    ui.dark_mode().enable()

# Global state
ALL_MODELS = {}
ALL_LORAS = []

def init_models():
    """Discover models and LoRAs on system."""
    global ALL_MODELS, ALL_LORAS
    ALL_MODELS = discover_all_models()
    ALL_LORAS = discover_loras()
    total = sum(len(m) for m in ALL_MODELS.values())
    print(f"📦 Discovered {total} models, {len(ALL_LORAS)} LoRAs")
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
        ui.label('Welcome to Forge').classes('forge-title text-white')
        ui.label('Your local AI creative studio').classes('forge-subtitle mb-8')
        
        with ui.card().classes('w-full forge-card p-6'):
            ui.label('📦 No AI models found').classes('text-xl text-white font-semibold mb-4')
            
            ui.label('Forge automatically discovers models in these folders:').classes('forge-description mb-3')
            
            with ui.column().classes('gap-1 mb-4 bg-zinc-800 rounded-lg p-3'):
                for path in MODEL_SEARCH_PATHS:
                    ui.label(f'• {path}').classes('text-zinc-400 text-sm font-mono')
            
            ui.label('To get started, download a model:').classes('forge-description mb-3')
            
            with ui.card().classes('w-full bg-indigo-950/50 border border-indigo-800 p-4 mb-4'):
                ui.label('Recommended first model').classes('text-indigo-300 text-sm font-semibold mb-2')
                ui.label('DreamShaper XL').classes('text-white text-lg font-semibold')
                ui.label('Artistic images with dreamy, painterly style. 6.5 GB.').classes('text-zinc-400 text-sm')
                ui.link('Download from CivitAI →', 'https://civitai.com/models/112902/dreamshaper-xl').classes('text-indigo-400 text-sm mt-2')
            
            with ui.row().classes('gap-3'):
                ui.button('Rescan for models', on_click=lambda: ui.navigate.to('/')).props('outline').classes('text-zinc-300')
                ui.link('Setup Guide', 'https://github.com/comfyanonymous/ComfyUI#installing').classes('text-zinc-400 text-sm self-center')

def welcome_no_backend():
    """Shown when models exist but ComfyUI isn't running."""
    with ui.column().classes('w-full max-w-2xl mx-auto items-center py-12'):
        ui.label('🔥').classes('text-6xl mb-4')
        ui.label('Almost ready!').classes('forge-title text-white')
        ui.label('Forge found your models, but ComfyUI needs to be running').classes('forge-subtitle mb-8')
        
        total = sum(len(m) for m in ALL_MODELS.values())
        ui.label(f'✓ Found {total} models on your system').classes('text-green-400 mb-6')
        
        # Determine ComfyUI path
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
                    # Start ComfyUI in background
                    subprocess.Popen(
                        ['python3', 'main.py'],
                        cwd=str(comfyui_path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    status_label.set_text('ComfyUI starting... waiting for backend')
                    # Wait and check
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
            
            ui.label('Or start manually:').classes('forge-description mb-3')
            with ui.card().classes('w-full bg-zinc-800 p-4 mb-4'):
                ui.label(f'cd {comfyui_path} && python main.py').classes('text-green-400 font-mono text-sm')
            
            ui.button('Check again', on_click=lambda: ui.navigate.to('/')).props('outline').classes('text-zinc-300')

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

def app_header():
    """Clean header with tagline and status."""
    
    # Platform-aware tagline
    platform_name = "your computer"
    if "mac" in SYSTEM.machine.lower() or "apple" in SYSTEM.chip.lower():
        platform_name = "your Mac"
    elif "windows" in SYSTEM.machine.lower():
        platform_name = "your PC"
    elif "linux" in SYSTEM.machine.lower():
        platform_name = "your machine"
    
    with ui.row().classes('w-full max-w-4xl mx-auto justify-between items-center py-6 px-4'):
        # Brand
        with ui.column().classes('gap-1'):
            with ui.row().classes('items-baseline gap-2'):
                ui.label('Forge').classes('text-2xl font-semibold text-white tracking-tight')
                ui.label(f'v{APP_VERSION}').classes('text-xs text-zinc-600')
            ui.label(f'Create images, video, and audio with AI — privately, on {platform_name}.').classes('text-sm text-zinc-500')
        
        # Status
        with ui.row().classes('items-center gap-3'):
            with ui.row().classes('items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800'):
                status_dot = ui.element('div').classes('w-2 h-2 rounded-full bg-zinc-600')
                status_label = ui.label('Checking...').classes('text-xs text-zinc-500')
            
            async def update_status():
                backend_ok, msg = check_backend()
                if backend_ok:
                    status_dot.classes(remove='bg-zinc-600 bg-red-500', add='bg-emerald-500')
                    status_label.set_text('Ready')
                    status_label.classes(remove='text-zinc-500 text-red-400', add='text-emerald-500')
                else:
                    status_dot.classes(remove='bg-zinc-600 bg-emerald-500', add='bg-red-500')
                    status_label.set_text('Offline')
                    status_label.classes(remove='text-zinc-500 text-emerald-500', add='text-red-400')
            
            ui.timer(0.1, update_status, once=True)
            ui.timer(10.0, update_status)
            
            ui.button(icon='help_outline', on_click=lambda: show_help()).props('flat round size=sm').classes('text-zinc-600 hover:text-zinc-400')

def show_help():
    """Show help dialog."""
    with ui.dialog() as dialog, ui.card().classes('p-6 max-w-md'):
        ui.label('🔥 Forge Help').classes('text-xl font-bold mb-4')
        ui.markdown('''
**Keyboard Shortcuts**
- `Cmd+Enter` - Generate image

**Tips**
- Click "🎲 Inspire me" for random prompts
- Click "✨ Enhance" to improve your prompt
- Click thumbnails in Recent to view past creations
- Copy seed to recreate exact images
        ''').classes('text-zinc-300')
        ui.button('Got it!', on_click=dialog.close).props('color=primary')
    dialog.open()

def model_recommendations_bar(media_type: str = "image"):
    """Show recommended models the user doesn't have yet, filtered by media type."""
    # Get installed model names
    installed = []
    for models in ALL_MODELS.values():
        installed.extend([m.name.lower() for m in models])
    
    # Get recommendations filtered by type
    all_recommendations = get_recommended_models(exclude_installed=installed)
    recommendations = [r for r in all_recommendations if r.type == media_type]
    
    if not recommendations:
        return  # Nothing to recommend for this type
    
    # Show subtle recommendations bar
    with ui.row().classes('w-full max-w-4xl mx-auto px-4 py-2 items-center gap-3'):
        type_labels = {'image': 'image', 'video': 'video', 'speech': 'voice', 'music': 'music'}
        ui.label(f'Suggested {type_labels.get(media_type, media_type)} models:').classes('text-xs text-zinc-600')
        
        for rec in recommendations[:3]:  # Show top 3
            with ui.link(target=rec.url, new_tab=True).classes('no-underline'):
                with ui.row().classes('items-center gap-1.5 px-2 py-1 rounded bg-zinc-900 border border-zinc-800 hover:border-cyan-600 hover:bg-zinc-800 transition-colors'):
                    ui.label(rec.name).classes('text-xs text-zinc-400')
                    ui.label(f'{rec.size_gb:.1f}GB').classes('text-xs text-zinc-600')
                    ui.icon('open_in_new', size='12px').classes('text-zinc-600')
        
        if len(recommendations) > 3:
            ui.label(f'+{len(recommendations) - 3} more').classes('text-xs text-zinc-600')

# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE GENERATION TAB
# ═══════════════════════════════════════════════════════════════════════════════

def image_generation_panel():
    """Image generation panel - v0.7 Output-Centric Layout."""
    models = [m for m in ALL_MODELS.get("image", []) if m.available_on_system()]

    if not models:
        with ui.column().classes('items-center justify-center py-12 gap-6 max-w-lg mx-auto'):
            ui.icon('image', size='64px').classes('text-zinc-600')
            ui.label('No image models found').classes('text-zinc-400 text-xl')
            ui.label('Download a model to start creating').classes('text-zinc-500 text-sm text-center')

            with ui.card().classes('w-full forge-card p-5 mt-2'):
                ui.label('QUICK START').classes('forge-section mb-4')

                with ui.column().classes('gap-3'):
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('bolt', size='24px').classes('text-amber-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('DreamShaper 8').classes('font-medium text-white')
                            ui.label('2GB • Fast & versatile • Great first model').classes('text-zinc-400 text-xs')
                        ui.link('Download', 'https://civitai.com/api/download/models/128713', new_tab=True).classes('text-indigo-400 text-sm')

                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('flash_on', size='24px').classes('text-yellow-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('SDXL Lightning').classes('font-medium text-white')
                            ui.label('6.5GB • 4 steps only • Ultra fast').classes('text-zinc-400 text-xs')
                        ui.link('Download', 'https://huggingface.co/ByteDance/SDXL-Lightning/resolve/main/sdxl_lightning_4step.safetensors', new_tab=True).classes('text-indigo-400 text-sm')

                ui.separator().classes('my-3')
                ui.label('Place downloaded .safetensors in:').classes('text-zinc-500 text-xs')
                ui.label('ComfyUI/models/checkpoints/').classes('text-zinc-400 text-xs font-mono bg-zinc-800 px-2 py-1 rounded')
        return

    # State
    state = {
        'model': models[0],
        'width': 1024,
        'height': 1024,
        'steps': 30,
        'cfg': 7,
        'seed': -1,
        'dim_preset': 0,
        'quality_preset': 1,
        'mode': 'generate',
        'selected_lora': None,
        'lora_strength': 0.8,
    }
    refs = {}

    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN LAYOUT - Output-Centric (v0.7)
    # ═══════════════════════════════════════════════════════════════════════════════

    with ui.column().classes('w-full gap-4'):

        # ─────────────────────────────────────────────────────────────────────
        # COMMAND BAR (Top) - Model + Prompt + Enhance + Create
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full forge-command-bar items-center gap-3'):
            # Model dropdown (compact)
            def on_model_select(m):
                state['model'] = m
                refs['model_btn'].text = m.name

            with ui.dropdown_button(models[0].name, auto_close=True).classes('shrink-0').props('no-caps dropdown-icon=expand_more color=dark dense') as refs['model_btn']:
                for m in models:
                    with ui.item(on_click=lambda m=m: on_model_select(m)).classes('forge-model-item'):
                        with ui.column().classes('gap-0.5 py-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(m.name).classes('text-white font-medium')
                                ui.badge(m.family).props('color=indigo outline dense')
                                ui.label(f'{m.size_gb:.1f}GB').classes('text-zinc-500 text-xs')
                            # Show description if available
                            if m.description:
                                ui.label(m.description).classes('text-zinc-400 text-xs max-w-xs')
                            else:
                                ui.label(f'{m.family.upper()} model').classes('text-zinc-500 text-xs')

            # Prompt input (expands to fill)
            refs['prompt'] = ui.input(placeholder='Describe what you want to create...').classes('flex-1 forge-command-prompt').props('dense outlined')

            # Inspiration button
            def set_random_prompt():
                import random
                prompt = random.choice(INSPIRATION_PROMPTS)
                refs['prompt'].value = prompt
                ui.notify('✨ Try this idea!', type='positive', position='top', timeout=1500)

            ui.button('🎲', on_click=set_random_prompt).props('flat dense').tooltip('Random inspiration')

            # Enhance button
            def do_enhance():
                original = refs['prompt'].value or ''
                if not original.strip():
                    ui.notify('Write something first!', type='warning')
                    return
                enhanced = enhance_prompt(original)
                refs['prompt'].value = enhanced
                ui.notify('✨ Prompt enhanced!', type='positive', position='top', timeout=1500)

            ui.button('✨', on_click=do_enhance).props('flat dense').classes('forge-enhance-btn').tooltip('Enhance prompt')

            # Create button (primary action)
            refs['gen_btn'] = ui.button('Create', on_click=lambda: do_generate()).props('no-caps').classes('forge-btn-primary')

        # ─────────────────────────────────────────────────────────────────────
        # HERO AREA (Center) - Image Display + Quick Actions
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-hero-area w-full'):
            # Image container
            with ui.element('div').classes('forge-image-container') as img_container:
                refs['placeholder_col'] = ui.column().classes('items-center gap-2')
                with refs['placeholder_col']:
                    ui.icon('image', size='48px').classes('text-zinc-600')
                    ui.label('Your creation will appear here').classes('text-zinc-500 text-sm')

                refs['output_img'] = ui.image().classes('hidden')

            # Quick actions bar
            with ui.row().classes('forge-quick-actions'):
                # Seed display
                refs['seed_display'] = ui.label('').classes('forge-seed-display hidden')

                async def copy_seed():
                    if 'last_seed' in state:
                        await ui.run_javascript(f'navigator.clipboard.writeText("{state["last_seed"]}")')
                        ui.notify(f'Seed {state["last_seed"]} copied!', type='positive', position='top', timeout=1500)

                refs['copy_seed_btn'] = ui.button('📋 Copy Seed', on_click=copy_seed).props('flat dense no-caps').classes('forge-quick-action-btn hidden')

                async def download_image():
                    if 'last_output' in state:
                        await ui.run_javascript(f'''
                            const a = document.createElement("a");
                            a.href = "{state["last_output"]}";
                            a.download = "forge_image.png";
                            a.click();
                        ''')
                        ui.notify('Downloading...', type='positive', position='top', timeout=1500)

                refs['download_btn'] = ui.button('⬇ Download', on_click=download_image).props('flat dense no-caps').classes('forge-quick-action-btn hidden')

                def use_for_variation():
                    if 'last_output' in state:
                        # Switch to variations mode and set source
                        set_mode('variations')
                        refs['variation_source_path'] = state['last_output']
                        refs['variation_source_preview'].set_source(state['last_output'])
                        refs['variation_source_preview'].classes(remove='hidden')
                        refs['variation_source_placeholder'].set_visibility(False)
                        ui.notify('Image loaded for variation', type='positive')

                refs['variation_btn'] = ui.button('🔄 Variation', on_click=use_for_variation).props('flat dense no-caps').classes('forge-quick-action-btn hidden')

                def use_for_upscale():
                    if 'last_output' in state:
                        set_mode('upscale')
                        refs['upscale_source_path'] = state['last_output']
                        refs['upscale_source_preview'].set_source(state['last_output'])
                        refs['upscale_source_preview'].classes(remove='hidden')
                        refs['upscale_source_placeholder'].set_visibility(False)
                        ui.notify('Image loaded for upscale', type='positive')

                refs['upscale_btn'] = ui.button('🔍 Upscale', on_click=use_for_upscale).props('flat dense no-caps').classes('forge-quick-action-btn hidden')

            # Progress bar (shown during generation)
            with ui.column().classes('w-full max-w-lg gap-1 mt-3'):
                refs['progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full forge-progress')
                refs['progress'].set_visibility(False)
                refs['progress_text'] = ui.label('').classes('forge-progress-text text-center w-full')
                refs['progress_text'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # HISTORY STRIP - Horizontal scroll of recent images
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-history-strip w-full'):
            with ui.row().classes('gap-2 items-center') as history_row:
                refs['gallery_container'] = history_row

                if generation_history:
                    update_image_gallery_v2(refs, state)
                else:
                    ui.label('Recent images will appear here').classes('text-zinc-600 text-xs px-2')

        # ─────────────────────────────────────────────────────────────────────
        # MODE TABS - Generate, Variations, Inpaint, Upscale
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full justify-center'):
            with ui.element('div').classes('forge-mode-tabs'):
                def set_mode(mode):
                    state['mode'] = mode
                    for m, btn in refs['mode_tab_buttons'].items():
                        if m == mode:
                            btn.classes(add='active')
                        else:
                            btn.classes(remove='active')
                    # Show/hide mode-specific sections
                    refs['variations_section'].set_visibility(mode == 'variations')
                    refs['inpaint_section'].set_visibility(mode == 'inpaint')
                    refs['upscale_section'].set_visibility(mode == 'upscale')

                refs['mode_tab_buttons'] = {}
                modes = [
                    ('generate', 'Generate'),
                    ('variations', 'Variations'),
                    ('inpaint', 'Inpaint'),
                    ('upscale', 'Upscale'),
                ]
                for mode_id, mode_label in modes:
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
                # Source upload
                with ui.column().classes('items-center gap-2'):
                    refs['variation_source'] = ui.element('div').classes('forge-source-upload')
                    with refs['variation_source']:
                        refs['variation_source_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['variation_source_placeholder'] = ui.column().classes('items-center')
                        with refs['variation_source_placeholder']:
                            ui.icon('add_photo_alternate', size='32px').classes('text-zinc-500')
                            ui.label('Upload').classes('text-zinc-500 text-xs')

                    refs['variation_upload'] = ui.upload(
                        on_upload=lambda e: handle_variation_upload(e),
                        auto_upload=True
                    ).props('accept=image/* flat dense').classes('hidden')
                    refs['variation_source'].on('click', lambda: refs['variation_upload'].run_method('pickFiles'))

                # Strength slider
                with ui.column().classes('gap-2 flex-1'):
                    ui.label('Variation Strength').classes('text-zinc-400 text-xs')
                    with ui.row().classes('items-center gap-3'):
                        refs['variation_strength'] = ui.slider(min=0.3, max=1.0, value=0.65, step=0.05).classes('flex-1')
                        refs['variation_strength_label'] = ui.label('0.65').classes('text-zinc-300 text-xs w-10')
                        refs['variation_strength'].on('update:model-value', lambda e: refs['variation_strength_label'].set_text(f'{e.args:.2f}'))
                    ui.label('Low = subtle changes, High = major changes').classes('text-zinc-500 text-xs')

        refs['variations_section'].set_visibility(False)

        # Inpaint mode inputs (placeholder)
        with ui.column().classes('w-full forge-mode-input-area') as inpaint_section:
            refs['inpaint_section'] = inpaint_section
            ui.label('INPAINT EDITOR').classes('forge-section-header mb-3')
            ui.label('Inpaint mode coming in Phase D').classes('text-zinc-500 text-sm')
        refs['inpaint_section'].set_visibility(False)

        # Upscale mode inputs (placeholder)
        with ui.column().classes('w-full forge-mode-input-area') as upscale_section:
            refs['upscale_section'] = upscale_section
            ui.label('UPSCALE').classes('forge-section-header mb-3')

            with ui.row().classes('items-start gap-6'):
                # Source upload
                with ui.column().classes('items-center gap-2'):
                    refs['upscale_source'] = ui.element('div').classes('forge-source-upload')
                    with refs['upscale_source']:
                        refs['upscale_source_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['upscale_source_placeholder'] = ui.column().classes('items-center')
                        with refs['upscale_source_placeholder']:
                            ui.icon('add_photo_alternate', size='32px').classes('text-zinc-500')
                            ui.label('Upload').classes('text-zinc-500 text-xs')

                    refs['upscale_upload'] = ui.upload(
                        on_upload=lambda e: handle_upscale_upload(e),
                        auto_upload=True
                    ).props('accept=image/* flat dense').classes('hidden')
                    refs['upscale_source'].on('click', lambda: refs['upscale_upload'].run_method('pickFiles'))

                # Scale options
                with ui.column().classes('gap-3'):
                    ui.label('Scale').classes('text-zinc-400 text-xs')
                    with ui.row().classes('gap-2'):
                        refs['scale_2x'] = ui.button('2×', on_click=lambda: select_scale(2)).props('dense no-caps color=primary')
                        refs['scale_4x'] = ui.button('4×', on_click=lambda: select_scale(4)).props('dense no-caps color=dark')

                    ui.label('Upscale mode coming in Phase C').classes('text-zinc-500 text-xs mt-2')

        refs['upscale_section'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # SETTINGS BAR (Bottom) - Compact presets
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
                    # Show custom inputs if Custom selected
                    refs['custom_size_row'].set_visibility(name == 'Custom')

                with ui.column().classes('forge-preset-options'):
                    for i, (name, w, h, hint) in enumerate(DIMENSION_PRESETS):
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 0 else '')) as opt:
                            opt.on('click', lambda i=i: select_size(i))
                            ui.element('div').classes('radio-dot')
                            # Show name with dimensions inline
                            with ui.row().classes('items-center gap-2'):
                                ui.label(name).classes('text-zinc-200')
                                ui.label(f'{w}×{h}').classes('text-zinc-500 text-xs')
                            opt.tooltip(hint)
                        refs['size_options'][i] = opt

                # Custom size inputs (hidden by default)
                with ui.row().classes('gap-2 items-center mt-2') as custom_row:
                    refs['custom_size_row'] = custom_row
                    refs['custom_width'] = ui.number(value=1024, min=256, max=2048, step=8).classes('w-20').props('dense outlined')
                    ui.label('×').classes('text-zinc-400')
                    refs['custom_height'] = ui.number(value=1024, min=256, max=2048, step=8).classes('w-20').props('dense outlined')

                    def apply_custom_size():
                        w = max(256, min(2048, (int(refs['custom_width'].value) // 8) * 8))
                        h = max(256, min(2048, (int(refs['custom_height'].value) // 8) * 8))
                        state['width'] = w
                        state['height'] = h
                        refs['custom_width'].value = w
                        refs['custom_height'].value = h

                    ui.button('Apply', on_click=apply_custom_size).props('dense no-caps size=sm')
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
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 1 else '')) as opt:  # Good is default
                            opt.on('click', lambda i=i: select_quality(i))
                            ui.element('div').classes('radio-dot')
                            ui.label(name).tooltip(f'{steps} steps, CFG {cfg} - {hint}')
                        refs['quality_options'][i] = opt

            ui.element('div').classes('flex-1')  # Spacer

            # Advanced settings toggle
            with ui.expansion('▾ Advanced Settings', value=False).classes('forge-advanced-toggle').props('dense'):
                with ui.row().classes('gap-6 p-3'):
                    with ui.column().classes('gap-2'):
                        ui.label('Seed').classes('text-zinc-400 text-xs')
                        refs['seed'] = ui.number(value=-1).classes('w-28').props('dense outlined')
                        ui.label('-1 = random').classes('text-zinc-500 text-xs')

                    with ui.column().classes('gap-2'):
                        ui.label('Steps').classes('text-zinc-400 text-xs')
                        with ui.row().classes('items-center gap-2'):
                            refs['steps_slider'] = ui.slider(min=10, max=60, value=30).classes('w-32')
                            refs['steps_input'] = ui.number(value=30, min=10, max=60, step=1).classes('w-16').props('dense outlined')

                            def sync_steps_from_slider(e):
                                val = int(e.args)
                                state['steps'] = val
                                refs['steps_input'].value = val

                            def sync_steps_from_input():
                                val = max(10, min(60, int(refs['steps_input'].value or 30)))
                                state['steps'] = val
                                refs['steps_slider'].value = val
                                refs['steps_input'].value = val

                            refs['steps_slider'].on('update:model-value', sync_steps_from_slider)
                            refs['steps_input'].on('blur', sync_steps_from_input)

                    with ui.column().classes('gap-2'):
                        ui.label('CFG').classes('text-zinc-400 text-xs')
                        with ui.row().classes('items-center gap-2'):
                            refs['cfg_slider'] = ui.slider(min=1, max=15, value=7, step=0.5).classes('w-32')
                            refs['cfg_input'] = ui.number(value=7, min=1, max=15, step=0.5).classes('w-16').props('dense outlined')

                            def sync_cfg_from_slider(e):
                                val = float(e.args)
                                state['cfg'] = val
                                refs['cfg_input'].value = val

                            def sync_cfg_from_input():
                                val = max(1, min(15, float(refs['cfg_input'].value or 7)))
                                state['cfg'] = val
                                refs['cfg_slider'].value = val
                                refs['cfg_input'].value = val

                            refs['cfg_slider'].on('update:model-value', sync_cfg_from_slider)
                            refs['cfg_input'].on('blur', sync_cfg_from_input)

                    # LoRA selector
                    if ALL_LORAS:
                        with ui.column().classes('gap-2 ml-6'):
                            ui.label('LoRA').classes('text-zinc-400 text-xs')
                            lora_options = {'None': None}
                            for lora in ALL_LORAS:
                                # Show name with compatibility hint
                                display = f"{lora.name[:25]}{'...' if len(lora.name) > 25 else ''} ({lora.compatible_with})"
                                lora_options[display] = lora.name
                            refs['lora_select'] = ui.select(
                                options=list(lora_options.keys()),
                                value='None',
                                on_change=lambda e: state.update({'selected_lora': lora_options.get(e.value)})
                            ).classes('w-48').props('dense outlined dark')
                            with ui.row().classes('items-center gap-2'):
                                ui.label('Strength').classes('text-zinc-500 text-xs')
                                refs['lora_strength'] = ui.slider(min=0, max=1, value=0.8, step=0.1).classes('w-24')
                                refs['lora_strength_input'] = ui.number(value=0.8, min=0, max=1, step=0.1).classes('w-16').props('dense outlined')

                                def sync_lora_from_slider(e):
                                    val = float(e.args)
                                    state['lora_strength'] = val
                                    refs['lora_strength_input'].value = val

                                def sync_lora_from_input():
                                    val = max(0, min(1, float(refs['lora_strength_input'].value or 0.8)))
                                    state['lora_strength'] = val
                                    refs['lora_strength'].value = val
                                    refs['lora_strength_input'].value = val

                                refs['lora_strength'].on('update:model-value', sync_lora_from_slider)
                                refs['lora_strength_input'].on('blur', sync_lora_from_input)

    # ═══════════════════════════════════════════════════════════════════════════════
    # HELPER FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════════

    async def handle_variation_upload(e):
        """Handle image upload for variations mode."""
        if e.content:
            import tempfile
            import os
            import base64
            ext = os.path.splitext(e.name)[1] or '.png'
            content = e.content.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(content)
                refs['variation_source_path'] = f.name

            refs['variation_source_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
            refs['variation_source_preview'].classes(remove='hidden')
            refs['variation_source_placeholder'].set_visibility(False)
            ui.notify('Source image loaded', type='positive')

    async def handle_upscale_upload(e):
        """Handle image upload for upscale mode."""
        if e.content:
            import tempfile
            import os
            import base64
            ext = os.path.splitext(e.name)[1] or '.png'
            content = e.content.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(content)
                refs['upscale_source_path'] = f.name

            refs['upscale_source_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
            refs['upscale_source_preview'].classes(remove='hidden')
            refs['upscale_source_placeholder'].set_visibility(False)
            ui.notify('Image loaded for upscale', type='positive')

    def select_scale(scale):
        """Select upscale factor."""
        state['upscale_factor'] = scale
        refs['scale_2x'].props('color=primary' if scale == 2 else 'color=dark')
        refs['scale_4x'].props('color=primary' if scale == 4 else 'color=dark')

    async def do_generate():
        """Generate image based on current mode and settings."""
        prompt = refs['prompt'].value
        if not prompt:
            ui.notify('Please describe what you want to create', type='warning')
            return

        refs['gen_btn'].disable()
        refs['gen_btn'].text = '⏳ Creating...'
        refs['progress'].set_visibility(True)
        refs['progress_text'].set_visibility(True)

        import time as time_module
        start_time = time_module.time()
        is_generating = True

        # Get current values
        steps = state['steps']
        cfg = state['cfg']
        seed = int(refs['seed'].value) if refs['seed'].value else -1

        # Timing estimate
        pixels = state['width'] * state['height']
        secs_per_step = 0.5 if pixels < 800000 else 1.0 if pixels < 1500000 else 1.5
        estimated_total = steps * secs_per_step + 5

        async def update_progress():
            nonlocal is_generating
            while is_generating:
                elapsed = time_module.time() - start_time
                progress = min(0.95, elapsed / estimated_total)
                remaining = estimated_total - elapsed

                refs['progress'].set_value(progress)
                if remaining > 0:
                    refs['progress_text'].set_text(f'⏳ {int(elapsed)}s elapsed • ~{int(remaining)}s remaining')
                else:
                    refs['progress_text'].set_text(f'⏳ Finalizing...')
                await asyncio.sleep(0.5)

        progress_task = asyncio.create_task(update_progress())

        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        state['last_seed'] = seed

        try:
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
                    lora_name=state.get('selected_lora'),
                    lora_strength=state.get('lora_strength', 0.8),
                )
            )

            is_generating = False
            elapsed = time_module.time() - start_time

            if output_path:
                state['last_output'] = output_path
                refs['placeholder_col'].set_visibility(False)
                refs['output_img'].classes(remove='hidden')
                refs['output_img'].set_source(output_path)
                refs['progress'].set_value(1.0)
                refs['progress_text'].set_text(f'✓ Complete in {int(elapsed)}s')

                # Show seed and quick actions
                refs['seed_display'].set_text(f'Seed: {seed}')
                refs['seed_display'].classes(remove='hidden')
                refs['copy_seed_btn'].classes(remove='hidden')
                refs['download_btn'].classes(remove='hidden')
                refs['variation_btn'].classes(remove='hidden')
                refs['upscale_btn'].classes(remove='hidden')

                ui.notify('Image created!', type='positive')
                add_to_history(output_path, prompt, state['model'].name, seed)
                update_image_gallery_v2(refs, state)
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


def update_image_gallery_v2(refs, state):
    """Update the horizontal history strip with recent images."""
    if 'gallery_container' not in refs:
        return
    refs['gallery_container'].clear()

    with refs['gallery_container']:
        for item in generation_history[:20]:  # Show up to 20 items
            def show_image(path=item['path'], prompt=item['prompt'], seed=item.get('seed', 0)):
                refs['output_img'].set_source(path)
                refs['output_img'].classes(remove='hidden')
                refs['placeholder_col'].set_visibility(False)
                state['last_output'] = path
                state['last_seed'] = seed
                refs['seed_display'].set_text(f'Seed: {seed}')
                refs['seed_display'].classes(remove='hidden')
                refs['copy_seed_btn'].classes(remove='hidden')
                refs['download_btn'].classes(remove='hidden')
                refs['variation_btn'].classes(remove='hidden')
                refs['upscale_btn'].classes(remove='hidden')
                ui.notify(f'"{prompt[:40]}..."' if len(prompt) > 40 else f'"{prompt}"', position='top', timeout=2000)

            with ui.element('div').classes('forge-history-item-img').on('click', show_image):
                ui.image(item['path']).classes('w-full h-full object-cover')


def video_generation_panel():
    """Video generation panel with LTX-Video support - v0.7 Output-Centric Layout."""
    video_models = [m for m in ALL_MODELS.get('video', []) if m.available_on_system()]
    if not video_models:
        with ui.column().classes('items-center justify-center py-12 gap-6 max-w-lg mx-auto'):
            ui.icon('movie', size='64px').classes('text-zinc-600')
            ui.label('No video models found').classes('text-zinc-400 text-xl')
            ui.label('Download a model to start creating videos').classes('text-zinc-500 text-sm text-center')

            with ui.card().classes('w-full forge-card p-5 mt-2'):
                ui.label('QUICK START').classes('forge-section mb-4')

                with ui.column().classes('gap-3'):
                    # LTX-Video - recommended for Mac
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('star', size='24px').classes('text-amber-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('LTX-Video 0.9.1 (Recommended)').classes('font-medium text-white')
                            ui.label('5GB • Works great on Mac • Fast generation').classes('text-zinc-400 text-xs')
                        ui.link('Download', 'https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.1.safetensors', new_tab=True).classes('text-indigo-400 text-sm')

                    # LTX Distilled - even faster
                    with ui.row().classes('items-center gap-3 p-3 rounded-lg bg-zinc-800/50'):
                        ui.icon('bolt', size='24px').classes('text-yellow-400')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label('LTX-Video Distilled (Fastest)').classes('font-medium text-white')
                            ui.label('5GB • 8 steps only • Quick iterations').classes('text-zinc-400 text-xs')
                        ui.link('Download', 'https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltxv-2b-0.9.8-distilled.safetensors', new_tab=True).classes('text-indigo-400 text-sm')

                ui.separator().classes('my-3')
                ui.label('Place downloaded .safetensors in:').classes('text-zinc-500 text-xs')
                ui.label('ComfyUI/models/checkpoints/').classes('text-zinc-400 text-xs font-mono bg-zinc-800 px-2 py-1 rounded')

                with ui.row().classes('mt-3 gap-2 items-center'):
                    ui.icon('info', size='16px').classes('text-zinc-500')
                    ui.label('Wan models not yet supported on Mac').classes('text-zinc-500 text-xs')
        return

    # State
    state = {
        'model': video_models[0],
        'width': 512, 'height': 320,
        'num_frames': 25,
        'steps': 30, 'cfg': 3.5,
        'size_preset': 0,
        'duration_preset': 0,
        'quality_preset': 1,
        'mode': 't2v',
        'loop_enabled': True,
    }
    refs = {}

    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN LAYOUT - Output-Centric (v0.7)
    # ═══════════════════════════════════════════════════════════════════════════════

    with ui.column().classes('w-full gap-4'):

        # ─────────────────────────────────────────────────────────────────────
        # COMMAND BAR (Top) - Model + Prompt + Enhance + Generate
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full forge-command-bar items-center gap-3'):
            # Model dropdown (compact)
            def on_video_model_select(m):
                state['model'] = m
                refs['video_model_btn'].text = m.name

            with ui.dropdown_button(video_models[0].name, auto_close=True).classes('shrink-0').props('no-caps dropdown-icon=expand_more color=dark dense') as refs['video_model_btn']:
                for m in video_models:
                    with ui.item(on_click=lambda m=m: on_video_model_select(m)).classes('forge-model-item'):
                        with ui.column().classes('gap-0.5 py-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(m.name).classes('text-white font-medium')
                                ui.badge(m.family).props('color=indigo outline dense')
                                ui.label(f'{m.size_gb:.1f}GB').classes('text-zinc-500 text-xs')
                            # Show description if available
                            if m.description:
                                ui.label(m.description).classes('text-zinc-400 text-xs max-w-xs')
                            else:
                                ui.label(f'{m.family.upper()} video model').classes('text-zinc-500 text-xs')

            # Prompt input (expands to fill)
            refs['prompt'] = ui.input(placeholder='Describe the video you want to create...').classes('flex-1 forge-command-prompt').props('dense outlined')

            # Enhance button
            def do_enhance_video():
                original = refs['prompt'].value or ''
                if not original.strip():
                    ui.notify('Write something first!', type='warning')
                    return
                enhanced = enhance_prompt(original, style="cinematic")
                refs['prompt'].value = enhanced
                ui.notify('✨ Prompt enhanced!', type='positive', position='top', timeout=1500)

            ui.button('✨', on_click=do_enhance_video).props('flat dense').classes('forge-enhance-btn').tooltip('Enhance prompt')

            # Generate button (primary action)
            refs['video_gen_btn'] = ui.button('Create', on_click=lambda: do_generate_video()).props('no-caps').classes('forge-btn-primary')

        # ─────────────────────────────────────────────────────────────────────
        # HERO AREA (Center) - Video Player + Transport Controls
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-hero-area w-full'):
            # Video container
            with ui.element('div').classes('forge-video-container') as video_container:
                refs['video_placeholder'] = ui.column().classes('w-full h-full items-center justify-center')
                with refs['video_placeholder']:
                    ui.icon('movie', size='48px').classes('text-zinc-600')
                    ui.label('Your video will appear here').classes('text-zinc-500 text-sm mt-2')

                refs['output_video'] = ui.video('').classes('w-full h-full object-contain hidden').props('loop')

            # Transport controls
            with ui.row().classes('forge-transport items-center'):
                # Playback controls
                async def video_play_pause():
                    await ui.run_javascript('''
                        const video = document.querySelector('.forge-video-container video');
                        if (video) { video.paused ? video.play() : video.pause(); }
                    ''')

                async def video_restart():
                    await ui.run_javascript('''
                        const video = document.querySelector('.forge-video-container video');
                        if (video) { video.currentTime = 0; video.play(); }
                    ''')

                ui.button(icon='replay', on_click=video_restart).props('flat dense').classes('forge-transport-btn').tooltip('Restart')
                ui.button(icon='play_arrow', on_click=video_play_pause).props('flat dense').classes('forge-transport-btn').tooltip('Play/Pause')

                # Loop toggle
                def toggle_loop():
                    state['loop_enabled'] = not state['loop_enabled']
                    refs['loop_btn'].classes(add='active' if state['loop_enabled'] else '', remove='active' if not state['loop_enabled'] else '')
                    ui.run_javascript(f'''
                        const video = document.querySelector('.forge-video-container video');
                        if (video) {{ video.loop = {str(state['loop_enabled']).lower()}; }}
                    ''')

                refs['loop_btn'] = ui.button(icon='loop', on_click=toggle_loop).props('flat dense').classes('forge-transport-btn active').tooltip('Loop')

                # Download
                async def download_video():
                    if 'last_output' in state:
                        await ui.run_javascript(f'''
                            const a = document.createElement("a");
                            a.href = "{state["last_output"]}";
                            a.download = "forge_video.mp4";
                            a.click();
                        ''')
                        ui.notify('Downloading...', type='positive', position='top', timeout=1500)

                ui.button(icon='download', on_click=download_video).props('flat dense').classes('forge-transport-btn').tooltip('Download')

                ui.element('div').classes('flex-1')  # Spacer

                # Seed display
                refs['seed_display'] = ui.label('').classes('forge-seed-display hidden')

                async def copy_video_seed():
                    if 'last_seed' in state:
                        await ui.run_javascript(f'navigator.clipboard.writeText("{state["last_seed"]}")')
                        ui.notify(f'Seed {state["last_seed"]} copied!', type='positive', position='top', timeout=1500)

                refs['copy_seed_btn'] = ui.button(icon='content_copy', on_click=copy_video_seed).props('flat dense').classes('forge-transport-btn hidden').tooltip('Copy seed')

                # Duration display
                refs['duration_display'] = ui.label('').classes('text-zinc-500 text-xs ml-2')

            # Progress bar (shown during generation)
            with ui.column().classes('w-full max-w-lg gap-1 mt-3'):
                refs['video_progress'] = ui.linear_progress(value=0, show_value=False).classes('w-full forge-progress')
                refs['video_progress'].set_visibility(False)
                refs['video_progress_text'] = ui.label('').classes('forge-progress-text text-center w-full')
                refs['video_progress_text'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # HISTORY STRIP - Horizontal scroll of recent videos
        # ─────────────────────────────────────────────────────────────────────
        with ui.element('div').classes('forge-history-strip w-full'):
            with ui.row().classes('gap-2 items-center') as history_row:
                refs['video_gallery_container'] = history_row

                if video_generation_history:
                    update_video_gallery_v2(refs, state)
                else:
                    ui.label('Recent videos will appear here').classes('text-zinc-600 text-xs px-2')

        # ─────────────────────────────────────────────────────────────────────
        # MODE TABS - T2V, I2V, V2V, Extend
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full justify-center'):
            with ui.element('div').classes('forge-mode-tabs'):
                def set_mode(mode):
                    state['mode'] = mode
                    # Update tab styling
                    for m, btn in refs['mode_tab_buttons'].items():
                        if m == mode:
                            btn.classes(add='active')
                        else:
                            btn.classes(remove='active')
                    # Show/hide mode-specific inputs
                    refs['i2v_section'].set_visibility(mode == 'i2v')
                    refs['v2v_section'].set_visibility(mode == 'v2v')
                    refs['extend_section'].set_visibility(mode == 'extend')

                refs['mode_tab_buttons'] = {}
                modes = [
                    ('t2v', 'Text→Video'),
                    ('i2v', 'Image→Video'),
                    ('v2v', 'Video→Video'),
                    ('extend', 'Extend'),
                ]
                for mode_id, mode_label in modes:
                    btn = ui.button(mode_label, on_click=lambda m=mode_id: set_mode(m)).props('flat no-caps')
                    btn.classes('forge-mode-tab' + (' active' if mode_id == 't2v' else ''))
                    refs['mode_tab_buttons'][mode_id] = btn

        # ─────────────────────────────────────────────────────────────────────
        # MODE-SPECIFIC INPUT AREAS
        # ─────────────────────────────────────────────────────────────────────

        # Image-to-Video inputs
        with ui.column().classes('w-full forge-mode-input-area') as i2v_section:
            refs['i2v_section'] = i2v_section
            ui.label('GUIDE FRAMES').classes('forge-section-header mb-3')

            with ui.row().classes('forge-guide-frames'):
                # First frame upload
                with ui.column().classes('items-center gap-1'):
                    refs['i2v_first_frame'] = ui.element('div').classes('forge-frame-upload')
                    with refs['i2v_first_frame']:
                        refs['i2v_first_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['i2v_first_placeholder'] = ui.column().classes('items-center')
                        with refs['i2v_first_placeholder']:
                            ui.icon('add_photo_alternate', size='24px').classes('text-zinc-500')
                            ui.label('First').classes('text-zinc-500 text-xs')

                    refs['i2v_first_upload'] = ui.upload(
                        on_upload=lambda e: handle_frame_upload(e, 'first'),
                        auto_upload=True
                    ).props('accept=image/* flat dense').classes('hidden')
                    refs['i2v_first_frame'].on('click', lambda: refs['i2v_first_upload'].run_method('pickFiles'))
                    ui.label('First Frame').classes('text-zinc-500 text-xs')

                ui.icon('arrow_forward', size='24px').classes('text-zinc-600')

                # Last frame upload (optional)
                with ui.column().classes('items-center gap-1'):
                    refs['i2v_last_frame'] = ui.element('div').classes('forge-frame-upload')
                    with refs['i2v_last_frame']:
                        refs['i2v_last_preview'] = ui.image().classes('w-full h-full object-cover hidden')
                        refs['i2v_last_placeholder'] = ui.column().classes('items-center')
                        with refs['i2v_last_placeholder']:
                            ui.icon('add_photo_alternate', size='24px').classes('text-zinc-500')
                            ui.label('Last').classes('text-zinc-500 text-xs')

                    refs['i2v_last_upload'] = ui.upload(
                        on_upload=lambda e: handle_frame_upload(e, 'last'),
                        auto_upload=True
                    ).props('accept=image/* flat dense').classes('hidden')
                    refs['i2v_last_frame'].on('click', lambda: refs['i2v_last_upload'].run_method('pickFiles'))
                    ui.label('Last Frame (opt)').classes('text-zinc-500 text-xs')

                ui.element('div').classes('flex-1')  # Spacer

                # Strength slider
                with ui.column().classes('gap-1'):
                    ui.label('Strength').classes('text-zinc-400 text-xs')
                    with ui.row().classes('items-center gap-2'):
                        refs['i2v_strength'] = ui.slider(min=0.5, max=1.0, value=0.85, step=0.05).classes('w-32')
                        refs['i2v_strength_input'] = ui.number(value=0.85, min=0.5, max=1.0, step=0.05).classes('w-16').props('dense outlined')

                        def sync_i2v_from_slider(e):
                            val = float(e.args)
                            refs['i2v_strength_input'].value = val

                        def sync_i2v_from_input():
                            val = max(0.5, min(1.0, float(refs['i2v_strength_input'].value or 0.85)))
                            refs['i2v_strength'].value = val
                            refs['i2v_strength_input'].value = val

                        refs['i2v_strength'].on('update:model-value', sync_i2v_from_slider)
                        refs['i2v_strength_input'].on('blur', sync_i2v_from_input)

        refs['i2v_section'].set_visibility(False)

        # Video-to-Video inputs (placeholder for Phase 3c)
        with ui.column().classes('w-full forge-mode-input-area') as v2v_section:
            refs['v2v_section'] = v2v_section
            ui.label('SOURCE VIDEO').classes('forge-section-header mb-3')
            ui.label('Video-to-Video coming in Phase 3c').classes('text-zinc-500 text-sm')
        refs['v2v_section'].set_visibility(False)

        # Extend inputs (placeholder for Phase 3d)
        with ui.column().classes('w-full forge-mode-input-area') as extend_section:
            refs['extend_section'] = extend_section
            ui.label('EXTEND VIDEO').classes('forge-section-header mb-3')
            ui.label('Video extension coming in Phase 3d').classes('text-zinc-500 text-sm')
        refs['extend_section'].set_visibility(False)

        # ─────────────────────────────────────────────────────────────────────
        # SETTINGS BAR (Bottom) - Compact presets
        # ─────────────────────────────────────────────────────────────────────
        with ui.row().classes('w-full forge-settings-bar gap-8'):
            # SIZE presets
            with ui.column().classes('forge-preset-group'):
                ui.label('SIZE').classes('forge-preset-label')
                refs['size_options'] = {}

                def select_size(idx):
                    state['size_preset'] = idx
                    name, w, h, _ = VIDEO_SIZE_PRESETS[idx]
                    state['width'] = w
                    state['height'] = h
                    for i, opt in refs['size_options'].items():
                        if i == idx:
                            opt.classes(add='selected')
                        else:
                            opt.classes(remove='selected')

                with ui.column().classes('forge-preset-options'):
                    for i, (name, w, h, hint) in enumerate(VIDEO_SIZE_PRESETS):
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 0 else '')) as opt:
                            opt.on('click', lambda i=i: select_size(i))
                            ui.element('div').classes('radio-dot')
                            # Show name with dimensions inline
                            with ui.row().classes('items-center gap-2'):
                                ui.label(name).classes('text-zinc-200')
                                ui.label(f'{w}×{h}').classes('text-zinc-500 text-xs')
                            opt.tooltip(hint)
                        refs['size_options'][i] = opt

            # DURATION presets
            with ui.column().classes('forge-preset-group'):
                ui.label('DURATION').classes('forge-preset-label')
                refs['duration_options'] = {}

                def select_duration(idx):
                    state['duration_preset'] = idx
                    _, frames, _ = VIDEO_DURATION_PRESETS[idx]
                    state['num_frames'] = frames
                    for i, opt in refs['duration_options'].items():
                        if i == idx:
                            opt.classes(add='selected')
                        else:
                            opt.classes(remove='selected')

                with ui.column().classes('forge-preset-options'):
                    for i, (name, frames, hint) in enumerate(VIDEO_DURATION_PRESETS):
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 0 else '')) as opt:
                            opt.on('click', lambda i=i: select_duration(i))
                            ui.element('div').classes('radio-dot')
                            ui.label(name).tooltip(f'{frames} frames - {hint}')
                        refs['duration_options'][i] = opt

            # QUALITY presets
            with ui.column().classes('forge-preset-group'):
                ui.label('QUALITY').classes('forge-preset-label')
                refs['quality_options'] = {}

                def select_quality(idx):
                    state['quality_preset'] = idx
                    _, steps, cfg, _ = VIDEO_QUALITY_PRESETS[idx]
                    state['steps'] = steps
                    state['cfg'] = cfg
                    for i, opt in refs['quality_options'].items():
                        if i == idx:
                            opt.classes(add='selected')
                        else:
                            opt.classes(remove='selected')

                with ui.column().classes('forge-preset-options'):
                    for i, (name, steps, cfg, hint) in enumerate(VIDEO_QUALITY_PRESETS):
                        with ui.element('div').classes('forge-radio-option' + (' selected' if i == 1 else '')) as opt:  # Good is default
                            opt.on('click', lambda i=i: select_quality(i))
                            ui.element('div').classes('radio-dot')
                            ui.label(name).tooltip(f'{steps} steps, CFG {cfg} - {hint}')
                        refs['quality_options'][i] = opt

            ui.element('div').classes('flex-1')  # Spacer

            # Advanced settings toggle
            with ui.expansion('▾ Advanced Settings', value=False).classes('forge-advanced-toggle').props('dense'):
                with ui.row().classes('gap-6 p-3'):
                    with ui.column().classes('gap-2'):
                        ui.label('Seed').classes('text-zinc-400 text-xs')
                        refs['video_seed'] = ui.number(value=-1).classes('w-28').props('dense outlined')
                        ui.label('-1 = random').classes('text-zinc-500 text-xs')

                    with ui.column().classes('gap-2 flex-1'):
                        ui.label('Negative prompt').classes('text-zinc-400 text-xs')
                        refs['negative_prompt'] = ui.input(placeholder='blur, distortion, artifacts...').classes('w-full').props('dense outlined')

    # ═══════════════════════════════════════════════════════════════════════════════
    # HELPER FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════════

    async def handle_frame_upload(e, frame_type):
        """Handle image upload for I2V mode."""
        if e.content:
            import tempfile
            import os
            import base64
            ext = os.path.splitext(e.name)[1] or '.png'
            content = e.content.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(content)
                if frame_type == 'first':
                    refs['i2v_image_path'] = f.name
                    refs['i2v_first_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
                    refs['i2v_first_preview'].classes(remove='hidden')
                    refs['i2v_first_placeholder'].set_visibility(False)
                else:
                    refs['i2v_last_image_path'] = f.name
                    refs['i2v_last_preview'].set_source(f'data:image/png;base64,{base64.b64encode(content).decode()}')
                    refs['i2v_last_preview'].classes(remove='hidden')
                    refs['i2v_last_placeholder'].set_visibility(False)

            ui.notify(f'{frame_type.title()} frame loaded', type='positive')

    async def do_generate_video():
        """Generate video based on current mode and settings."""
        prompt = refs['prompt'].value
        if not prompt:
            ui.notify('Please describe what you want to create', type='warning')
            return

        refs['video_gen_btn'].disable()
        refs['video_gen_btn'].text = '⏳ Creating...'
        refs['video_progress'].set_visibility(True)
        refs['video_progress_text'].set_visibility(True)

        import time as time_module
        start_time = time_module.time()
        is_generating = True

        # Timing estimates
        pixels = state['width'] * state['height'] * state['num_frames']
        if pixels < 5_000_000:
            secs_per_step = 2.5
        elif pixels < 15_000_000:
            secs_per_step = 4.0
        else:
            secs_per_step = 6.0

        estimated_total_secs = state['steps'] * secs_per_step + 30

        async def update_progress():
            nonlocal is_generating
            while is_generating:
                elapsed = time_module.time() - start_time
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                progress = min(0.95, elapsed / estimated_total_secs)
                remaining = max(0, estimated_total_secs - elapsed)
                rem_mins = int(remaining // 60)
                rem_secs = int(remaining % 60)

                refs['video_progress'].set_value(progress)
                if remaining > 0:
                    refs['video_progress_text'].set_text(f'⏳ {mins}:{secs:02d} elapsed • ~{rem_mins}:{rem_secs:02d} remaining')
                else:
                    refs['video_progress_text'].set_text(f'⏳ {mins}:{secs:02d} elapsed • finalizing...')
                await asyncio.sleep(0.5)

        progress_task = asyncio.create_task(update_progress())

        seed = int(refs['video_seed'].value) if refs['video_seed'].value else -1
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        state['last_seed'] = seed

        try:
            if state['mode'] == 'i2v':
                if not refs.get('i2v_image_path'):
                    raise ValueError("Please upload a first frame image")

                output_path, status_msg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: generate_video_from_image(
                        prompt_text=prompt,
                        image_path=refs['i2v_image_path'],
                        model_name=state['model'].name,
                        width=state['width'],
                        height=state['height'],
                        num_frames=state['num_frames'],
                        steps=state['steps'],
                        cfg=state['cfg'],
                        seed=seed,
                        strength=refs['i2v_strength'].value,
                    )
                )
            else:
                # Text-to-Video (default)
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
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)

            if output_path:
                state['last_output'] = output_path
                refs['video_placeholder'].set_visibility(False)
                refs['output_video'].classes(remove='hidden')
                refs['output_video'].set_source(output_path)
                refs['video_progress'].set_value(1.0)
                refs['video_progress_text'].set_text(f'✓ Complete in {mins}:{secs:02d}')

                # Show seed
                refs['seed_display'].set_text(f'Seed: {seed}')
                refs['seed_display'].classes(remove='hidden')
                refs['copy_seed_btn'].classes(remove='hidden')

                ui.notify('Video created!', type='positive')
                add_video_to_history(output_path, prompt, state['model'].name, seed)
                update_video_gallery_v2(refs, state)
            else:
                refs['video_progress_text'].set_text(f'✗ {status_msg}')
                ui.notify(status_msg, type='negative')
        except Exception as e:
            is_generating = False
            refs['video_progress_text'].set_text(f'✗ Error: {str(e)}')
            ui.notify(str(e), type='negative')
        finally:
            is_generating = False
            progress_task.cancel()
            refs['video_gen_btn'].enable()
            refs['video_gen_btn'].text = 'Create'
            await asyncio.sleep(3)
            refs['video_progress'].set_visibility(False)


def update_video_gallery_v2(refs, state):
    """Update the horizontal history strip with recent videos."""
    if 'video_gallery_container' not in refs:
        return
    refs['video_gallery_container'].clear()

    with refs['video_gallery_container']:
        for item in video_generation_history[:12]:  # Show up to 12 items
            def show_video(path=item['path'], prompt=item['prompt'], seed=item['seed']):
                refs['output_video'].set_source(path)
                refs['output_video'].classes(remove='hidden')
                refs['video_placeholder'].set_visibility(False)
                state['last_output'] = path
                state['last_seed'] = seed
                refs['seed_display'].set_text(f'Seed: {seed}')
                refs['seed_display'].classes(remove='hidden')
                refs['copy_seed_btn'].classes(remove='hidden')
                ui.notify(f'"{prompt[:40]}..."' if len(prompt) > 40 else f'"{prompt}"', position='top', timeout=2000)

            with ui.element('div').classes('forge-history-item').on('click', show_video):
                ui.icon('play_circle').classes('play-icon')
            # TODO: Generate actual video thumbnails


def voice_generation_panel():
    """Voice/speech generation panel."""
    voice_models = ALL_MODELS.get('speech', [])
    
    # Show helpful info even without models
    with ui.column().classes('items-center justify-center py-12 gap-4 max-w-lg mx-auto'):
        ui.icon('mic', size='64px').classes('text-zinc-600')
        
        if voice_models:
            ui.label('Voice Generation').classes('text-zinc-300 text-lg')
            ui.label('Text-to-speech with voice cloning').classes('text-zinc-500 text-sm')
            # TODO: Add actual voice generation UI
            ui.label('Coming soon...').classes('text-zinc-500 mt-4')
        else:
            ui.label('No voice models found').classes('text-zinc-400 text-lg')
            ui.label('Add speech models to clone voices and generate speech').classes('text-zinc-500 text-sm text-center')
            
            with ui.card().classes('w-full forge-card p-4 mt-4'):
                ui.label('RECOMMENDED MODELS').classes('forge-section mb-3')
                with ui.column().classes('gap-2'):
                    ui.markdown('''
| Model | Size | Best For |
|-------|------|----------|
| **Chatterbox TTS** | 2GB | Voice cloning, emotional speech |
| **XTTS v2** | 1.5GB | Multi-language, fast |
| **Bark** | 5GB | Sound effects + speech |
| **WhisperSpeech** | 1GB | Clean, natural voice |
                    ''').classes('text-sm')
                
                ui.link('📥 Chatterbox on HuggingFace', 'https://huggingface.co/ResembleAI/chatterbox', new_tab=True).classes('mt-3 text-indigo-400')
                ui.link('📥 XTTS on HuggingFace', 'https://huggingface.co/coqui/XTTS-v2', new_tab=True).classes('text-indigo-400')
                ui.label('Voice models require ComfyUI audio nodes').classes('text-zinc-500 text-xs mt-2')


def music_generation_panel():
    """Music generation panel."""
    music_models = ALL_MODELS.get('music', [])
    
    with ui.column().classes('items-center justify-center py-12 gap-4 max-w-lg mx-auto'):
        ui.icon('music_note', size='64px').classes('text-zinc-600')
        
        if music_models:
            ui.label('Music Generation').classes('text-zinc-300 text-lg')
            ui.label('Create background music and soundtracks').classes('text-zinc-500 text-sm')
            # TODO: Add actual music generation UI
            ui.label('Coming soon...').classes('text-zinc-500 mt-4')
        else:
            ui.label('No music models found').classes('text-zinc-400 text-lg')
            ui.label('Add music models to generate soundtracks and audio').classes('text-zinc-500 text-sm text-center')
            
            with ui.card().classes('w-full forge-card p-4 mt-4'):
                ui.label('RECOMMENDED MODELS').classes('forge-section mb-3')
                with ui.column().classes('gap-2'):
                    ui.markdown('''
| Model | Size | Best For |
|-------|------|----------|
| **MusicGen Small** | 1.5GB | Quick background music |
| **MusicGen Large** | 3.5GB | Higher quality compositions |
| **Stable Audio** | 2GB | Sound effects + music |
| **AudioCraft** | 4GB | Meta's full audio suite |
                    ''').classes('text-sm')
                
                ui.link('📥 MusicGen on HuggingFace', 'https://huggingface.co/facebook/musicgen-small', new_tab=True).classes('mt-3 text-indigo-400')
                ui.link('📥 Stable Audio', 'https://huggingface.co/stabilityai/stable-audio-open-1.0', new_tab=True).classes('text-indigo-400')
                ui.label('Music models require ComfyUI audio nodes').classes('text-zinc-500 text-xs mt-2')


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════

@ui.page('/')
def main_page():
    """Main application page with smart onboarding."""
    setup_theme()
    
    app_state = get_app_state()
    
    with ui.column().classes('w-full min-h-screen bg-zinc-950'):
        
        if app_state == "no_models":
            welcome_no_models()
            
        elif app_state == "no_backend":
            welcome_no_backend()
            
        else:
            # Normal operation
            app_header()
            
            # Tab navigation
            with ui.column().classes('w-full max-w-4xl mx-auto px-4'):
                with ui.tabs().classes('w-full') as tabs:
                    image_tab = ui.tab('🖼️ Images')
                    video_tab = ui.tab('🎬 Video')
                    # Coming in future release:
                    # voice_tab = ui.tab('🎤 Voice')
                    # music_tab = ui.tab('🎵 Music')

                with ui.tab_panels(tabs, value=image_tab).classes('w-full mt-4'):
                    with ui.tab_panel(image_tab):
                        model_recommendations_bar("image")
                        image_generation_panel()

                    with ui.tab_panel(video_tab):
                        model_recommendations_bar("video")
                        video_generation_panel()

                    # Coming in future release:
                    # with ui.tab_panel(voice_tab):
                    #     model_recommendations_bar("speech")
                    #     voice_generation_panel()
                    #
                    # with ui.tab_panel(music_tab):
                    #     model_recommendations_bar("music")
                    #     music_generation_panel()

# ═══════════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ in {"__main__", "__mp_main__"}:
    print(f"🔥 Starting Forge v{APP_VERSION}")
    print(f"   System: {SYSTEM.machine} / {SYSTEM.chip} / {SYSTEM.ram_gb}GB")
    
    init_models()
    
    ui.run(
        title=f'🔥 Forge',
        port=7861,
        reload=False,
        show=False,
    )
