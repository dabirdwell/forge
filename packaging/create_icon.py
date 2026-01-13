#!/usr/bin/env python3
"""
Create Forge app icon.
Generates a 1024x1024 PNG and converts to .icns for macOS.

The icon design:
- Dark background with subtle gradient
- Flame/forge icon in cyan (#06b6d4)
- Modern, minimal, professional
"""

import subprocess
import sys
from pathlib import Path

# Try to use PIL, install if needed
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--break-system-packages"])
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

ICON_SIZE = 1024
OUTPUT_DIR = Path(__file__).parent


def create_icon():
    """Create the Forge app icon."""

    # Create base image with dark background
    img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background
    padding = 80
    corner_radius = 180

    # Draw rounded rectangle background
    bg_color = (15, 15, 15, 255)  # Very dark gray

    # Create rounded rectangle mask
    mask = Image.new('L', (ICON_SIZE, ICON_SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [padding, padding, ICON_SIZE - padding, ICON_SIZE - padding],
        radius=corner_radius,
        fill=255
    )

    # Draw background
    bg = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), bg_color)
    img.paste(bg, mask=mask)

    # Add subtle gradient overlay
    gradient = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)
    for y in range(padding, ICON_SIZE - padding):
        alpha = int(20 * (1 - (y - padding) / (ICON_SIZE - 2 * padding)))
        gradient_draw.line([(padding, y), (ICON_SIZE - padding, y)], fill=(255, 255, 255, alpha))

    img = Image.alpha_composite(img, gradient)

    # Draw flame icon
    draw = ImageDraw.Draw(img)
    accent = (6, 182, 212, 255)  # Cyan #06b6d4
    accent_glow = (6, 182, 212, 80)

    # Flame center point
    cx, cy = ICON_SIZE // 2, ICON_SIZE // 2 + 30

    # Draw glow effect first
    glow_img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)

    # Main flame shape (larger outer glow)
    flame_points = [
        (cx, cy - 280),       # Top tip
        (cx + 180, cy - 100), # Right upper
        (cx + 160, cy + 50),  # Right middle
        (cx + 100, cy + 180), # Right lower
        (cx, cy + 240),       # Bottom
        (cx - 100, cy + 180), # Left lower
        (cx - 160, cy + 50),  # Left middle
        (cx - 180, cy - 100), # Left upper
    ]

    # Draw glow
    glow_draw.polygon(flame_points, fill=accent_glow)
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=40))
    img = Image.alpha_composite(img, glow_img)

    # Redraw on composited image
    draw = ImageDraw.Draw(img)

    # Main flame (solid)
    inner_flame = [
        (cx, cy - 240),
        (cx + 140, cy - 80),
        (cx + 130, cy + 40),
        (cx + 80, cy + 150),
        (cx, cy + 200),
        (cx - 80, cy + 150),
        (cx - 130, cy + 40),
        (cx - 140, cy - 80),
    ]
    draw.polygon(inner_flame, fill=accent)

    # Inner detail - darker center to add depth
    inner_detail = [
        (cx, cy - 160),
        (cx + 80, cy - 40),
        (cx + 70, cy + 40),
        (cx + 40, cy + 100),
        (cx, cy + 130),
        (cx - 40, cy + 100),
        (cx - 70, cy + 40),
        (cx - 80, cy - 40),
    ]
    darker_accent = (4, 140, 165, 255)  # Slightly darker cyan
    draw.polygon(inner_detail, fill=darker_accent)

    # Hot center - bright white-ish
    hot_center = [
        (cx, cy - 80),
        (cx + 40, cy),
        (cx + 35, cy + 30),
        (cx + 20, cy + 60),
        (cx, cy + 80),
        (cx - 20, cy + 60),
        (cx - 35, cy + 30),
        (cx - 40, cy),
    ]
    hot_color = (150, 220, 235, 255)  # Light cyan, almost white
    draw.polygon(hot_center, fill=hot_color)

    # Save PNG
    png_path = OUTPUT_DIR / "AppIcon.png"
    img.save(png_path, "PNG")
    print(f"✓ Created {png_path}")

    # Convert to ICNS using iconutil (macOS only)
    iconset_dir = OUTPUT_DIR / "AppIcon.iconset"
    iconset_dir.mkdir(exist_ok=True)

    # Generate all required sizes
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(iconset_dir / f"icon_{size}x{size}.png")

        # @2x versions
        if size <= 512:
            resized_2x = img.resize((size * 2, size * 2), Image.LANCZOS)
            resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")

    # Rename files to match iconutil requirements
    icon_map = {
        "icon_16x16.png": "icon_16x16.png",
        "icon_16x16@2x.png": "icon_16x16@2x.png",
        "icon_32x32.png": "icon_32x32.png",
        "icon_32x32@2x.png": "icon_32x32@2x.png",
        "icon_64x64.png": "icon_32x32@2x.png",  # 64 = 32@2x
        "icon_128x128.png": "icon_128x128.png",
        "icon_128x128@2x.png": "icon_128x128@2x.png",
        "icon_256x256.png": "icon_256x256.png",
        "icon_256x256@2x.png": "icon_256x256@2x.png",
        "icon_512x512.png": "icon_512x512.png",
        "icon_512x512@2x.png": "icon_512x512@2x.png",
        "icon_1024x1024.png": "icon_512x512@2x.png",
    }

    # Try to create .icns
    try:
        icns_path = OUTPUT_DIR / "AppIcon.icns"
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
            check=True,
            capture_output=True
        )
        print(f"✓ Created {icns_path}")

        # Clean up iconset
        import shutil
        shutil.rmtree(iconset_dir)

    except FileNotFoundError:
        print("⚠ iconutil not found (not on macOS?). PNG icon created, but .icns skipped.")
    except subprocess.CalledProcessError as e:
        print(f"⚠ iconutil failed: {e.stderr.decode()}")
        print("  PNG icon created, but .icns conversion failed.")

    return png_path


if __name__ == "__main__":
    create_icon()
