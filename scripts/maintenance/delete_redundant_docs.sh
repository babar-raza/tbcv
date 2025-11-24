#!/bin/bash
# Script to delete redundant documentation files from docs/
# Content has been incorporated into new docs/ files

echo "Deleting redundant documentation files from docs/..."
echo "===================================================="

# Historical fix reports
rm -v ENDPOINT_AUDIT.md
rm -v FIX_REPORT.md
rm -v FIXES_APPLIED.txt
rm -v FIXES_SUMMARY.txt
rm -v LATEST_FIXES.txt
rm -v README_FIXES.md
rm -v RUN_TESTS.txt

# Redundant guides (covered in new docs/)
rm -v TEST_SUITE_README.md
rm -v QUICKSTART.md
rm -v README.md

# Python files that don't belong in docs/
rm -v __init__.py
rm -v __main__.py

# Old versions now replaced by new docs
rm -v agents_and_workflows.md  # Split into agents.md + workflows.md

echo ""
echo "===================================================="
echo "Deletion complete!"
echo ""
echo "KEPT (current documentation):"
echo "  - agents.md (NEW - comprehensive agent reference)"
echo "  - workflows.md (NEW - complete workflow docs)"
echo "  - troubleshooting.md (NEW - practical troubleshooting)"
echo "  - architecture.md (to be updated)"
echo "  - api_and_web_ui.md (to be split into api_reference.md + web_dashboard.md)"
echo "  - cli_usage.md (to be updated with recommendation commands)"
echo "  - configuration.md (to be verified)"
echo "  - deployment.md (to be verified)"
echo "  - testing.md (to be verified)"
echo "  - truth_store_and_plugins.md (to be renamed to truth_store.md)"
echo "  - CHANGELOG.md (version history)"
echo "  - history_and_backlog.md (historical context)"
echo ""
echo "Files deleted: 13"
