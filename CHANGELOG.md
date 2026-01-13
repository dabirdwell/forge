# Changelog

All notable changes to Forge will be documented in this file.

## [1.0.0] - 2026-01-13

### Added
- **Image Editing Mode** — Three modes in Image tab: Create, Edit, Upscale
  - **Create** — Generate new images from text prompts (existing functionality)
  - **Edit (img2img)** — Transform existing images guided by prompts
    - Upload any image as input
    - Transformation strength presets: Subtle (30%), Moderate (50%), Strong (70%), Creative (90%)
    - Works with all image models (SDXL, SD1.5, Lightning, Turbo)
  - **Upscale** — Enhance image resolution using AI upscalers
    - 5 upscaler models: UltraSharp, AnimeSharp, ESRGAN, RealESRGAN, RealESRGAN Anime
    - 4x resolution increase
- **Mode-specific UI** — Interface adapts based on selected mode
  - Input image upload appears for Edit/Upscale modes
  - Transformation strength selector for Edit mode
  - Upscaler model selector for Upscale mode

### Changed
- Image tab now has mode selector buttons at top (Create/Edit/Upscale)
- Generate button text changes based on mode
- All output added to gallery regardless of mode

### Technical
- Added `generate_img2img()` for image-to-image transformation
- Added `generate_inpaint()` for masked region editing (foundation for future)
- Added `upscale_image()` for resolution enhancement
- Added workflow builders for each editing operation
- Added `IMG2IMG_STRENGTH_PRESETS` and `UPSCALER_MODELS` constants
- Image panel state now tracks mode, input image, denoise strength, upscaler selection

## [0.9.0] - 2026-01-13

### Added
- **BYOM Music Generation** — Bring Your Own music models, completing the BYOM suite
  - Model selector dropdown showing all discovered music models
  - Support for MusicGen, Stable Audio, AudioCraft, Riffusion, AudioLDM/2
  - All music models route through ComfyUI workflows
- **Music Generation Features**
  - Duration presets: Short (5s), Medium (15s), Standard (30s), Long (60s)
  - Style tags: ambient, electronic, acoustic, orchestral, lofi, rock, jazz, classical
  - Melody conditioning: Upload audio to guide generation (MusicGen, AudioCraft)
- **Music Model Discovery** — Automatically finds music models in ComfyUI paths
  - Family detection for all supported music model architectures
  - Memory requirements estimated per model family

### Changed
- Music tab now fully functional (was placeholder)
- All four tabs (Image, Video, Voice, Music) now have consistent BYOM architecture

### Technical
- Added music model families to `MEMORY_MULTIPLIERS` and `FAMILY_FALLBACKS`
- Added `generate_music()` function for music generation routing
- Added workflow builders for each music model family
- Added `MUSIC_DURATION_PRESETS` and `MUSIC_STYLE_TAGS` constants

## [0.8.0] - 2026-01-13

### Added
- **BYOM Voice Models** — Bring Your Own TTS models, consistent with Image/Video tabs
  - Model selector dropdown in Voice tab shows all discovered TTS models
  - Backend badges: "Built-in" (green) for direct mode, "ComfyUI" (blue) for workflow mode
  - Support for XTTS, F5-TTS, Bark, TorToise, StyleTTS2 through ComfyUI
  - Built-in Chatterbox TTS always available as fallback (no setup required)
- **Dual Backend Routing** — Models route through appropriate backend automatically
  - Direct mode: Chatterbox loads from HuggingFace, runs standalone
  - ComfyUI mode: Other TTS models run through ComfyUI workflows
- **TTS Model Discovery** — Automatically finds TTS models in ComfyUI model paths
  - Family detection for XTTS, F5-TTS, Bark, TorToise, StyleTTS2
  - Memory requirements estimated per model family

### Changed
- Voice tab now shows model selector (like Image/Video tabs)
- Mode selector and expression tags only visible for Chatterbox
- Generation routes based on selected model's `backend_mode`

