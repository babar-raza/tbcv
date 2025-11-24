# TBCV Validator Migration - Autonomous Implementation Guide

**Purpose**: This document is the SINGLE ENTRY POINT for autonomous implementation of the validator architecture migration.

**Target Audience**: AI assistant or developer implementing the migration autonomously without human intervention between steps.

**Status**: Ready for Implementation
**Priority**: P0 - Production Critical
**Timeline**: 8-10 weeks (can be accelerated with continuous work)

---

## Mission Statement

**Implement the complete validator architecture migration** from monolithic ContentValidatorAgent to modular validator agents, following the phased rollout plan with backward compatibility and zero downtime.

**Success Criteria**: All 8 validators migrated, 100% traffic on new architecture, all tests passing, production stable.

**Autonomy Level**: FULL - Implement all phases without waiting for approval between steps. Only stop if critical errors occur that cannot be auto-resolved.

---

## Prerequisites Checklist

Before starting, verify:
- [ ] Current working directory: `/path/to/tbcv`
- [ ] Git repository initialized and clean
- [ ] Python environment activated
- [ ] All current tests passing: `python -m pytest tests/ -v`
- [ ] Database accessible: `tbcv.db` exists
- [ ] Config files present: `config/main.yaml`, `config/seo.yaml`, etc.
- [ ] Server can start: `python main.py --mode api --port 8000` (test and stop)

**If any prerequisite fails**: Document the issue and attempt to fix autonomously. Only escalate if fix is unclear.

---

## Implementation Order (STRICT SEQUENCE)

**CRITICAL**: Follow this order exactly. Do not skip steps or implement out of sequence.

### Phase 0: Preparation (Week 0)
**Estimated Time**: 2-4 hours
**Can Skip If**: Pressed for time and willing to accept slightly higher risk

```
1. Create feature flag infrastructure
   └─> File: core/feature_flags.py
   └─> File: config/features.yaml
   └─> Tests: tests/test_feature_flags.py

2. Create test framework
   └─> Directory: tests/validators/
   └─> Files: tests/validators/__init__.py, fixtures/
   └─> Run: python -m pytest tests/validators/ -v

3. Capture baseline metrics
   └─> Run: python -m pytest --cov=agents/content_validator tests/
   └─> Save: baseline_metrics.json
```

### Phase 1: Foundation (Week 1-2)
**Estimated Time**: 8-12 hours
**CANNOT SKIP**: This is the foundation for everything

```
1. Create BaseValidatorAgent
   └─> File: agents/validators/__init__.py
   └─> File: agents/validators/base_validator.py
   └─> Tests: tests/validators/test_base_validator.py
   └─> Verify: Can instantiate base class

2. Implement SeoValidatorAgent (FIRST VALIDATOR - PROOF OF CONCEPT)
   └─> File: agents/validators/seo_validator.py
   └─> Tests: tests/validators/test_seo_validator.py
   └─> Verify: Tests passing, SEO validation works

3. Implement ValidatorRouter
   └─> File: agents/validators/router.py
   └─> Tests: tests/validators/test_validator_router.py
   └─> Verify: Routing works, fallback works

4. Integrate with Orchestrator
   └─> File: agents/orchestrator.py (MODIFY)
   └─> Add: ValidatorRouter integration
   └─> Verify: Orchestrator can use router, backward compatible

5. Register SeoValidator
   └─> File: api/server.py (MODIFY)
   └─> Add: SeoValidatorAgent registration
   └─> Verify: Agent shows in /registry/agents

6. Add API endpoint
   └─> File: api/server.py (MODIFY)
   └─> Add: GET /api/validators/available
   └─> Verify: Returns validator list

7. Run all tests
   └─> Run: python -m pytest tests/ -v --cov
   └─> Verify: All tests pass, coverage >85%
```

### Phase 2: Core Validators (Week 3-5)
**Estimated Time**: 12-18 hours
**CRITICAL**: Implement each validator completely before moving to next

