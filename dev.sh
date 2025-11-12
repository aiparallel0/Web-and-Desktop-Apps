#!/bin/bash
# All-in-one setup and test script

cmd=$1

case "$cmd" in
  setup)
    echo "Installing dependencies..."
    pip3 install torch transformers pillow opencv-python numpy pytesseract 2>/dev/null || pip install torch transformers pillow opencv-python numpy pytesseract
    npm install
    echo "✓ Setup complete"
    ;;
  test)
    echo "Testing Python..."
    python3 -c "import torch, transformers, PIL, cv2, numpy; print('✓ Python OK')" 2>/dev/null || python -c "import torch, transformers, PIL, cv2, numpy; print('✓ Python OK')"
    ;;
  extract)
    img=$2
    model=${3:-sroie}
    if [ -z "$img" ]; then
      echo "Usage: ./dev.sh extract <image> [model]"
      echo "Models: ocr, sroie, florence2"
      exit 1
    fi
    if [ "$model" = "ocr" ]; then
      python3 extract_ocr.py "$img" 2>/dev/null || python extract_ocr.py "$img"
    else
      python3 extract_donut.py "$img" --model "$model" 2>/dev/null || python extract_donut.py "$img" --model "$model"
    fi
    ;;
  models)
    echo "Downloading models..."
    python3 test.py --download 2>/dev/null || python test.py --download
    ;;
  *)
    echo "Receipt Extractor - Dev Script"
    echo ""
    echo "Usage:"
    echo "  ./dev.sh setup              Install all dependencies"
    echo "  ./dev.sh test               Test Python environment"
    echo "  ./dev.sh extract <img> [model]   Test extraction"
    echo "  ./dev.sh models             Download models"
    echo ""
    echo "Development:"
    echo "  npm start                   Run app"
    echo "  npm run build               Build app"
    ;;
esac
