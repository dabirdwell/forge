# Contributing to Forge

Thanks for your interest in contributing to Forge!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/forge.git`
3. Create a branch: `git checkout -b my-feature`
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/forge.git
cd forge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in development
python forge_nicegui.py
```

## Code Style

- Python: Follow PEP 8
- Use descriptive variable names
- Add docstrings to functions
- Keep functions focused and small

## Testing

Before submitting:
- Test all four tabs (Image, Video, Voice, Music)
- Test on macOS (primary platform)
- Verify ComfyUI integration works
- Check for console errors

## Pull Request Guidelines

- One feature/fix per PR
- Clear description of changes
- Reference any related issues
- Include screenshots for UI changes

## Reporting Issues

When reporting bugs:
- Include macOS/Python version
- Include ComfyUI version
- Describe steps to reproduce
- Include error messages/logs

## Feature Requests

Open an issue with:
- Clear description of the feature
- Use case / why it's needed
- Any implementation ideas

## Areas for Contribution

Check the roadmap in README.md:
- Image-to-video workflows
- LoRA browser and support
- Additional model support
- UI/UX improvements
- Documentation

## Questions?

Open a GitHub Discussion or issue.

---

Thank you for helping make Forge better!