```
For EACH validator in order:
  1. YamlValidatorAgent
  2. MarkdownValidatorAgent
  3. CodeValidatorAgent
  4. LinkValidatorAgent
  5. StructureValidatorAgent
  6. TruthValidatorAgent

For each validator:
  1. Create validator file
     └─> File: agents/validators/{name}_validator.py
     └─> Code: Copy template, implement validate()

  2. Create tests
     └─> File: tests/validators/test_{name}_validator.py
     └─> Tests: valid content, invalid content, edge cases

  3. Register agent
     └─> File: api/server.py (MODIFY)
     └─> Add: Registration in lifespan()

  4. Add to config
     └─> File: config/main.yaml (MODIFY)
     └─> Add: validators.{name}.enabled: true

  5. Verify
     └─> Run: python -m pytest tests/validators/test_{name}_validator.py -v
     └─> Run: curl http://localhost:8000/api/validators/available
     └─> Verify: Validator appears in list

  6. Update ValidatorRouter map
     └─> File: agents/validators/router.py (MODIFY)
     └─> Add: Mapping in _build_validator_map()
```

### Phase 3: Integration & Testing (Week 6)
**Estimated Time**: 6-8 hours
**CRITICAL**: Do not deploy without these tests passing

```
1. Parity Testing
   └─> File: tests/validators/test_parity.py
   └─> Test: New validators match legacy results
   └─> Verify: 95%+ parity on sample content

2. Integration Testing
   └─> File: tests/integration/test_validator_pipeline.py
   └─> Test: Full end-to-end validation
   └─> Verify: All validation types work through API

3. Load Testing
   └─> File: tests/performance/test_load.py
   └─> Test: 100 concurrent validations
   └─> Verify: No memory leaks, performance acceptable

4. Update UI (Dynamic Discovery)
   └─> File: templates/validations_list.html (MODIFY)
   └─> Add: Dynamic validator loading via API
   └─> Remove: Hardcoded checkboxes
   └─> Verify: UI shows all available validators
```

### Phase 4: Configuration & Deployment Prep (Week 7)
**Estimated Time**: 4-6 hours
**CRITICAL**: Production deployment preparation

```
1. Enable fuzzy_detector
   └─> File: config/main.yaml (MODIFY)
   └─> Change: fuzzy_detector.enabled: false → true
   └─> Verify: Fuzzy detector registers

2. Configure feature flags
   └─> File: config/features.yaml
   └─> Set: All validators to 0% initially
   └─> Verify: Feature flags work

3. Create deployment scripts
   └─> File: scripts/deploy.sh
   └─> File: scripts/rollback.sh
   └─> File: scripts/smoke_test.sh

4. Update documentation
   └─> File: README.md (MODIFY)
   └─> File: docs/validators.md (NEW)
   └─> Add: Migration notes, new validator guide
```

### Phase 5: Gradual Rollout (Week 7-8)
**Estimated Time**: Monitor over 1-2 weeks
**DEPLOYMENT PHASE**: Real production changes

```
IF DEPLOYING TO PRODUCTION:

  Week 7 - Day 1: Enable 10% traffic
    └─> File: config/features.yaml (MODIFY)
    └─> Set: All validators to 10%
    └─> Deploy: Run deployment script
    └─> Monitor: 24 hours
    └─> Rollback if: Errors > 1%, latency > 2x

  Week 7 - Day 3: Increase to 50%
    └─> Set: All validators to 50%
    └─> Monitor: 24 hours

  Week 7 - Day 5: Increase to 100%
    └─> Set: All validators to 100%
    └─> Monitor: 48 hours

  Week 8: Stabilization
    └─> Monitor metrics
    └─> Fix any issues
    └─> Document issues found

ELSE (DEVELOPMENT):

  Set all validators to 100% immediately
  └─> File: config/features.yaml
  └─> Set: All to 100%
  └─> Test: Full validation pipeline
```

