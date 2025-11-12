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
