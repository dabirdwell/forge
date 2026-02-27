# NeoVak TTS Backend Expansion

**Status:** Open
**Priority:** Medium
**Created:** 2026-02-11

---

## Objective

Add Sesame CSM and Qwen3-TTS as additional voice backends alongside Chatterbox TTS.

---

## Background

The house_ai project validated two new TTS systems:

| Backend | Strength | Tested Output |
|---------|----------|---------------|
| Sesame CSM | High-quality voice cloning from 10s reference | 4.4s audio in 7.4s (~1.68x realtime) |
| Qwen3-TTS VoiceDesign | Voice creation from text description | 5.5s audio, excellent quality |

Both are working in prototype at `/Claude_Technical/house_ai/.venv/`

Qwen3-TTS VoiceDesign is particularly notable—released 2026-02-10, allows natural language voice design without reference audio.

---

## Implementation Plan

### Phase 1: Backend Abstraction

Create unified TTS interface in `neovak_backend.py`:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable

class TTSBackend(ABC):
    """Base class for TTS backends."""
    
    name: str
    supports_voice_cloning: bool = False
    supports_voice_design: bool = False
    
    @abstractmethod
    def load(self, progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Load model. Returns (success, message)."""
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload model to free memory."""
        pass
    
    @abstractmethod
    def generate(
        self,
        text: str,
        output_path: Path,
        voice_reference: Optional[Path] = None,
        voice_description: Optional[str] = None,
        **kwargs
    ) -> tuple[bool, Path]:
        """Generate speech. Returns (success, output_path)."""
        pass
    
    @abstractmethod
    def get_status(self) -> tuple[bool, str]:
        """Get backend status. Returns (ready, message)."""
        pass


class ChatterboxBackend(TTSBackend):
    """Existing Chatterbox implementation wrapped."""
    name = "Chatterbox"
    supports_voice_cloning = True
    # ... wrap existing functions


class CSMBackend(TTSBackend):
    """Sesame CSM via mlx-audio."""
    name = "Sesame CSM"
    supports_voice_cloning = True
    # ... implement


class Qwen3TTSBackend(TTSBackend):
    """Qwen3-TTS VoiceDesign."""
    name = "Qwen3-TTS"
    supports_voice_design = True
    # ... implement
```

### Phase 2: CSM Integration

1. Add CSM imports (conditional to avoid conflict)
2. Implement `CSMBackend` class
3. Add voice cloning workflow (10s reference upload)
4. Test generation pipeline

### Phase 3: Qwen3-TTS Integration

1. Add qwen-tts imports (conditional)
2. Implement `Qwen3TTSBackend` class
3. Add voice description textarea to UI
4. Implement voice preset system for descriptions

### Phase 4: UI Updates

`neovak_ui.py` changes:

1. **Backend selector dropdown** in voice tab
   - Chatterbox (default)
   - Sesame CSM
   - Qwen3-TTS VoiceDesign

2. **Dynamic options panel** based on backend:
   - Chatterbox: Voice preset, expression tags, exaggeration
   - CSM: Reference audio upload, context audio
   - Qwen3-TTS: Voice description textarea

3. **Voice description presets** for Qwen3-TTS:
   - "Documentary Narrator"
   - "AI Assistant"
   - "Dramatic Announcer"
   - Custom...

### Phase 5: Dependency Resolution

Address transformers version conflict:

**Option A: Conditional imports** (preferred)
```python
def _get_csm_backend():
    """Lazy load to avoid import-time conflict."""
    from mlx_audio.tts.generate import generate_speech
    return generate_speech

def _get_qwen_backend():
    """Lazy load."""
    from qwen_tts import Qwen3TTSModel
    return Qwen3TTSModel
```

**Option B: Separate venvs** (fallback)
- Document venv switching in TTS_BACKENDS.md
- NeoVak calls subprocess with correct venv

---

## Files to Modify

| File | Changes |
|------|---------|
| `neovak_backend.py` | Add TTSBackend ABC, CSMBackend, Qwen3TTSBackend classes |
| `neovak_ui.py` | Backend selector, dynamic options panel |
| `requirements.txt` | Add mlx-audio, qwen-tts as optional |
| `docs/TTS_BACKENDS.md` | Update with integration status |

---

## Testing Checklist

- [ ] Chatterbox still works (no regression)
- [ ] CSM generates audio from reference
- [ ] Qwen3-TTS generates audio from description
- [ ] Backend switching works without crash
- [ ] Memory properly freed on backend switch
- [ ] UI updates correctly per backend

---

## Acceptance Criteria

1. All three TTS backends functional in NeoVak
2. Smooth backend switching without restart
3. Backend-specific options visible only when relevant
4. Voice description presets for Qwen3-TTS
5. Documentation updated

---

## Related

- [[TTS_BACKENDS]] - Technical reference
- [[NeoVak_Project]] - Project overview
- `/Claude_Technical/house_ai/README.md` - Prototype validation

---

*Assigned to: Claude Code session (substantial development)*
