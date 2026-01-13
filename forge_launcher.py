#!/usr/bin/env python3
"""
Forge Native Launcher
Creates a native macOS window that runs Forge - no terminal needed.

This is the entry point for the packaged .app:
1. Shows a native window (not a browser)
2. Auto-starts ComfyUI backend
3. Runs NiceGUI server
4. Embeds the web UI in the native window

Think: How LM Studio works, but for multimedia AI.
"""

import sys
import os
import subprocess
import threading
import time
import json
from pathlib import Path

# Check for required packages
try:
    import webview
except ImportError:
    print("Installing pywebview for native window support...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview", "--break-system-packages"])
    import webview

# Configuration
APP_NAME = "Forge"
APP_VERSION = "1.0.0"
FORGE_PORT = 7861
COMFYUI_PORT = 8188
COMFYUI_URL = f"http://127.0.0.1:{COMFYUI_PORT}"
FORGE_URL = f"http://127.0.0.1:{FORGE_PORT}"

# Paths
if getattr(sys, 'frozen', False):
    # Running as compiled app
    APP_DIR = Path(sys._MEIPASS)
    RESOURCES_DIR = APP_DIR
else:
    # Running as script
    APP_DIR = Path(__file__).parent
    RESOURCES_DIR = APP_DIR

CONFIG_DIR = Path.home() / ".config" / "forge"
CONFIG_FILE = CONFIG_DIR / "forge_config.json"
LOG_FILE = CONFIG_DIR / "forge.log"


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def log(message: str):
    """Log message to file and console."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    print(log_line.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_line)


def load_config() -> dict:
    """Load or create configuration."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            pass

    # Default config
    config = {
        "comfyui_path": "",
        "comfyui_url": COMFYUI_URL,
        "output_dir": str(Path.home() / "Documents" / "Forge-Output"),
        "model_paths": []
    }

    # Try to find ComfyUI
    common_paths = [
        Path.home() / "ComfyUI",
        Path.home() / "comfyui",
        Path.home() / "AI" / "ComfyUI",
        Path.home() / "Documents" / "AI-Projects" / "ComfyUI",
        Path.home() / "Projects" / "ComfyUI",
        Path("/Applications/ComfyUI"),
    ]

    for path in common_paths:
        if (path / "main.py").exists():
            config["comfyui_path"] = str(path)
            config["model_paths"] = [str(path / "models")]
            break

    save_config(config)
    return config


def save_config(config: dict):
    """Save configuration."""
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def check_comfyui_running() -> bool:
    """Check if ComfyUI is running."""
    import urllib.request
    try:
        urllib.request.urlopen(COMFYUI_URL, timeout=2)
        return True
    except:
        return False


def check_forge_running() -> bool:
    """Check if Forge is running."""
    import urllib.request
    try:
        urllib.request.urlopen(FORGE_URL, timeout=2)
        return True
    except:
        return False


def start_comfyui(config: dict) -> subprocess.Popen | None:
    """Start ComfyUI backend."""
    comfyui_path = config.get("comfyui_path", "")

    if not comfyui_path or not Path(comfyui_path).exists():
        log("ComfyUI path not configured or doesn't exist")
        return None

    comfyui_path = Path(comfyui_path)

    # Check for venv
    venv_python = comfyui_path / "venv" / "bin" / "python"
    if venv_python.exists():
        python_cmd = str(venv_python)
    else:
        python_cmd = sys.executable

    log(f"Starting ComfyUI from {comfyui_path}")

    try:
        process = subprocess.Popen(
            [python_cmd, "main.py", "--listen", "127.0.0.1", "--port", str(COMFYUI_PORT)],
            cwd=str(comfyui_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Wait for ComfyUI to start
        for i in range(60):
            if check_comfyui_running():
                log("ComfyUI started successfully")
                return process
            time.sleep(1)

        log("ComfyUI failed to start within 60 seconds")
        return None

    except Exception as e:
        log(f"Failed to start ComfyUI: {e}")
        return None


def start_forge():
    """Start Forge server in background thread."""
    def run_forge():
        # Import and run Forge
        sys.path.insert(0, str(RESOURCES_DIR))
        os.chdir(str(RESOURCES_DIR))

        # Set environment
        os.environ["FORGE_CONFIG"] = str(CONFIG_FILE)

        try:
            from forge_nicegui import ui
            ui.run(
                title=f'{APP_NAME} - Local AI Creative Suite',
                port=FORGE_PORT,
                reload=False,
                show=False,  # Don't open browser - we'll use native window
            )
        except Exception as e:
            log(f"Forge error: {e}")

    thread = threading.Thread(target=run_forge, daemon=True)
    thread.start()
    return thread


class ForgeApp:
    """Main application controller."""

    def __init__(self):
        self.config = None
        self.comfyui_process = None
        self.forge_thread = None
        self.window = None

    def setup(self):
        """Initialize the application."""
        ensure_config_dir()
        log(f"Starting {APP_NAME} v{APP_VERSION}")

        self.config = load_config()

        # Check if ComfyUI is running
        if not check_comfyui_running():
            if self.config.get("comfyui_path"):
                log("Starting ComfyUI...")
                self.comfyui_process = start_comfyui(self.config)
                if not self.comfyui_process:
                    return False
            else:
                log("ComfyUI not configured")
                # Continue anyway - Forge will show setup screen

        # Start Forge
        log("Starting Forge server...")
        self.forge_thread = start_forge()

        # Wait for Forge to be ready
        for i in range(30):
            if check_forge_running():
                log("Forge is ready")
                return True
            time.sleep(0.5)

        log("Forge failed to start")
        return False

    def show_setup_dialog(self):
        """Show setup dialog if ComfyUI not found."""
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox

            root = tk.Tk()
            root.withdraw()

            result = messagebox.askyesno(
                "Forge Setup",
                "ComfyUI was not found.\n\n"
                "ComfyUI is the AI backend that powers image, video, and music generation.\n\n"
                "Would you like to locate your ComfyUI installation?"
            )

            if result:
                folder = filedialog.askdirectory(title="Select your ComfyUI folder")
                if folder and (Path(folder) / "main.py").exists():
                    self.config["comfyui_path"] = folder
                    self.config["model_paths"] = [str(Path(folder) / "models")]
                    save_config(self.config)
                    return True
                elif folder:
                    messagebox.showerror(
                        "Invalid Folder",
                        "The selected folder doesn't appear to be a ComfyUI installation.\n\n"
                        "(main.py not found)"
                    )

            root.destroy()
            return False

        except Exception as e:
            log(f"Dialog error: {e}")
            return False

    def run(self):
        """Run the application."""
        # Try to setup
        if not self.config.get("comfyui_path"):
            if not self.show_setup_dialog():
                log("Setup cancelled")
                return

        if not self.setup():
            log("Setup failed")
            return

        # Create native window
        log("Opening native window...")
        self.window = webview.create_window(
            f'{APP_NAME}',
            FORGE_URL,
            width=1400,
            height=900,
            min_size=(1000, 700),
            background_color='#0a0a0a',
        )

        # Run the window (blocks until closed)
        webview.start()

        log("Window closed, shutting down...")
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        if self.comfyui_process:
            log("Stopping ComfyUI...")
            self.comfyui_process.terminate()
            try:
                self.comfyui_process.wait(timeout=5)
            except:
                self.comfyui_process.kill()


def main():
    """Main entry point."""
    app = ForgeApp()
    try:
        app.run()
    except KeyboardInterrupt:
        log("Interrupted")
    except Exception as e:
        log(f"Fatal error: {e}")
        raise
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