### Phase 6: Cleanup (Week 9-10, OPTIONAL)
**Estimated Time**: 4-6 hours
**OPTIONAL**: Can be deferred

```
1. Add deprecation warnings
   └─> File: agents/content_validator.py (MODIFY)
   └─> Add: Deprecation warnings in handle_validate_content()

2. Create future validator template
   └─> File: agents/validators/TEMPLATE_validator.py
   └─> Document: How to add new validators

3. Performance tuning
   └─> Implement: Parallel execution in router
   └─> Test: Load tests show improvement

4. Final documentation
   └─> Update: All docs
   └─> Create: Migration completion report
```

---

## Key Documents Reference

**READ IN THIS ORDER**:

1. **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** (SKIM - 5 min)
   - Understand the "why" and high-level approach
   - Know the success criteria
   - Understand risk levels

2. **[IMPLEMENTATION_PLAN_NEW_AGENTS.md](../IMPLEMENTATION_PLAN_NEW_AGENTS.md)** (READ CAREFULLY - 30 min)
   - **THIS IS YOUR CODE REFERENCE**
   - Contains complete implementations:
     - BaseValidatorAgent (copy this exactly)
     - SeoValidatorAgent (copy this exactly)
     - YamlValidatorAgent (use as template)
     - ValidatorRouter (copy this exactly)
   - Contains configuration examples
   - Contains test examples

3. **[MIGRATION_PLAN.md](MIGRATION_PLAN.md)** (REFERENCE AS NEEDED)
   - Week-by-week details
   - Testing procedures
   - Deployment procedures
   - Rollback procedures

4. **[ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md)** (REFERENCE IF UNCLEAR)
   - Architectural decisions
   - Why things are designed this way
   - Production considerations

---

## Code Templates Location

**All ready-to-use code is in**: `IMPLEMENTATION_PLAN_NEW_AGENTS.md`

**Copy these exactly**:
- BaseValidatorAgent (lines 15-190)
- SeoValidatorAgent (lines 200-600)
- ValidatorRouter (not in doc, implement based on MIGRATION_PLAN.md)

**Use as templates**:
- YamlValidatorAgent (modify for other validators)
- Test structure (adapt for each validator)

---

## Autonomous Implementation Rules

### 1. Error Handling
```
IF test fails:
  1. Analyze error
  2. Fix code
  3. Rerun test
  4. If fails 3 times: Document and move to next (mark TODO)
  5. Return to fix later

IF import fails:
  1. Check if file exists
  2. Check import path
  3. Fix or create file
  4. Continue

IF unclear requirement:
  1. Make reasonable assumption based on architecture
  2. Document assumption in code comments
  3. Continue
```

### 2. Testing Protocol
```
AFTER each validator implementation:
  1. Run: python -m pytest tests/validators/test_{name}_validator.py -v
  2. Verify: All tests pass
  3. Run: python -m pytest tests/ -k "not integration" -v
  4. Verify: No regressions

AFTER Phase 1 complete:
  1. Run: python -m pytest tests/ -v --cov
  2. Verify: Coverage >85%
  3. Run: python main.py --mode api --port 8000 (test startup)
  4. Verify: Server starts, no errors

AFTER Phase 2 complete:
  1. Run all integration tests
  2. Run load tests
  3. Verify all validators work
```

### 3. Git Commit Strategy
```
COMMIT after each:
  - Phase completion
  - Validator implementation
  - Major milestone

COMMIT MESSAGE format:
  feat: {description}

  - What was added
  - Why it was added
  - Tests included

EXAMPLE:
  feat: Add SeoValidatorAgent

  - Implement SEO headings and heading sizes validation
  - Extracts headings, checks H1, hierarchy, lengths
  - Includes 15 unit tests with 95% coverage
  - Part of Phase 1: Foundation
```

### 4. Documentation Strategy
```
UPDATE documentation:
  - After each phase
  - When adding new files
  - When modifying existing behavior

CREATE MIGRATION_LOG.md:
  - Track what was implemented
  - Track issues encountered
  - Track decisions made
  - Track time spent per phase
```

