# Desktop Application

Electron-based desktop application for receipt extraction.

## Quick Start

```bash
# Install dependencies
npm install

# Run app
npm start
```

## Building Distributables

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```

Built applications will be in `dist/` directory.

## Requirements

- Node.js 16+
- Python 3.8+ (must be in PATH)
- Python dependencies installed globally:
  ```bash
  pip install torch transformers pillow opencv-python numpy pytesseract
  ```

## Notes

- First run will download AI models (~500MB-1GB)
- Models are cached for subsequent runs
- Python must be accessible from command line
- Build uses `--asar=false` to ensure Python scripts are accessible
# Desktop App Icons

This directory contains the application icons for the Receipt Extractor desktop app.

## Current Status

**Placeholder icons are provided.** The current `icon.svg` is a simple receipt-themed design with AI elements.

## Generating Icons

To generate platform-specific icon formats from the SVG:

### 1. Install Dependencies

```bash
pip install pillow cairosvg
```

### 2. Run Generator

```bash
python generate_icons.py
```

This will create:
- `icon.png` (512x512) - Universal PNG format
- `icon.ico` - Windows icon (multiple resolutions: 16, 32, 48, 64, 128, 256)
- `icon.icns` - macOS icon (requires macOS to generate properly)
- `icon-linux.png` (512x512) - Linux icon

## Customizing Icons

### Option 1: Replace SVG (Recommended)

1. Create your custom icon in SVG format (512x512px recommended)
2. Save as `icon.svg` in this directory
3. Run `python generate_icons.py` to regenerate all formats

### Option 2: Replace Individual Files

You can also directly replace individual icon files:

- **Windows:** Replace `icon.ico`
- **macOS:** Replace `icon.icns`
- **Linux:** Replace `icon-linux.png`
- **Universal:** Replace `icon.png`

## Icon Requirements

### Design Guidelines
- **Size:** 512x512px or larger (SVG is scalable)
- **Format:** SVG for source, PNG/ICO/ICNS for platforms
- **Style:** Clear and recognizable at small sizes (16x16px)
- **Theme:** Receipt/document related (consider app branding)

### Platform-Specific Formats

| Platform | Format | Sizes Required |
|----------|--------|----------------|
| Windows  | .ico   | 16, 32, 48, 64, 128, 256 |
| macOS    | .icns  | 16, 32, 64, 128, 256, 512 (with @2x) |
| Linux    | .png   | 512x512 (or multiple sizes) |

## Current Placeholder Design

The placeholder icon features:
- Blue background (#00B0F0)
- White receipt paper
- Gray text lines (representing receipt content)
- Yellow AI sparkle badge (representing AI processing)
- Zig-zag bottom edge (classic receipt perforation)

## Tools for Icon Design

### Free Tools
- [Figma](https://figma.com) - Professional design tool (free tier available)
- [Inkscape](https://inkscape.org) - Free SVG editor
- [GIMP](https://gimp.org) - Free image editor

### Icon Generators
- [favicon.io](https://favicon.io) - Generate favicons and icons
- [app-icon-generator](https://easyappicon.com) - Generate app icons for all platforms
- [cloudconvert.com](https://cloudconvert.com) - Convert between formats

## Testing Icons

After generating new icons:

1. **Windows:** Check `icon.ico` in File Explorer
2. **macOS:** Check `icon.icns` in Finder
3. **Electron:** Run `npm start` in desktop-app to see icon in app window
4. **Build:** Run `npm run build` to test in packaged app

## Troubleshooting

### ICO Generation Issues
- Ensure Pillow is installed: `pip install pillow`
- Check that PNG is 256x256 or larger

### ICNS Generation Issues
- ICNS requires macOS `iconutil` command
- On Windows/Linux, a PNG fallback is created instead
- Use online converters or run on macOS for proper ICNS

### SVG Rendering Issues
- Ensure cairosvg is installed: `pip install cairosvg`
- Check that SVG uses standard elements (no filters/effects)
- Try simplifying SVG if conversion fails

## Next Steps

1. ✅ Placeholder icons created
2. ⬜ Design custom branded icons
3. ⬜ Generate all platform formats
4. ⬜ Test icons in built application
5. ⬜ Update Electron builder config to use icons


## Desktop Entry Configuration
```desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Receipt Extractor
Comment=AI-powered receipt text extraction web application
Exec=/home/user/Web-and-Desktop-Apps/launch-receipt-app.sh
Icon=/home/user/Web-and-Desktop-Apps/desktop-app/assets/icon.png
Terminal=true
Categories=Utility;Office;
Keywords=receipt;ocr;extraction;ai;
StartupNotify=true
```


## Icon (SVG)
```svg
<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="512" height="512" rx="64" fill="#00B0F0"/>

  <!-- Receipt Paper -->
  <rect x="128" y="80" width="256" height="352" rx="8" fill="white"/>

  <!-- Receipt Lines -->
  <rect x="160" y="120" width="192" height="8" rx="4" fill="#E0E0E0"/>
  <rect x="160" y="148" width="160" height="8" rx="4" fill="#E0E0E0"/>
  <rect x="160" y="176" width="192" height="8" rx="4" fill="#E0E0E0"/>
  <rect x="160" y="204" width="128" height="8" rx="4" fill="#E0E0E0"/>
  <rect x="160" y="232" width="192" height="8" rx="4" fill="#E0E0E0"/>
  <rect x="160" y="260" width="160" height="8" rx="4" fill="#E0E0E0"/>

  <!-- Total Line (highlighted) -->
  <rect x="160" y="320" width="192" height="12" rx="6" fill="#00B0F0"/>

  <!-- AI Sparkle Icon -->
  <circle cx="368" cy="368" r="48" fill="#FFC107"/>
  <path d="M368,332 L376,356 L400,364 L376,372 L368,396 L360,372 L336,364 L360,356 Z" fill="white"/>

  <!-- Zig-zag bottom edge -->
  <path d="M128,432 L144,416 L160,432 L176,416 L192,432 L208,416 L224,432 L240,416 L256,432 L272,416 L288,432 L304,416 L320,432 L336,416 L352,432 L368,416 L384,432 L384,432 L128,432 Z" fill="white"/>
