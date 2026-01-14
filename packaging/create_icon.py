#!/usr/bin/env python3
"""
Create NeoVak app icon.
Generates a 1024x1024 PNG and converts to .icns for macOS.

The icon design:
- Dark background with subtle gradient
- Vacuum tube shape glowing amber (#f59e0b)
- Warm, retro-futuristic, alive
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
    """Create the NeoVak app icon - a glowing vacuum tube."""

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

    # Colors - amber/gold vacuum tube palette
    amber = (245, 158, 11, 255)        # #f59e0b - primary accent
    gold = (251, 191, 36, 255)         # #fbbf24 - hot/hover
    amber_glow = (245, 158, 11, 60)    # Amber with transparency for glow
    dark_amber = (180, 115, 8, 255)    # Darker amber for depth
    hot_white = (255, 230, 180, 255)   # Warm white for filament

    # Center point
    cx, cy = ICON_SIZE // 2, ICON_SIZE // 2

    # Draw glow effect first
    glow_img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)

    # Outer glow - large ellipse
    glow_draw.ellipse(
        [cx - 300, cy - 350, cx + 300, cy + 350],
        fill=amber_glow
    )
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=60))
    img = Image.alpha_composite(img, glow_img)

    # Redraw on composited image
    draw = ImageDraw.Draw(img)

    # Tube glass outline (dark, subtle)
    tube_outline = (40, 40, 40, 255)
    draw.ellipse([cx - 180, cy - 280, cx + 180, cy + 280], outline=tube_outline, width=8)

    # Tube glass (very subtle, translucent)
    glass_color = (60, 60, 60, 100)
    draw.ellipse([cx - 170, cy - 270, cx + 170, cy + 270], fill=glass_color)

    # Base/socket (bottom of tube)
    base_color = (50, 50, 50, 255)
    draw.rounded_rectangle(
        [cx - 120, cy + 180, cx + 120, cy + 300],
        radius=20,
        fill=base_color
    )
    # Base pins
    for offset in [-70, -25, 25, 70]:
        draw.rectangle(
            [cx + offset - 8, cy + 280, cx + offset + 8, cy + 320],
            fill=(80, 80, 80, 255)
        )

    # Top cap
    draw.ellipse([cx - 80, cy - 300, cx + 80, cy - 240], fill=base_color)

    # Inner glow (the "hot" part of the tube)
    inner_glow = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    inner_glow_draw = ImageDraw.Draw(inner_glow)
    inner_glow_draw.ellipse(
        [cx - 120, cy - 180, cx + 120, cy + 150],
        fill=(245, 158, 11, 120)
    )
    inner_glow = inner_glow.filter(ImageFilter.GaussianBlur(radius=30))
    img = Image.alpha_composite(img, inner_glow)

    # Redraw on composited image
    draw = ImageDraw.Draw(img)

    # Filament structure (the glowing element inside)
    # Vertical support wires
    wire_color = (100, 100, 100, 255)
    draw.line([(cx - 60, cy + 120), (cx - 60, cy - 160)], fill=wire_color, width=4)
    draw.line([(cx + 60, cy + 120), (cx + 60, cy - 160)], fill=wire_color, width=4)

    # Glowing filament (zigzag pattern)
    filament_points = []
    y_start = cy - 140
    y_end = cy + 100
    segments = 8
    amplitude = 50

    for i in range(segments + 1):
        y = y_start + (y_end - y_start) * i / segments
        x_offset = amplitude if i % 2 == 0 else -amplitude
        filament_points.append((cx + x_offset, y))

    # Draw filament with glow
    filament_glow = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    filament_glow_draw = ImageDraw.Draw(filament_glow)
    filament_glow_draw.line(filament_points, fill=gold, width=16)
    filament_glow = filament_glow.filter(ImageFilter.GaussianBlur(radius=8))
    img = Image.alpha_composite(img, filament_glow)

    # Sharp filament on top
    draw = ImageDraw.Draw(img)
    draw.line(filament_points, fill=hot_white, width=6)

    # Bright center spot (hottest part)
    bright_spot = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    bright_draw = ImageDraw.Draw(bright_spot)
    bright_draw.ellipse(
        [cx - 30, cy - 30, cx + 30, cy + 30],
        fill=(255, 240, 200, 180)
    )
    bright_spot = bright_spot.filter(ImageFilter.GaussianBlur(radius=15))
    img = Image.alpha_composite(img, bright_spot)

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
