# 📦 Distributing Forge

This guide covers how to package and distribute Forge to other users.

## Quick Build

```bash
# Build for your current platform
./packaging/build_all.sh
```

## Platform-Specific Builds

### macOS (.app + .dmg)

```bash
# Build the app bundle
./packaging/build_app.sh

# Create DMG installer (optional)
./packaging/create_dmg.sh
```

**Output:**
- `dist/Forge.app` — Drag to Applications
- `dist/Forge-1.0.0-macOS.dmg` — Professional installer

**What users get:**
- Double-click app to launch
- Auto-detects ComfyUI location
- Starts ComfyUI automatically if not running
- First-run setup wizard
- Browser opens automatically

### Windows (Portable)

```bash
# On Windows
packaging\build_windows.bat
```

**Output:**
- `dist/Forge-Windows/` folder
- Zip this folder to distribute

**What users get:**
- `Start Forge.bat` — Double-click to run
- First-run creates virtual environment
- Auto-installs dependencies
- Guides user to install ComfyUI if missing

### Linux (Tarball)

```bash
./packaging/build_linux.sh
```

**Output:**
- `dist/Forge-Linux/` folder
- `dist/Forge-Linux-1.0.0.tar.gz` — Distributable tarball

**What users get:**
- `./forge.sh` — Run from terminal
- Auto-detects ComfyUI
- Desktop integration file included

## Distribution Checklist

Before sharing:

- [ ] Test fresh install on clean machine
- [ ] Verify ComfyUI detection works
- [ ] Test with at least one checkpoint model
- [ ] Check all tabs function correctly
- [ ] Update version number if needed

## GitHub Releases

To create a GitHub release:

```bash
# Tag the release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Build all platforms
VERSION=1.0.0 ./packaging/build_all.sh

# Upload to GitHub Releases:
# - Forge-1.0.0-macOS.dmg
# - Forge-Windows-1.0.0.zip
# - Forge-Linux-1.0.0.tar.gz
```

## What Users Need

### All Platforms
- **ComfyUI** — The AI backend (https://github.com/comfyanonymous/ComfyUI)
- **At least one model** — Checkpoint file in ComfyUI/models/checkpoints/
- **8GB+ RAM** — 16GB+ recommended for SDXL models

### macOS
- macOS 11 (Big Sur) or later
- Apple Silicon recommended (M1/M2/M3/M4)
- Python 3.10+ (bundled with macOS or Homebrew)

### Windows
- Windows 10/11
- Python 3.10+ from python.org
- ~4GB disk space

### Linux
- Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch, etc.
- Python 3.10+
- python3-venv, python3-pip packages

## Handling Support Questions

Common issues users may encounter:

### "ComfyUI not found"
- Forge will prompt to locate ComfyUI
- User needs to browse to their ComfyUI folder
- Path is saved to config for future launches

### "No models found"
- User needs at least one checkpoint model
- Direct them to civitai.com or huggingface.co
- See docs/MODEL_GUIDE.md for recommendations

### "Python not installed"
- macOS: `brew install python3` or python.org
- Windows: Download from python.org
- Linux: `sudo apt install python3 python3-venv`

### macOS "unidentified developer" warning
- Right-click app → Open
- Or: System Preferences → Privacy & Security → Open Anyway

## Version Numbering

We use semantic versioning:
- **Major.Minor.Patch** (e.g., 1.0.0)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

Set version when building:
```bash
VERSION=1.2.3 ./packaging/build_all.sh
```

## Code Signing (Optional)

For wider distribution without security warnings:

### macOS
```bash
# Sign the app (requires Apple Developer account)
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Your Name" \
    dist/Forge.app

# Notarize (required for distribution outside App Store)
xcrun notarytool submit dist/Forge-1.0.0-macOS.dmg \
    --apple-id "your@email.com" \
    --team-id "TEAMID" \
    --password "app-specific-password"
```

### Windows
Use signtool with a code signing certificate.

## File Sizes

Approximate sizes:
- macOS .app: ~5 MB (before venv/dependencies)
- macOS .dmg: ~3 MB
- Windows .zip: ~3 MB
- Linux .tar.gz: ~2 MB

First-run downloads (dependencies): ~200 MB
