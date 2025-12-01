# Web Application Frontend

<!--
================================================================================
CIRCULAR EXCHANGE FRAMEWORK - Module Documentation
================================================================================
Module ID: web-app.frontend
Description: Browser-based interface for receipt extraction
Dependencies: [web-app.backend.app, shared.models.model_manager]
Exports: [index.html, styles.css, app.js]

Note: This frontend integrates with the Circular Exchange Framework through
the backend API. Configuration changes are reflected when models are loaded
or when extraction parameters are updated via API calls.
================================================================================
-->

Browser-based interface for receipt extraction.

## Quick Start

### Option 1: Direct File Open
Simply open `index.html` in your browser.

### Option 2: HTTP Server (Recommended)
```bash
# Python 3
python -m http.server 8000

# Node.js
npx http-server -p 8000
```

Then navigate to `http://localhost:8000`

## Configuration

Edit `js/app.js` to change API endpoint:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

## Features

- Model selection and switching
- Image upload (drag & drop supported)
- Real-time extraction
- Export to JSON, CSV, TXT
- Responsive design
