# Quick Start Guide - Receipt Extractor Web App

## 🚀 Easiest Method - Use the Startup Script

### Windows:
1. Double-click `start-web-app.bat`
2. The browser will automatically open to http://localhost:3000
3. Press any key in the script window to stop both servers when done

### Linux/Mac:
1. Open terminal in this directory
2. Run: `chmod +x start-web-app.sh` (first time only)
3. Run: `./start-web-app.sh`
4. The browser will automatically open to http://localhost:3000
5. Press Ctrl+C to stop both servers when done

---

## 📋 Manual Method

If the script doesn't work, follow these steps:

### Step 1: Start Backend (Terminal 1)
```powershell
cd C:\Users\User\desktop\Web-and-Desktop-Apps
cd web-app/backend
python app.py
```
Backend will run on: http://localhost:5000

### Step 2: Start Frontend (Terminal 2 - New Window)
```powershell
cd C:\Users\User\desktop\Web-and-Desktop-Apps
cd web-app/frontend
python -m http.server 3000
```
Frontend will run on: http://localhost:3000

### Step 3: Open Browser
Navigate to: **http://localhost:3000**

---

## ⚠️ Troubleshooting

### "SSL-enabled server port" Error
This means you're accessing a different web server (Apache/IIS) instead of the Python server.

**Solutions:**
1. Make sure you're using `http://localhost:3000` (not port 80, 8000, or any other port)
2. Stop Apache/IIS if running:
   - Windows: Services → Stop "Apache" or "World Wide Web Publishing Service"
3. Use the startup script which uses port 3000 (less likely to conflict)

### "Address already in use" Error
Another process is using the port.

**Solution - Change Frontend Port:**
```powershell
# Instead of port 3000, try 3001, 8080, 8888, etc.
python -m http.server 8080
# Then open http://localhost:8080
```

### Backend Not Starting
**Check Python is installed:**
```powershell
python --version
```

**Install requirements:**
```powershell
cd web-app/backend
pip install -r requirements.txt
```

### Can't Find the Directory
**Make sure you're in the right location:**
```powershell
# From Desktop
cd Web-and-Desktop-Apps
dir  # Should show: web-app, desktop-app, shared, etc.
```

---

## 🎯 Using the Application

1. **Select a Model**: Choose from SROIE Donut, CORD Donut, Florence-2, or Tesseract OCR
2. **Upload Receipt**: Click or drag-and-drop a receipt image (JPG, PNG, BMP, TIFF)
3. **Extract Data**: Click "Extract Receipt Data" button
4. **View Results**: See extracted store info, date, total, and line items
5. **Export**: Download results as JSON, CSV, or TXT

---

## 🌐 Accessing URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend (Web UI)** | http://localhost:3000 | Use this to access the app |
| **Backend API** | http://localhost:5000 | API runs here (don't access directly) |
| **API Health Check** | http://localhost:5000/api/health | Test if API is running |
| **Available Models** | http://localhost:5000/api/models | List available AI models |

---

## ❌ Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| http://[::]:3000 | http://localhost:3000 |
| https://localhost:3000 | http://localhost:3000 (no 's') |
| http://localhost (no port) | http://localhost:3000 |
| Running from wrong directory | cd to Web-and-Desktop-Apps first |

---

## 📞 Still Having Issues?

1. **Check both servers are running** - You should see Flask output in backend terminal
2. **Try a different port** - Use `python -m http.server 8080` and access http://localhost:8080
3. **Check firewall** - Allow Python through Windows Firewall
4. **Restart terminals** - Close all terminals and start fresh
5. **Reboot** - Sometimes Windows needs a restart to release ports

---

## 🔍 Quick Tests

**Test Backend is Running:**
Open browser to: http://localhost:5000/api/health

Should show:
```json
{
  "status": "healthy",
  "service": "receipt-extraction-api"
}
```

**Test Frontend is Running:**
Open browser to: http://localhost:3000

Should show the Receipt Extractor web interface.