---

## Critical Decision Points

### Decision 1: Skip Phase 0?
**Question**: Should we skip feature flag infrastructure to save time?

**Answer**:
- IF production deployment: NO - Feature flags are critical
- IF development only: YES - Can skip, set all validators to 100%

**Your Decision**: _______________

### Decision 2: Parallel vs Sequential Validator Implementation?
**Question**: Implement all validators in parallel or one at a time?

**Answer**:
- RECOMMENDED: Sequential (safer, easier to debug)
- ALTERNATIVE: Parallel (faster, but harder to troubleshoot)

**Your Decision**: Sequential (default)

### Decision 3: Remove Legacy Code?
**Question**: Remove old validation methods from ContentValidator?

**Answer**:
- IF production: Keep as fallback for 6+ months
- IF development: Can remove after Phase 3

**Your Decision**: _______________

---

## Progress Tracking Template

**Copy this to MIGRATION_LOG.md and update as you go**:

```markdown
# TBCV Validator Migration - Implementation Log

## Started: YYYY-MM-DD HH:MM
## Status: IN_PROGRESS | COMPLETED | BLOCKED

---

## Phase 0: Preparation
- [ ] Feature flags created
- [ ] Test framework created
- [ ] Baseline metrics captured
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED | SKIPPED
- **Time Spent**: X hours
- **Issues**: None | [List issues]

## Phase 1: Foundation
- [ ] BaseValidatorAgent implemented
- [ ] SeoValidatorAgent implemented
- [ ] ValidatorRouter implemented
- [ ] Orchestrator integration complete
- [ ] API endpoint added
- [ ] All tests passing
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED
- **Time Spent**: X hours
- **Issues**: None | [List issues]

## Phase 2: Core Validators
- [ ] YamlValidatorAgent
- [ ] MarkdownValidatorAgent
- [ ] CodeValidatorAgent
- [ ] LinkValidatorAgent
- [ ] StructureValidatorAgent
- [ ] TruthValidatorAgent
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED
- **Time Spent**: X hours
- **Issues**: None | [List issues]

## Phase 3: Integration & Testing
- [ ] Parity tests passing
- [ ] Integration tests passing
- [ ] Load tests passing
- [ ] UI updated
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED
- **Time Spent**: X hours
- **Issues**: None | [List issues]

## Phase 4: Configuration & Deployment Prep
- [ ] Fuzzy detector enabled
- [ ] Feature flags configured
- [ ] Deployment scripts created
- [ ] Documentation updated
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED
- **Time Spent**: X hours
- **Issues**: None | [List issues]

## Phase 5: Gradual Rollout
- [ ] 10% traffic enabled
- [ ] 50% traffic enabled
- [ ] 100% traffic enabled
- [ ] Monitoring complete
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED | N/A
- **Time Spent**: X hours
- **Issues**: None | [List issues]

## Phase 6: Cleanup
- [ ] Deprecation warnings added
- [ ] Template created
- [ ] Performance tuned
- [ ] Final docs updated
- **Status**: NOT_STARTED | IN_PROGRESS | COMPLETED | SKIPPED
- **Time Spent**: X hours
- **Issues**: None | [List issues]

---

## Total Time Spent: X hours
## Completion Date: YYYY-MM-DD
## Final Status: SUCCESS | PARTIAL | BLOCKED

## Blockers (if any):
1. [Blocker description]
2. [Blocker description]

## Decisions Made:
1. [Decision and rationale]
2. [Decision and rationale]

## Deferred Items:
1. [What was deferred and why]
2. [What was deferred and why]
```

---

## Success Verification Checklist

**After complete implementation, verify ALL of these**:

