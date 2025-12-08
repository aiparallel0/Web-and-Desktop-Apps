#!/bin/bash
# Repository Analysis Runner
# Convenience script to run repository analysis from anywhere

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🔍 Repository Screener${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${YELLOW}❌ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if the screener script exists
if [ ! -f "$REPO_ROOT/tools/scripts/repo_screener.py" ]; then
    echo -e "${YELLOW}❌ Screener script not found at: $REPO_ROOT/tools/scripts/repo_screener.py${NC}"
    exit 1
fi

# Change to repository root
cd "$REPO_ROOT" || exit 1

# Run the screener
echo -e "${GREEN}📊 Running repository analysis...${NC}"
echo ""

python tools/scripts/repo_screener.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✅ Analysis Complete!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo -e "${GREEN}📄 Reports generated:${NC}"
    echo -e "   - REPOSITORY_ANALYSIS.md ($(wc -l < REPOSITORY_ANALYSIS.md) lines)"
    echo -e "   - repository_analysis.json ($(wc -l < repository_analysis.json) lines)"
    echo ""
    echo -e "${GREEN}📖 View the report:${NC}"
    echo -e "   cat REPOSITORY_ANALYSIS.md | less"
    echo -e "   code REPOSITORY_ANALYSIS.md"
    echo ""
    echo -e "${GREEN}📚 Documentation:${NC}"
    echo -e "   - Quick Reference: REPOSITORY_SCREENER_QUICK_REF.md"
    echo -e "   - Full Docs: docs/REPOSITORY_SCREENER.md"
    echo ""
else
    echo ""
    echo -e "${YELLOW}❌ Analysis failed. Check the error messages above.${NC}"
    exit 1
fi
