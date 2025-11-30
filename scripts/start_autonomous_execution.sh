#!/bin/bash
# Start Autonomous Execution
# Kicks off the entire MCP migration with parallel agents

echo "=================================================="
echo "STARTING AUTONOMOUS MCP MIGRATION"
echo "=================================================="
echo "Date: $(date)"
echo "Repository: $(git remote get-url origin)"
echo ""

# Verify prerequisites
echo "Checking prerequisites..."

# Check git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Check if on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Warning: Not on main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes detected. Please commit or stash them."
    exit 1
fi

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) not installed"
    echo "Install: https://cli.github.com/"
    exit 1
fi

# Check pytest
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not installed"
    echo "Install: pip install pytest"
    exit 1
fi

echo "✓ All prerequisites met"
echo ""

# Pull latest
echo "Pulling latest changes..."
git pull origin main

# Show current status
echo ""
echo "Current MCP Status:"
python scripts/mcp_progress_dashboard.py 2>/dev/null || echo "Dashboard not yet available"

echo ""
echo "=================================================="
echo "PHASE 1: FOUNDATION (Sequential Execution)"
echo "=================================================="
echo ""

# Execute Phase 1 tasks sequentially
for task in TASK-001 TASK-002 TASK-003; do
    echo "Starting $task..."
    bash scripts/autonomous_executor.sh "$task"

    # Wait for PR to be created and merged
    echo "Waiting for $task PR to be merged..."
    sleep 10

    # Check if merged
    while ! gh pr list --state merged --search "$task" --limit 1 | grep -q "$task"; do
        echo "Waiting for $task to be merged..."
        sleep 30
    done

    echo "✓ $task complete and merged"
    echo ""
done

echo "=================================================="
echo "PHASE 1 COMPLETE - VALIDATING"
echo "=================================================="

# Run Phase 1 validation
bash scripts/validate_phase1.sh

echo ""
echo "=================================================="
echo "PHASE 2: CORE OPERATIONS (Parallel Execution)"
echo "=================================================="
echo ""

# Start Phase 2 tasks in parallel
echo "Launching parallel agents for Phase 2..."

# Track 1: AGENT-VAL
(
    bash scripts/autonomous_executor.sh TASK-004
    bash scripts/autonomous_executor.sh TASK-007
) &
PID_TRACK1=$!

# Track 2: AGENT-WF
(
    bash scripts/autonomous_executor.sh TASK-005
    bash scripts/autonomous_executor.sh TASK-008
) &
PID_TRACK2=$!

# Track 3: AGENT-ENH
(
    bash scripts/autonomous_executor.sh TASK-006
    bash scripts/autonomous_executor.sh TASK-009
) &
PID_TRACK3=$!

# Track 4: AGENT-ADM
bash scripts/autonomous_executor.sh TASK-010 &
PID_TRACK4=$!

# Wait for all tracks to complete
echo "Waiting for all Phase 2 tasks to complete..."
wait $PID_TRACK1 $PID_TRACK2 $PID_TRACK3 $PID_TRACK4

echo ""
echo "=================================================="
echo "PHASE 2 COMPLETE - VALIDATING"
echo "=================================================="

# Run Phase 2 validation
bash scripts/validate_phase2.sh

echo ""
echo "=================================================="
echo "PHASE 3: ADVANCED FEATURES (Parallel Execution)"
echo "=================================================="
echo ""

# Start Phase 3 tasks in parallel
(
    bash scripts/autonomous_executor.sh TASK-011
    bash scripts/autonomous_executor.sh TASK-012
) &
PID_TRACK5=$!

(
    bash scripts/autonomous_executor.sh TASK-013
    bash scripts/autonomous_executor.sh TASK-014
) &
PID_TRACK6=$!

wait $PID_TRACK5 $PID_TRACK6

echo ""
echo "=================================================="
echo "PHASE 3 COMPLETE - VALIDATING"
echo "=================================================="

bash scripts/validate_phase3.sh

echo ""
echo "=================================================="
echo "PHASE 4: INTEGRATION (Parallel Execution)"
echo "=================================================="
echo ""

# Start Phase 4 tasks in parallel
bash scripts/autonomous_executor.sh TASK-015 &
PID_CLI=$!

bash scripts/autonomous_executor.sh TASK-016 &
PID_API=$!

wait $PID_CLI $PID_API

echo ""
echo "=================================================="
echo "PHASE 4 COMPLETE - VALIDATING"
echo "=================================================="

bash scripts/validate_phase4.sh

echo ""
echo "=================================================="
echo "PHASE 5: ENFORCEMENT (Sequential Execution)"
echo "=================================================="
echo ""

# Execute Phase 5 sequentially
bash scripts/autonomous_executor.sh TASK-017
bash scripts/autonomous_executor.sh TASK-018

echo ""
echo "=================================================="
echo "FINAL VALIDATION"
echo "=================================================="

bash scripts/validate_final.sh

echo ""
echo "=================================================="
echo "🎉 AUTONOMOUS EXECUTION COMPLETE! 🎉"
echo "=================================================="
echo ""
echo "Migration Summary:"
python scripts/mcp_progress_dashboard.py

echo ""
echo "Next Steps:"
echo "1. Review all merged PRs"
echo "2. Run manual regression tests"
echo "3. Update documentation"
echo "4. Deploy to production"
echo ""
echo "Completion Time: $(date)"
echo "=================================================="
