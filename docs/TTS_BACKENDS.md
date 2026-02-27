# NeoVak TTS Backends

*Technical reference for text-to-speech systems in NeoVak*

**Last Updated:** 2026-02-11
**Status:** Chatterbox integrated, CSM and Qwen3-TTS pending integration

---

## Overview

NeoVak supports multiple TTS backends for voice generation. Each has different strengths:

| Backend | Voice Cloning | Voice Design | Speed | Quality | Status |
|---------|--------------|--------------|-------|---------|--------|
| Chatterbox | ✅ Reference audio | ❌ | Fast (turbo mode) | Good | **Integrated** |
| Sesame CSM | ✅ 10s reference | ❌ | ~1.7x realtime | Excellent | Prototype |
| Qwen3-TTS VoiceDesign | ❌ | ✅ Text description | ~1x realtime | Excellent | Prototype |

---

## Chatterbox TTS (Current)

**Location:** Integrated in `neovak_backend.py`
**Model:** ChatterboxTTS / ChatterboxTurboTTS from HuggingFace

### Capabilities
- Two quality modes: Turbo (fast) and Standard (quality)
- Voice cloning from reference audio
- Expression tags for emotion control
- ~20 voice presets included

### Expression Tags
```
[laugh] [sigh] [cough] [sniffle] [groan] [yawn] [gasp]
```

### Usage in NeoVak
```python
from neovak_backend import generate_speech, load_voice_models

# Load models (first time)
load_voice_models()

# Generate speech
result = generate_speech(
    text="Hello world",
    mode="turbo",  # or "standard"
    voice_preset="female_1",
    exaggeration=0.5
)
```

### Voice Presets Directory
`/Fawkes/Products and Services/NeoVak/voices/`

---

## Sesame CSM (Pending Integration)

**Prototype Location:** `/Claude_Technical/house_ai/.venv/`
**Model:** `mlx-community/csm-1b` via mlx-audio
**Released:** January 2025

### Key Features
- Conversational context awareness
- 10-second reference audio for voice cloning
- Native Apple Silicon optimization via MLX
- 1B parameters, ~8.6GB peak memory

### Benchmarks (Mac Studio M2 Max)
- 4.4 seconds audio in 7.4 seconds (~1.68x realtime)
- 14.3 tokens/sec, 14,282 samples/sec

### Prototype Usage
```python
from mlx_audio.tts.generate import generate_speech

audio = generate_speech(
    text="Your text here",
    model_path="mlx-community/csm-1b"
)
```

### Integration Notes
- Requires `mlx-audio` package
- Conflict with Qwen3-TTS: mlx-audio needs transformers 5.0.0rc3
- Consider separate venv or conditional imports

---

## Qwen3-TTS VoiceDesign (Pending Integration)

**Prototype Location:** `/Claude_Technical/house_ai/.venv/`
**Model:** `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`
**Released:** 2026-02-10 (yesterday!)

### Key Features
- **VoiceDesign**: Create voices from natural language descriptions
- No reference audio needed
- Instruction control for emotion/tone
- 10 languages supported
- 97ms streaming latency
- Apache 2.0 license

### Voice Description Example
```
"Cold, authoritative AI presence. Deep masculine voice with 
deliberate pacing and subtle mechanical undertone. Speaks with 
unsettling calm, as if discussing something routine while 
implying threat."
```

### Model Variants
| Variant | Purpose | Size |
|---------|---------|------|
| VoiceDesign | Text-to-voice description | 1.7B |
| CustomVoice | 9 premium speaker presets | 1.7B |
| Base | 3-second voice cloning | 1.7B |

### Prototype Usage
```python
from qwen_tts import Qwen3TTSModel

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
)

audio = model.synthesize(
    text="Your text here",
    voice_description="Warm, friendly narrator voice"
)
```

### Integration Notes
- Requires `qwen-tts` package
- PyTorch/MPS backend (no MLX native yet)
- ~3GB model download
- Conflict with CSM: qwen-tts needs transformers 4.57.3

---

## Dependency Conflict Resolution

CSM (mlx-audio) and Qwen3-TTS have conflicting transformers requirements:

### Option 1: Separate Virtual Environments
```bash
# CSM environment
python -m venv csm_env
source csm_env/bin/activate
pip install mlx-audio

# Qwen3-TTS environment  
python -m venv qwen_env
source qwen_env/bin/activate
pip install qwen-tts
```

### Option 2: Conditional Loading
Only import the backend being used. The conflict only matters at import time.

### Option 3: Live with Warning
Current prototype uses single venv with warning. Both packages functional despite version mismatch.

---

## Integration Roadmap

### Phase 1: Backend Abstraction
Create unified `TTSBackend` interface in `neovak_backend.py`:

```python
class TTSBackend:
    def load(self) -> None: ...
    def unload(self) -> None: ...
    def generate(self, text: str, **kwargs) -> Path: ...
    def get_status(self) -> tuple[bool, str]: ...
```

### Phase 2: CSM Integration
- Add CSM as backend option
- Voice cloning workflow in UI
- Reference audio upload

### Phase 3: Qwen3-TTS Integration
- Add VoiceDesign as backend option
- Voice description textarea in UI
- Per-mode voice instructions for house_ai use case

### Phase 4: Backend Selection UI
- Dropdown to select TTS backend
- Backend-specific options panel
- Model download/management

---

## Use Case Mapping

| Use Case | Recommended Backend | Reason |
|----------|-------------------|--------|
| Clone specific voice | CSM or Chatterbox | Reference audio workflow |
| Design new character voice | Qwen3-TTS VoiceDesign | Natural language description |
| Quick narration | Chatterbox Turbo | Fastest generation |
| House AI psychological modes | Qwen3-TTS VoiceDesign | Per-mode voice instructions |
| Emotional expression | Chatterbox | Expression tags |

---

## Related

- [[NeoVak_Project]] - Project overview
- [[AI_House_Intelligence]] - House AI using TTS
- [[Production_Orchestration_System]] - Voice for show production
- [[AI_Orchestration_Ecosystem]] - Full tool ecosystem

---

*Created: 2026-02-11*
*Location: /Fawkes/Products and Services/NeoVak/docs/*