### Functional Verification
- [ ] All 8 validators registered: `curl http://localhost:8000/registry/agents | jq '.total_agents'` (should show 8+ agents)
- [ ] Dynamic discovery works: `curl http://localhost:8000/api/validators/available | jq '.validators | length'` (should show 10 validators)
- [ ] SEO validator works: Test SEO validation via API, check for H1 detection
- [ ] Fuzzy detector enabled: `curl http://localhost:8000/registry/agents | jq '.agents.fuzzy_detector'` (should not be null)
- [ ] UI shows dynamic validators: Open `http://localhost:8000/dashboard/validations`, verify checkboxes load from API
- [ ] Fallback to legacy works: Unregister validator, verify fallback triggers
- [ ] UI override works: Select validator disabled in config, verify it attempts to run

### Test Verification
- [ ] All unit tests pass: `python -m pytest tests/validators/ -v` (100% pass rate)
- [ ] All integration tests pass: `python -m pytest tests/integration/ -v` (100% pass rate)
- [ ] Coverage >85%: `python -m pytest --cov=agents/validators --cov-report=term-missing` (check percentage)
- [ ] No regressions: `python -m pytest tests/ -v` (all existing tests still pass)
- [ ] Load test passes: `python -m pytest tests/performance/test_load.py -v` (no timeouts, no memory leaks)

### Code Quality Verification
- [ ] No Python errors: `python -m pylint agents/validators/*.py` (or similar linter)
- [ ] Type hints present: Check all new files have type annotations
- [ ] Docstrings present: Check all classes and public methods have docstrings
- [ ] No TODO comments: Search for TODO, resolve or document in issues

### Documentation Verification
- [ ] README.md updated: Reflects new architecture
- [ ] API docs updated: `/api/validators/available` documented
- [ ] Migration log complete: MIGRATION_LOG.md shows all phases
- [ ] New validator guide exists: Template for future validators

### Deployment Verification (if deploying)
- [ ] Feature flags work: Toggle flags, verify behavior changes
- [ ] Rollback tested: Disable feature, verify fallback to legacy
- [ ] Smoke tests pass: Run `scripts/smoke_test.sh`
- [ ] No production errors: Check logs for 24 hours after deployment

---

## Completion Report Template

**When finished, create this file**: `MIGRATION_COMPLETION_REPORT.md`

```markdown
# TBCV Validator Migration - Completion Report

## Executive Summary
- **Start Date**: YYYY-MM-DD
- **End Date**: YYYY-MM-DD
- **Total Duration**: X weeks / X hours
- **Status**: ✅ COMPLETED | ⚠️ PARTIAL | ❌ BLOCKED
- **Production Deployed**: YES | NO
- **Overall Success**: YES | NO

## Phases Completed
- [x] Phase 0: Preparation
- [x] Phase 1: Foundation
- [x] Phase 2: Core Validators
- [x] Phase 3: Integration & Testing
- [x] Phase 4: Configuration & Deployment
- [x] Phase 5: Gradual Rollout
- [x] Phase 6: Cleanup

## Validators Implemented
- [x] YamlValidatorAgent
- [x] MarkdownValidatorAgent
- [x] CodeValidatorAgent
- [x] LinkValidatorAgent
- [x] StructureValidatorAgent
- [x] SeoValidatorAgent
- [x] TruthValidatorAgent
- [x] Fuzzy Detector (enabled)

## Metrics Achieved
| Metric | Baseline | Target | Actual | Status |
|--------|----------|--------|--------|--------|
| ContentValidator LOC | 2100 | <300 | ___ | ✅/❌ |
| Test Coverage | 75% | 90%+ | ___% | ✅/❌ |
| Validators as Agents | 2/10 | 10/10 | ___/10 | ✅/❌ |
| UI Coverage | 70% | 100% | ___% | ✅/❌ |
| Avg Validation Latency | 45ms | <50ms | ___ms | ✅/❌ |
| Error Rate | 0.1% | <0.5% | ___% | ✅/❌ |

## Issues Encountered
1. [Issue description, how resolved]
2. [Issue description, how resolved]

## Decisions Made
1. [Decision and rationale]
2. [Decision and rationale]

## Deferred Items
1. [What was deferred, why, when to revisit]
2. [What was deferred, why, when to revisit]

## Recommendations
1. [Recommendation for future]
2. [Recommendation for future]

## Lessons Learned
1. [What went well]
2. [What could be improved]

## Next Steps
1. [Immediate next steps]
2. [Future enhancements]
```