### Technical
- Added `backend_mode` field to Model dataclass ("comfyui" or "direct")
- Added `generate_speech_comfyui()` for routing TTS through ComfyUI
- Added workflow builders for each TTS model family
- Added `poll_comfyui_output()` for audio output retrieval
- TTS models added to `MEMORY_MULTIPLIERS` and `FAMILY_FALLBACKS`

## [0.7.0] - 2026-01-13

### Added
- **Voice Generation** — Text-to-speech using Chatterbox TTS with voice cloning
  - Quick mode: Fast generation with expression tags like `[laugh]`, `[sigh]`, `[gasp]`
  - Quality mode: Higher fidelity with emotion control (calm → dramatic slider)
  - Voice cloning: Upload 5-10 sec of speech to clone any voice
  - Audio controls: Speed (0.5-1.5x) and pitch (-6 to +6 semitones)
  - Voice presets: Drop .wav/.mp3 files in `voices/` folder
- **Dynamic Memory Detection** — Real-time available memory checking (not just total RAM)
- **Memory Requirement Estimates** — Each model shows estimated memory needed for inference
- **Memory-Aware Model Selector** — Color-coded badges (green/yellow/orange/red) show if model fits
- **Live Memory Display** — Header shows current available memory, updates every 10 seconds
- **Memory Pressure Indicator** — Color changes based on system memory pressure

### Changed
- Model dropdown now shows estimated VRAM requirement alongside file size
- Models that won't fit show warning instead of description
- Header displays available memory instead of total RAM
- Voice tab now fully functional (was placeholder)

### Technical
- Added `get_available_memory_gb()` to SystemInfo for real-time memory checking
- Added `get_memory_pressure()` for system-wide memory status
- Added `estimate_memory_required()` with architecture-specific multipliers
- Model dataclass now includes `vram_required_gb` and `can_run_now()` method
- Added voice generation functions: `generate_speech()`, `load_voice_models()`, `process_voice_audio()`
- Voice models lazy-loaded to conserve memory until first use

## [0.6.0] - 2026-01-12

### Added
- Improved progress tracking with websocket connection to ComfyUI
- More accurate time estimates based on actual step timing

## [0.5.0] - 2026-01-12

### Added
- **Recent Generations Gallery** — Browse and click thumbnails of your last 12 creations
- **Seed Display & Reuse** — See the seed used, easily reuse it for variations
- **Generation Time Tracking** — Shows how long each generation took
- **Prompt Enhancement** — "✨ Enhance" button adds quality-boosting keywords
- **Smart Model Detection** — Auto-applies optimal settings for Lightning/Turbo models
- **Progress Indicator** — Visual feedback during generation
- **Keyboard Shortcut** — Ctrl+Enter to generate (coming soon)
- **Polished Button Animations** — Subtle hover effects for better feedback

### Changed
- Reorganized project structure for GitHub release
- Improved button styling with gradient and hover effects
- Better status messages throughout the interface
- Cleaner separation of concerns (UI/backend)

### Fixed
- Aspect ratio preview now updates smoothly
- Seed extraction from generation status

## [0.4.0] - 2026-01-12

### Added
- Aspect ratio preview widget
- Auto-start ComfyUI from onboarding screen
- Model-specific generation settings (Lightning, Turbo, SD1.5, SDXL)
- Cross-machine access (Mac Studio serving MacBook Pro)
- Broken symlink handling in model discovery

### Changed
- Complete UI redesign with custom styling
- Typography system with Inter font
- Onboarding screens for no-models and no-backend states
- Progressive disclosure of controls

## [0.3.0] - 2026-01-11

### Added
- Video generation tab with LTX-Video support
- Model tooltips with descriptions
- Dimension presets with use-case names
- Quality presets (Draft, Fast, Standard, Best)

### Changed
- Streamlined control layout
- Better model filtering (excludes VAEs, ControlNets)

## [0.2.0] - 2026-01-10

### Added
- Basic image generation
- Model selector
- Dimension controls
- Quality controls

## [0.1.0] - 2026-01-09

### Added
- Initial prototype
- ComfyUI backend integration
- NiceGUI interface foundation
