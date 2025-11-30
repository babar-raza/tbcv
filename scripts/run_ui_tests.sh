#!/bin/bash
# =============================================================================
# TBCV Playwright UI Tests Runner (Unix/Linux/macOS)
# =============================================================================

set -e

echo ""
echo "============================================"
echo "TBCV Playwright UI Tests"
echo "============================================"
echo ""

# Check if Playwright is installed
if ! python -c "import playwright" 2>/dev/null; then
    echo "[INFO] Installing Playwright..."
    pip install playwright pytest-playwright
fi

# Check if browsers are installed
echo "[INFO] Checking Playwright browsers..."
playwright install chromium

echo ""
echo "[INFO] Running UI tests..."
echo ""

# Run tests with all arguments passed to this script
pytest tests/ui/ -v --browser chromium "$@"

TEST_EXIT=$?

echo ""
if [ $TEST_EXIT -eq 0 ]; then
    echo "============================================"
    echo "[SUCCESS] All UI tests passed!"
    echo "============================================"
else
    echo "============================================"
    echo "[FAILED] Some UI tests failed"
    echo "============================================"
fi

exit $TEST_EXIT