---

## Emergency Contacts & Escalation

**IF BLOCKED** and cannot resolve autonomously:

1. **Document the blocker** in MIGRATION_LOG.md
2. **Attempt workaround** (continue with other phases)
3. **Flag for human review** in completion report

**CRITICAL BLOCKERS** (stop immediately):
- Database corruption
- Production errors >5%
- Data loss
- Security vulnerability

**NON-CRITICAL BLOCKERS** (continue with other work):
- Single test failure
- Minor performance issue
- Documentation incomplete
- UI glitch

---

## Quick Reference Commands

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run only validator tests
python -m pytest tests/validators/ -v

# Run with coverage
python -m pytest --cov=agents/validators --cov-report=html tests/

# Run specific test
python -m pytest tests/validators/test_seo_validator.py::test_seo_missing_h1 -v

# Run load tests
python -m pytest tests/performance/ -v
```

### Server
```bash
# Start server
python main.py --mode api --port 8000

# Check health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready

# Check validators
curl http://localhost:8000/registry/agents | jq
curl http://localhost:8000/api/validators/available | jq

# Test validation
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "# Test\nContent", "validation_types": ["seo"]}' | jq
```

### Git
```bash
# Commit after phase
git add .
git commit -m "feat: Complete Phase 1 - Foundation"

# Tag milestone
git tag -a v2.1.0-beta1 -m "Phase 1 Complete"

# View changes
git diff
git status
```

---

## File Checklist

**By end of implementation, these files should exist**:

### New Files Created
- [ ] `core/feature_flags.py`
- [ ] `config/features.yaml`
- [ ] `agents/validators/__init__.py`
- [ ] `agents/validators/base_validator.py`
- [ ] `agents/validators/seo_validator.py`
- [ ] `agents/validators/yaml_validator.py`
- [ ] `agents/validators/markdown_validator.py`
- [ ] `agents/validators/code_validator.py`
- [ ] `agents/validators/link_validator.py`
- [ ] `agents/validators/structure_validator.py`
- [ ] `agents/validators/truth_validator.py`
- [ ] `agents/validators/router.py`
- [ ] `agents/validators/TEMPLATE_validator.py`
- [ ] `tests/validators/__init__.py`
- [ ] `tests/validators/test_base_validator.py`
- [ ] `tests/validators/test_seo_validator.py`
- [ ] `tests/validators/test_validator_router.py`
- [ ] `tests/validators/test_parity.py`
- [ ] `MIGRATION_LOG.md`
- [ ] `MIGRATION_COMPLETION_REPORT.md`

### Modified Files
- [ ] `api/server.py` (added validator registrations, API endpoint)
- [ ] `agents/orchestrator.py` (integrated ValidatorRouter)
- [ ] `config/main.yaml` (added validator configs, enabled fuzzy_detector)
- [ ] `templates/validations_list.html` (dynamic validator loading)
- [ ] `README.md` (updated documentation)

---

## Ready to Begin?

**You have everything you need**:
✅ Clear implementation order
✅ Code templates
✅ Testing procedures
✅ Success criteria
✅ Progress tracking
✅ Rollback procedures

**Start with**: Phase 0 or Phase 1 (if skipping Phase 0)

**Remember**: You are autonomous. Make decisions, document them, keep going.

**Good luck!** 🚀

---

**Last Updated**: 2025-11-22
**Status**: Ready for Implementation
**Estimated Total Time**: 30-40 hours continuous work
**Estimated Calendar Time**: 8-10 weeks with monitoring