</svg>
```


## Python Utilities
```python
#!/usr/bin/env python3
import os,sys
from pathlib import Path
try:
 from PIL import Image
 import cairosvg
except ImportError:print("ERROR: Required packages not installed.");print("Please run: pip install pillow cairosvg");sys.exit(1)
def svg_to_png(svg_path,png_path,size):cairosvg.svg2png(url=svg_path,write_to=png_path,output_width=size,output_height=size);print(f"✓ Generated: {png_path} ({size}x{size})")
def create_ico(png_path,ico_path):
 img=Image.open(png_path)
 sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
 images=[]
 for size in sizes:resized=img.resize(size,Image.Resampling.LANCZOS);images.append(resized)
 images[0].save(ico_path,format='ICO',sizes=[img.size for img in images],append_images=images[1:])
 print(f"✓ Generated: {ico_path} (multi-resolution)")
def create_icns(png_path,icns_path):
 img=Image.open(png_path)
 if sys.platform=='darwin':
  import subprocess,tempfile
  with tempfile.TemporaryDirectory()as tmpdir:
   iconset=os.path.join(tmpdir,'icon.iconset')
   os.makedirs(iconset)
   sizes=[16,32,64,128,256,512]
   for size in sizes:
    resized=img.resize((size,size),Image.Resampling.LANCZOS)
    resized.save(os.path.join(iconset,f'icon_{size}x{size}.png'))
    if size<=256:resized_2x=img.resize((size*2,size*2),Image.Resampling.LANCZOS);resized_2x.save(os.path.join(iconset,f'icon_{size}x{size}@2x.png'))
   subprocess.run(['iconutil','-c','icns',iconset,'-o',icns_path])
  print(f"✓ Generated: {icns_path}")
 else:img.save(icns_path.replace('.icns','.png'));print(f"⚠ ICNS generation requires macOS. Created PNG fallback instead.");print(f"  Please run this script on macOS to generate proper .icns file.")
def main():
 assets_dir=Path(__file__).parent
 svg_path=assets_dir/'icon.svg'
 if not svg_path.exists():print(f"ERROR: {svg_path} not found!");sys.exit(1)
 print("Receipt Extractor - Icon Generator");print("="*50)
 png_path=assets_dir/'icon.png'
 svg_to_png(str(svg_path),str(png_path),512)
 ico_path=assets_dir/'icon.ico'
 create_ico(str(png_path),str(ico_path))
 icns_path=assets_dir/'icon.icns'
 create_icns(str(png_path),str(icns_path))
 linux_png_path=assets_dir/'icon-linux.png'
 img=Image.open(png_path)
 img.save(linux_png_path)
 print(f"✓ Generated: {linux_png_path} (512x512)");print("="*50);print("✓ Icon generation complete!");print("\nNext steps:");print("1. Review the generated icons");print("2. Replace icon.svg with your custom design if desired");print("3. Re-run this script to regenerate icons")
if __name__=='__main__':main()
import os,sys,json,logging
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from shared.models.model_manager import ModelManager
logging.basicConfig(level=logging.INFO,format='%(message)s')
logger=logging.getLogger(__name__)
if sys.platform=='win32':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
def main():
 if len(sys.argv)<2:print(json.dumps({'success':False,'error':'Usage: python process_receipt.py <image_path> [model_id]'}));sys.exit(1)
 image_path=sys.argv[1]
 model_id=sys.argv[2]if len(sys.argv)>2 else None
 if not os.path.exists(image_path):print(json.dumps({'success':False,'error':f'Image file not found: {image_path}'}));sys.exit(1)
 try:
  logger.info(f"Initializing model manager...")
  model_manager=ModelManager()
  if model_id:
   success=model_manager.select_model(model_id)
   if not success:print(json.dumps({'success':False,'error':f'Invalid model ID: {model_id}'}));sys.exit(1)
  else:model_id=model_manager.get_default_model();model_manager.select_model(model_id)
  logger.info(f"Using model: {model_id}")
  processor=model_manager.get_processor(model_id)
  logger.info(f"Processing image: {image_path}")
  result=processor.extract(image_path)
  print(json.dumps(result.to_dict()))
 except Exception as e:logger.error(f"Error: {e}",exc_info=True);print(json.dumps({'success':False,'error':str(e)}));sys.exit(1)
if __name__=='__main__':main()
```
