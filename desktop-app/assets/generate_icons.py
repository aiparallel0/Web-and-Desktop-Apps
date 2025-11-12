#!/usr/bin/env python3
"""
Icon Generator for Receipt Extractor Desktop App

This script converts the icon.svg file into platform-specific icon formats:
- icon.png (512x512) - Universal PNG format
- icon.ico - Windows icon format (multiple resolutions)
- icon.icns - macOS icon format
- icon-linux.png (512x512) - Linux icon format

Requirements:
    pip install pillow cairosvg

Usage:
    python generate_icons.py
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Please run: pip install pillow cairosvg")
    sys.exit(1)


def svg_to_png(svg_path, png_path, size):
    """Convert SVG to PNG at specified size."""
    cairosvg.svg2png(
        url=svg_path,
        write_to=png_path,
        output_width=size,
        output_height=size
    )
    print(f"✓ Generated: {png_path} ({size}x{size})")


def create_ico(png_path, ico_path):
    """Create Windows ICO file with multiple resolutions."""
    img = Image.open(png_path)

    # ICO requires multiple sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

    # Create images at different sizes
    images = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)

    # Save as ICO
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[img.size for img in images],
        append_images=images[1:]
    )
    print(f"✓ Generated: {ico_path} (multi-resolution)")


def create_icns(png_path, icns_path):
    """Create macOS ICNS file."""
    # Note: Creating proper ICNS requires iconutil (macOS only)
    # For cross-platform support, we'll just copy the PNG and notify
    img = Image.open(png_path)

    if sys.platform == 'darwin':
        # On macOS, create proper ICNS
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            iconset = os.path.join(tmpdir, 'icon.iconset')
            os.makedirs(iconset)

            # Create all required sizes for iconset
            sizes = [16, 32, 64, 128, 256, 512]
            for size in sizes:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(os.path.join(iconset, f'icon_{size}x{size}.png'))

                # Retina versions
                if size <= 256:
                    resized_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
                    resized_2x.save(os.path.join(iconset, f'icon_{size}x{size}@2x.png'))

            # Convert iconset to icns
            subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', icns_path])

        print(f"✓ Generated: {icns_path}")
    else:
        # On other platforms, just copy PNG as placeholder
        img.save(icns_path.replace('.icns', '.png'))
        print(f"⚠ ICNS generation requires macOS. Created PNG fallback instead.")
        print(f"  Please run this script on macOS to generate proper .icns file.")


def main():
    # Get paths
    assets_dir = Path(__file__).parent
    svg_path = assets_dir / 'icon.svg'

    if not svg_path.exists():
        print(f"ERROR: {svg_path} not found!")
        sys.exit(1)

    print("Receipt Extractor - Icon Generator")
    print("=" * 50)

    # Generate PNG (main icon)
    png_path = assets_dir / 'icon.png'
    svg_to_png(str(svg_path), str(png_path), 512)

    # Generate Windows ICO
    ico_path = assets_dir / 'icon.ico'
    create_ico(str(png_path), str(ico_path))

    # Generate macOS ICNS
    icns_path = assets_dir / 'icon.icns'
    create_icns(str(png_path), str(icns_path))

    # Generate Linux PNG (just a copy)
    linux_png_path = assets_dir / 'icon-linux.png'
    img = Image.open(png_path)
    img.save(linux_png_path)
    print(f"✓ Generated: {linux_png_path} (512x512)")

    print("=" * 50)
    print("✓ Icon generation complete!")
    print("\nNext steps:")
    print("1. Review the generated icons")
    print("2. Replace icon.svg with your custom design if desired")
    print("3. Re-run this script to regenerate icons")


if __name__ == '__main__':
    main()
