# Quick Start: Autonomous MCP Migration Execution

**Last Updated**: 2025-11-30
**Status**: Ready to Execute

---

## 🚀 One-Command Execution

To start the complete autonomous migration:

```bash
# Execute everything in one command
bash scripts/start_autonomous_execution.sh
```

This will:
- ✅ Execute all 18 tasks in optimal order
- ✅ Run 4 parallel agents where possible
- ✅ Validate each phase before proceeding
- ✅ Create PRs automatically
- ✅ Run tests continuously
- ✅ Complete in 6-9 weeks

---

## 📋 Prerequisites

Before running, ensure you have:

```bash
# 1. Git repository access
git remote get-url origin  # Should show your repo

# 2. GitHub CLI installed
gh --version  # Should show v2.0+

# 3. Python environment
python --version  # Should show 3.9+
pip install -r requirements.txt

# 4. Clean working directory
git status  # Should show "nothing to commit, working tree clean"
```

---

## 🎯 Manual Execution (Task by Task)

If you prefer to execute tasks manually:

### Step 1: Execute a Single Task

```bash
# Execute TASK-001 (Foundation)
bash scripts/autonomous_executor.sh TASK-001

# Wait for PR to be merged (or merge manually)
gh pr list

# Merge the PR
gh pr merge <PR-number> --squash
```

### Step 2: Check Progress

```bash
# View progress dashboard
python scripts/mcp_progress_dashboard.py
```

### Step 3: Validate Phase

```bash
# After completing Phase 1
bash scripts/validate_phase1.sh

# After completing Phase 2
bash scripts/validate_phase2.sh
```

---

## 📊 Monitoring Progress

### Real-Time Dashboard

```bash
# Watch progress in real-time
watch -n 60 python scripts/mcp_progress_dashboard.py
```

### Check Task Status

```bash
# List all open PRs for MCP migration
gh pr list --label "mcp-migration"

# List all merged PRs
gh pr list --state merged --label "mcp-migration"
```

### View Test Results

```bash
# Run tests for specific task
pytest tests/svc/test_mcp_*.py -v

# Check coverage
pytest --cov=svc --cov=api --cov=cli --cov-report=html
open htmlcov/index.html
```

---

## 🔧 Troubleshooting

### If a Task Fails

```bash
# Check the error
git log -1

# Rollback the task
git reset --hard HEAD~1

# Fix the issue
# Edit the relevant files

# Re-run the task
bash scripts/autonomous_executor.sh TASK-XXX
```

### If Tests Fail

```bash
# Run tests in verbose mode
pytest tests/svc/test_failing.py -vv --tb=long

# Check logs
tail -f data/logs/tbcv.log

# Fix and re-run
git add .
git commit --amend --no-edit
git push --force-with-lease
```

### If PR Won't Merge

```bash
# Check PR status
gh pr view <PR-number>

# View CI checks
gh pr checks <PR-number>

# Fix conflicts
git fetch origin main
git rebase origin/main

# Push update
git push --force-with-lease
```

---

## ⚡ Speed Up Execution

### Use More Parallel Agents

Edit `scripts/start_autonomous_execution.sh` and increase parallelization:

```bash
# Instead of 4 parallel tracks, run all Phase 2 tasks in parallel:
for task in TASK-004 TASK-005 TASK-006 TASK-007 TASK-008 TASK-009 TASK-010; do
    bash scripts/autonomous_executor.sh "$task" &
done
wait
```

### Auto-Merge PRs

Enable auto-merge for PRs that pass CI:

```bash
# In autonomous_executor.sh, add --auto-merge flag
gh pr create --auto-merge --auto-merge-method squash
```

### Skip Manual Validation

If confident in automation:

```bash
# Comment out validation gates in start_autonomous_execution.sh
# bash scripts/validate_phase1.sh  # <- Comment this
```

---

## 📈 Expected Timeline

### With Default Settings (Sequential where dependencies exist)
- **Phase 1**: 8 days (sequential)
- **Phase 2**: 9 days (4 parallel tracks)
- **Phase 3**: 5 days (2 parallel tracks)
- **Phase 4**: 4 days (2 parallel tracks)
- **Phase 5**: 5 days (sequential)
- **Total**: ~31 days (6-7 weeks)

### With Maximum Parallelization
- **Phase 1**: 8 days (must be sequential)
- **Phase 2**: 5 days (7 tasks in parallel)
- **Phase 3**: 3 days (4 tasks in parallel)
- **Phase 4**: 4 days (2 tasks in parallel)
- **Phase 5**: 5 days (must be sequential)
- **Total**: ~25 days (5 weeks)

---

## ✅ Success Indicators

You'll know it's working when:

1. **PRs Being Created**
   ```bash
   gh pr list
   # Should show TASK-XXX PRs
   ```

2. **Tests Passing**
   ```bash
   gh pr checks <PR-number>
   # All checks should be green
   ```

3. **Coverage Increasing**
   ```bash
   python scripts/mcp_progress_dashboard.py
   # Method count should increase
   ```

4. **No Errors**
   ```bash
   git log --oneline
   # All commits should be successful
   ```

---

## 🎉 Completion

When all tasks are complete:

```bash
# Final validation
bash scripts/validate_final.sh

# Should output:
# ✅✅✅ ALL PHASES COMPLETE - PRODUCTION READY ✅✅✅

# Tag release
git tag -a v2.0.0-mcp -m "MCP-first architecture complete"
git push origin v2.0.0-mcp

# Celebrate!
echo "🎉 MCP Migration Complete! 🎉"
```

---

## 📚 Documentation References

- **Full Plan**: [plans/comms.md](comms.md)
- **Detailed Tasks**: [plans/tasks/](tasks/)
- **Production Code**: [plans/IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- **Autonomous Execution**: [plans/AUTONOMOUS_EXECUTION_PLAN.md](AUTONOMOUS_EXECUTION_PLAN.md)
- **Current Analysis**: [reports/coms.md](../reports/coms.md)

---

## 🆘 Getting Help

### Check Documentation First
1. Review [AUTONOMOUS_EXECUTION_PLAN.md](AUTONOMOUS_EXECUTION_PLAN.md)
2. Check [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for code examples
3. Look at task card: `plans/tasks/TASK-XXX.md`

### Debug Issues
```bash
# Check logs
tail -f data/logs/tbcv.log

# Check git status
git status

# Check PR status
gh pr list

# Check test output
pytest -vv --tb=long
```

### Report Bugs
```bash
# Create issue
gh issue create --title "TASK-XXX: [problem]" --body "[details]"
```

---

**Ready to Start?**

```bash
# Let's go!
bash scripts/start_autonomous_execution.sh
```

---

**Good Luck! The autonomous agents are ready to work for you! 🤖**
