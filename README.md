# Receipt Extractor - SIMPLIFIED VERSION

🎉 **STREAMLINED** - Only working public models included!

## ✅ What's Changed

1. **Only public models** - No authentication required for any model
2. **SROIE Donut is default** - Reliable Donut model that always works
3. **Removed auth-required models** - AdamCodd and PaliGemma removed
4. **Guaranteed to work** - All remaining models work out-of-the-box

## 🚀 Quick Start

**Windows:**
```powershell
.\dev.bat setup
npm start
```

**Linux/Mac:**
```bash
./dev.sh setup
npm start
```

## ⚡ Commands

**Windows:**
- `.\dev.bat setup` - Install everything
- `.\dev.bat test` - Test Python
- `.\dev.bat extract img.jpg` - Test extraction
- `npm start` - Run app
- `npm run build` - Build app

**Linux/Mac:**
- `./dev.sh setup` - Install everything
- `./dev.sh test` - Test Python
- `./dev.sh extract img.jpg` - Test extraction
- `npm start` - Run app
- `npm run build` - Build app

## 🎯 Available Models

All models are public and work without authentication:

- **SROIE Donut** ✅ DEFAULT - Donut model, 4 fields (store, date, total, address)
- **Florence-2** ✅ RECOMMENDED - Best results, comprehensive extraction
- **OCR** ⚡ FAST - Requires Tesseract installed

## 💡 Troubleshooting

**Empty extraction results?**
- ✅ Use SROIE (default Donut model) or Florence-2
- Both work reliably without authentication

**PowerShell error?**
- Use `.\dev.bat` not `dev.bat`

**Python not found?**
- Install Python 3.8+
- Check "Add to PATH"
- Restart terminal

**First extraction slow?**
- Model downloading (~500MB-1GB, one-time)
- Wait 2-5 minutes
- After that: fast!

## 📊 What Each Model Does

| Model | Items | Store | Total | Speed | Auth |
|-------|-------|-------|-------|-------|------|
| **SROIE Donut** | ❌ | ✅ | ✅ | Fast | No |
| **Florence-2** | ✅ | ✅ | ✅ | Medium | No |
| OCR | ✅ | ✅ | ✅ | Fast | No* |

*OCR requires Tesseract installed

## License

MIT
