#!/bin/bash
# Script to delete redundant documentation files
# Content has been incorporated into new README.md and docs/

echo "Deleting redundant documentation files from root..."
echo "=================================================="

# Historical analysis and bug reports (content covered in new docs)
rm -v analysis.md
rm -v EXECUTIVE_SUMMARY.md
rm -v TBCV_SYSTEM_ANALYSIS.md
rm -v QUICK_FIX_ENHANCEMENT_BUG.md

# Historical fix reports (content is historical, covered in CHANGELOG.md)
rm -v ENDPOINT_AUDIT.md
rm -v FIX_REPORT.md
rm -v FIXES_APPLIED.md
rm -v README_FIXES.md
rm -v FIXES_APPLIED.txt
rm -v FIXES_SUMMARY.txt
rm -v LATEST_FIXES.txt
rm -v IMPLEMENTATION_PLAN.txt

# Redundant setup/testing guides (covered in new README.md and docs/)
rm -v SETUP_GUIDE.md
rm -v QUICKSTART.md
rm -v TEST_SUITE_README.md
rm -v TESTING.md
rm -v RUN_TESTS.txt

# Old README (replaced by new README.md)
rm -v README_original.md

echo ""
echo "=================================================="
echo "Deletion complete!"
echo ""
echo "KEPT (valuable reference):"
echo "  - README.md (NEW - comprehensive)"
echo "  - CHANGELOG.md (version history)"
echo "  - requirements.txt (Python dependencies)"
echo "  - requirements.md (formal specification)"
echo "  - VERSION.txt (version info)"
echo "  - GENERIC_VALIDATION_ROADMAP.md (future planning)"
echo "  - taskcards.md (implementation specs)"
echo "  - requirements_mapping.md (requirements mapping)"
echo "  - CLEANUP_INSTRUCTIONS.md (cleanup guide)"
echo "  - DOCUMENTATION_STATUS.md (doc progress tracker)"
echo "  - NEW_DOCS_SUMMARY.md (rewrite summary)"
echo ""
echo "Files deleted: 20"
