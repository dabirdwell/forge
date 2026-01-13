# 🔥 Forge

**Local AI Creative Suite for Mac**

Generate images, videos, voice, and music using AI models running entirely on your machine. No cloud, no subscriptions, no limits.

*Think "LM Studio for multimedia"*

<!-- Add screenshot: ![Forge Screenshot](screenshots/forge-hero.png) -->

## 📥 Download

**[Download Forge for Mac →](https://github.com/dabirdwell/forge/releases/latest)**

Just download, drag to Applications, and double-click. No terminal required.

| Platform | Download | Requirements |
|----------|----------|--------------|
| **macOS** | [Forge.dmg](https://github.com/dabirdwell/forge/releases/latest/download/Forge.dmg) | macOS 11+, Apple Silicon recommended |
| **Windows** | Coming soon | — |
| **Linux** | Coming soon | — |

### What You Need

1. **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** — The AI backend (Forge will help you set it up)
2. **At least one AI model** — Forge guides you through downloading your first model

That's it. Forge handles everything else automatically.

---

## ✨ Features

### 🖼️ Image Generation
- **Create** — Generate images from text with SD 1.5, SDXL, Flux, Lightning, Turbo
- **Edit** — Transform existing images with img2img (upload → prompt → transform)
- **Upscale** — Enhance resolution 4x with AI upscalers (UltraSharp, ESRGAN, etc.)
- Smart model detection with memory-aware recommendations

### 🎬 Video Generation
- Text-to-video with LTX-Video
- Duration presets (1-3 seconds)
- Motion strength control

### 🗣️ Voice Generation
- Text-to-speech with Chatterbox TTS (built-in, no setup required)
- Expression tags: `[laugh]`, `[sigh]`, `[gasp]`, `[cough]`
- Voice cloning from 5-10 second samples
- Speed & pitch control
- BYOM support: XTTS, F5-TTS, Bark, TorToise, StyleTTS2 via ComfyUI

### 🎵 Music Generation
- BYOM architecture for music models
- Support for MusicGen, Stable Audio, AudioCraft, Riffusion, AudioLDM
- Duration presets (5s, 15s, 30s, 60s)
- Style tags: ambient, electronic, orchestral, lofi, rock, jazz, classical
- Melody conditioning (upload audio to guide generation)

### 🎯 Quality of Life
- **Memory-aware model selector** — Color-coded badges show if model fits in RAM
- **One-click presets** — Square, Portrait, Landscape + quality settings
- **AI prompt enhancement** — Expand simple ideas into detailed prompts
- **Generation history** — Browse recent creations with thumbnails
- **Keyboard shortcuts** — Cmd+Enter to generate
- **Beautiful dark UI** — Designed for creators, not engineers

---

## 🛠️ Building from Source

<details>
<summary>For developers who want to modify Forge or build it themselves</summary>

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4) — Intel works but slower
- Python 3.10+
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed somewhere on your Mac
- At least one checkpoint model

### Build the App

```bash
# Clone Forge
git clone https://github.com/dabirdwell/forge.git
cd forge

# Build Forge.app
./packaging/build_app.sh
```

The built app will be in `dist/Forge.app`. Drag it to Applications.

### Run from Source (Development)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Forge
python forge_launcher.py
```

</details>

## 📦 Model Setup

Forge auto-discovers models from your ComfyUI installation.

### Model Locations

| Type | Path | Examples |
|------|------|----------|
| **Image** | `ComfyUI/models/checkpoints/` | SD 1.5, SDXL, Flux, Lightning |
| **Video** | `ComfyUI/models/checkpoints/` | LTX-Video |
| **Upscalers** | `ComfyUI/models/upscale_models/` | ESRGAN, RealESRGAN, UltraSharp |
| **Voice** | `ComfyUI/models/TTS/` | XTTS, F5-TTS, Bark |
| **Music** | `ComfyUI/models/audio/` | MusicGen, Stable Audio |

### Recommended Starter Models

| Model | Size | Tab | Notes |
|-------|------|-----|-------|
| [DreamShaper 8](https://civitai.com/models/4384) | 2 GB | Image | General purpose, fast |
| [SDXL Lightning 4-step](https://huggingface.co/ByteDance/SDXL-Lightning) | 6.5 GB | Image | High quality, only 4 steps |
| [LTX-Video 2B](https://huggingface.co/Lightricks/LTX-Video) | 5 GB | Video | Text-to-video |
| [4x-UltraSharp](https://openmodeldb.info/models/4x-UltraSharp) | 67 MB | Image/Upscale | Best photo upscaler |

Voice generation works out-of-the-box with built-in Chatterbox TTS (downloads automatically on first use).

📖 See **[docs/MODEL_GUIDE.md](docs/MODEL_GUIDE.md)** for detailed model recommendations and download links.

## 📖 Usage

### Create an Image

1. Ensure **🖼️ Create** mode is selected
2. Select a model from the dropdown
3. Type a description (or click 🎲 for inspiration)
4. Click "✨ Enhance" to expand your prompt (optional)
5. Choose size and quality presets
6. Click **Create Image**

### Edit an Image (img2img)

1. Click **✏️ Edit** mode
2. Upload an image
3. Describe how you want to transform it
4. Choose transformation strength (Subtle → Creative)
5. Click **Transform Image**

### Upscale an Image

1. Click **🔍 Upscale** mode
2. Upload an image
3. Select an upscaler model
4. Click **Upscale Image**

### Generate Voice

1. Switch to **Voice** tab
2. Type text (add expression tags like `[laugh]` for natural sounds)
3. Optionally upload a voice sample to clone
4. Adjust speed/pitch if desired
5. Click **Generate**

### Generate Music

1. Switch to **Music** tab
2. Select a music model
3. Describe the music you want
4. Choose duration and style tags
5. Optionally upload audio for melody conditioning
6. Click **Generate**

## ⚙️ Configuration

### Config File (Recommended)

Copy `forge_config.example.json` to `forge_config.json` and customize:

```json
{
  "comfyui_path": "~/ComfyUI",
  "comfyui_url": "http://127.0.0.1:8188",
  "output_dir": "~/Documents/Forge-Output",
  "model_paths": [
    "~/ComfyUI/models",
    "/Volumes/ExternalDrive/AI-Models"
  ]
}
```

### Environment Variables (Alternative)

```bash
# Custom ComfyUI URL (default: http://127.0.0.1:8188)
export COMFYUI_URL=http://127.0.0.1:8188

# Custom output directory
export FORGE_OUTPUT_DIR=/path/to/outputs

# Additional model search paths (colon-separated)
export FORGE_MODEL_PATHS=/path/to/models:/another/path
```

### Voice Presets

Drop `.wav` or `.mp3` files in `forge/voices/` folder to add voice presets:

```
voices/
├── Narrator.wav     → "Narrator" in dropdown
├── Warm.wav         → "Warm" in dropdown
└── Energetic.mp3    → "Energetic" in dropdown
```

## 🎨 Model Compatibility

### Image Models
- ✅ Stable Diffusion 1.5
- ✅ SDXL / SDXL Lightning / SDXL Turbo
- ✅ DreamShaper variants
- ✅ RealVis XL
- ✅ Flux (experimental)

### Video Models
- ✅ LTX-Video 2B (all variants)
- ⚠️ Wan 2.1/2.2 (Linux/Windows only — Mac MPS has fp8 issues)

### Voice Models
- ✅ Chatterbox TTS (built-in, always available)
- ✅ XTTS v2 (via ComfyUI)
- ✅ F5-TTS (via ComfyUI)
- ✅ Bark (via ComfyUI)
- ✅ TorToise (via ComfyUI)

### Music Models
- ✅ MusicGen (via ComfyUI)
- ✅ Stable Audio (via ComfyUI)
- ✅ AudioCraft (via ComfyUI)
- ✅ Riffusion (via ComfyUI)

## 🐛 Troubleshooting

### "ComfyUI not running"
Use the launcher script which handles this automatically:
```bash
./start.sh
```
Or start ComfyUI manually in a separate terminal before running Forge.

### "No models found"
Check that you have at least one `.safetensors` or `.ckpt` file in `models/checkpoints/`.

### Black images on Mac
Start ComfyUI with:
```bash
python main.py --force-fp32
```

### Model shows red/orange memory warning
The model may be too large for available RAM. Try:
- Closing other applications
- Using a smaller model
- Restarting to free memory

### Video generation timeout
Video generation takes 2-10 minutes. Try:
- Reducing frame count (25 instead of 81)
- Reducing resolution (512×320)
- Using fewer steps

## 📦 Downloads

Pre-built packages available for:

| Platform | Download | Notes |
|----------|----------|-------|
| **macOS** | [Forge.dmg](https://github.com/dabirdwell/forge/releases) | Apple Silicon recommended |
| **Windows** | [Forge-Windows.zip](https://github.com/dabirdwell/forge/releases) | Windows 10/11 |
| **Linux** | [Forge-Linux.tar.gz](https://github.com/dabirdwell/forge/releases) | Ubuntu 20.04+, etc. |

Or build from source (see Installation above).

## 📁 Project Structure

```
forge/
├── start.sh                  # Easy launcher script
├── forge_nicegui.py          # Main UI application
├── forge_backend.py          # ComfyUI integration & generation logic
├── forge_progress.py         # Real-time progress tracking
├── forge_config.json         # Local configuration (gitignored)
├── forge_config.example.json # Example configuration
├── voices/                   # Voice preset samples
├── output/                   # Generated files (gitignored)
├── workflows/                # ComfyUI workflow templates
├── packaging/                # Build scripts for distribution
├── docs/
│   ├── MODEL_GUIDE.md        # Detailed model setup guide
│   └── DISTRIBUTION.md       # Packaging & distribution guide
├── requirements.txt
├── CHANGELOG.md
├── VISION.md
└── README.md
```

## 🤝 Contributing

Contributions welcome! Current roadmap:

- [x] Inpainting with mask drawing
- [x] ControlNet support
- [x] Batch generation
- [x] Presets/favorites system
- [ ] Image-to-video workflows
- [ ] LoRA browser and support

## 📄 License

MIT License — use freely, attribution appreciated.

---

Built with 💜 using [NiceGUI](https://nicegui.io) and [ComfyUI](https://github.com/comfyanonymous/ComfyUI)

---

## 🔮 Vision

Forge aims to be **"LM Studio for multimedia"** — making local AI creative tools accessible to everyone, not just technical users. See [VISION.md](VISION.md) for the full roadmap.
