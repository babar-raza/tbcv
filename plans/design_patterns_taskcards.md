# Design Patterns Implementation - Task Cards

## Overview

| Task | Priority | Effort | Pattern |
|------|----------|--------|---------|
| TC-DP-001: Enhanced Parallel Execution | P1 | Low | Parallel/Scatter-Gather |
| TC-DP-002: Reflection Pattern | P2 | Medium | Reflection (Self-Critique) |
| TC-DP-003: Agentic RAG | P3 | High | Agentic RAG |

---

## TC-DP-001: Enhanced Parallel Execution

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: Validator execution is sequential within files; implement tiered parallel execution
- Allowed paths:
  - `core/validator_router.py`
  - `config/validation_flow.yaml`
  - `agents/orchestrator.py`
  - `tests/core/test_validator_router.py`
  - `docs/implementation/PARALLEL_EXECUTION.md`
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m cli.main validate --path ./test_content/`
- Web: `python main.py` then open http://127.0.0.1:8000 and run validation
- Tests: `pytest tests/core/test_validator_router.py -v`
- Benchmark: Validation of 100 files completes in <15s (was ~30s)
- No mock data used in production paths
- Configs in `./config/` are enforced end to end

**Deliverables:**
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests in `/tests/` covering:
  - Happy path: tiered execution completes correctly
  - Failing path: early termination on critical errors
  - Edge case: single validator in tier
- If schemas change, include forward-compatible migration code

**Hard rules:**
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in mock tests
- UI vs CLI vs MCP endpoint parity for the feature
- Dual testing modes: Mock vs Live Data (runtime flag)
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies without approval
- Keep code style consistent with existing codebase
- Keep documentation in sync with code changes
- Keep tests in sync with code changes
- Make sure there is no regression in existing functionality

**Implementation steps:**

1. **Design: Tier Configuration**
   ```yaml
   # config/validation_flow.yaml
   validators:
     tier_1:  # No dependencies, run in parallel
       - yaml_validator
       - markdown_validator
       - link_validator
       - seo_validator
     tier_2:  # Depends on tier_1
       - structure_validator
       - code_validator
     tier_3:  # Depends on tier_2
       - truth_validator
       - llm_validator

   execution:
     early_termination: true
     critical_error_levels: ["critical", "fatal"]
   ```

2. **Design: Tiered Executor**
   ```python
   # core/validator_router.py
   async def execute_tiered(self, content: str, context: Dict) -> List[ValidationResult]:
       results = []
       for tier_name, validators in self.tiers.items():
           tier_results = await asyncio.gather(*[
               self._run_validator(v, content, context)
               for v in validators
               if self._should_run(v, context)
           ])
           results.extend(tier_results)
           if self._has_critical_errors(tier_results):
               break
       return results
   ```

3. **Tests required:**
   - `test_tiered_execution_parallel_within_tier`
   - `test_tiered_execution_sequential_between_tiers`
   - `test_early_termination_on_critical_error`
   - `test_single_validator_tier`
   - `test_empty_tier_skipped`
   - `test_benchmark_100_files_under_15s`

4. **Documentation required:**
   - `docs/implementation/PARALLEL_EXECUTION.md`

**Self-review (answer yes/no at the end):**
- [ ] Thorough implementation
- [ ] Systematic testing
- [ ] Wired UI and backend
- [ ] MCP usage intact
- [ ] CLI and Web in sync
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No regression in existing tests

**Runbook:**
```bash
# 1. Update config
# Edit config/validation_flow.yaml with tier definitions

# 2. Implement tiered execution
# Edit core/validator_router.py

# 3. Run tests
pytest tests/core/test_validator_router.py -v

# 4. Run benchmark
python -c "import time; start=time.time(); import asyncio; from core.validator_router import ValidatorRouter; asyncio.run(ValidatorRouter().benchmark(100)); print(f'Time: {time.time()-start:.2f}s')"

# 5. Verify CLI
python -m cli.main validate --path ./test_content/

# 6. Verify Web
python main.py
# Open http://127.0.0.1:8000, run validation

# 7. Full test suite (no regression)
pytest -q

# 8. Update docs
# Edit docs/implementation/PARALLEL_EXECUTION.md
```

---

## TC-DP-002: Reflection Pattern for Recommendations

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: Recommendations generated without quality check; implement self-critique loop
- Allowed paths:
  - `agents/recommendation_critic.py` (new)
  - `agents/recommendation_agent.py`
  - `prompts/recommendation_critique.yaml` (new)
  - `config/reflection.yaml` (new)
  - `tests/agents/test_recommendation_critic.py` (new)
  - `tests/agents/test_recommendation_agent.py`
  - `docs/implementation/REFLECTION_PATTERN.md` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m cli.main validate --path ./test_content/ --generate-recommendations`
- Web: `python main.py` then open http://127.0.0.1:8000/recommendations
- Tests: `pytest tests/agents/test_recommendation_critic.py tests/agents/test_recommendation_agent.py -v`
- Metric: Recommendation false positive rate <5% (was ~15%)
- No mock data used in production paths
- Configs in `./config/` are enforced end to end

**Deliverables:**
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests in `/tests/` covering:
  - Happy path: recommendation refined successfully
  - Failing path: low-quality recommendation discarded
  - Edge case: recommendation already high quality (no refinement needed)
  - Edge case: duplicate recommendations deduplicated
- If schemas change, include forward-compatible migration code

**Hard rules:**
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in mock tests
- UI vs CLI vs MCP endpoint parity for the feature
- Dual testing modes: Mock vs Live Data (runtime flag)
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies without approval
- Keep code style consistent with existing codebase
- Keep documentation in sync with code changes
- Keep tests in sync with code changes
- Make sure there is no regression in existing functionality

**Implementation steps:**

1. **Design: RecommendationCriticAgent**
   ```python
   # agents/recommendation_critic.py
   class RecommendationCriticAgent(BaseAgent):
       async def critique(self, recommendation: Dict, context: Dict) -> Dict:
           """Return quality assessment with actionable/fixes_issue/quality_score."""

       async def refine(self, recommendation: Dict, critique: Dict) -> Dict:
           """Improve recommendation based on critique feedback."""

       def _deduplicate(self, recommendations: List[Dict]) -> List[Dict]:
           """Remove semantically similar recommendations."""
   ```

2. **Design: Critique Prompts**
   ```yaml
   # prompts/recommendation_critique.yaml
   critique_prompt: |
     Evaluate this recommendation:
     1. Is it actionable?
     2. Does it fix the issue?
     3. Quality score (0.0-1.0)
     Return JSON with: actionable, fixes_issue, quality_score, should_discard, needs_refinement

   refinement_prompt: |
     Improve this recommendation based on the critique.
   ```

3. **Design: Configuration**
   ```yaml
   # config/reflection.yaml
   reflection:
     enabled: true
     max_iterations: 2
     quality_threshold: 0.7
     discard_threshold: 0.3
     deduplicate: true
     similarity_threshold: 0.85
   ```

4. **Design: Integration Flow**
   ```python
   # agents/recommendation_agent.py
   async def generate_recommendations(self, validation, content, context):
       raw = await self._generate_raw(validation, content)
       refined = []
       for rec in raw:
           critique = await self.critic.critique(rec, context)
           if critique["should_discard"]:
               continue
           if critique["needs_refinement"]:
               rec = await self.critic.refine(rec, critique)
           rec["critique_score"] = critique["quality_score"]
           refined.append(rec)
       return self._deduplicate(refined)
   ```

5. **Tests required:**
   - `test_critique_identifies_low_quality`
   - `test_critique_passes_high_quality`
   - `test_refine_improves_recommendation`
   - `test_discard_below_threshold`
   - `test_deduplicate_similar_recommendations`
   - `test_max_iterations_respected`
   - `test_reflection_disabled_via_config`

6. **Documentation required:**
   - `docs/implementation/REFLECTION_PATTERN.md`

**Self-review (answer yes/no at the end):**
- [ ] Thorough implementation
- [ ] Systematic testing
- [ ] Wired UI and backend
- [ ] MCP usage intact
- [ ] CLI and Web in sync
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No regression in existing tests

**Runbook:**
```bash
# 1. Create config
# Create config/reflection.yaml

# 2. Create prompts
# Create prompts/recommendation_critique.yaml

# 3. Create critic agent
# Create agents/recommendation_critic.py

# 4. Integrate into recommendation agent
# Edit agents/recommendation_agent.py

# 5. Run new tests
pytest tests/agents/test_recommendation_critic.py -v

# 6. Run existing tests (no regression)
pytest tests/agents/test_recommendation_agent.py -v

# 7. Verify CLI
python -m cli.main validate --path ./test_content/ --generate-recommendations

# 8. Verify Web
python main.py
# Open http://127.0.0.1:8000/recommendations

# 9. Full test suite
pytest -q

# 10. Measure false positive rate
python -c "from tests.metrics import measure_false_positives; print(measure_false_positives())"

# 11. Update docs
# Create docs/implementation/REFLECTION_PATTERN.md
```

---

## TC-DP-003: Agentic RAG for Truth Lookups

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: Truth validation uses exact/fuzzy matching; implement semantic vector search
- Allowed paths:
  - `core/vector_store.py` (new)
  - `core/embeddings.py` (new)
  - `agents/truth_manager.py`
  - `config/rag.yaml` (new)
  - `cli/main.py` (add index-truths command)
  - `tests/core/test_vector_store.py` (new)
  - `tests/core/test_embeddings.py` (new)
  - `tests/agents/test_truth_manager.py`
  - `docs/implementation/AGENTIC_RAG.md` (new)
  - `pyproject.toml` (add chromadb dependency)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m cli.main index-truths --family words`
- CLI: `python -m cli.main validate --path ./test_content/`
- Web: `python main.py` then open http://127.0.0.1:8000 and run validation
- Tests: `pytest tests/core/test_vector_store.py tests/core/test_embeddings.py tests/agents/test_truth_manager.py -v`
- Metric: Truth match recall >90% (was ~70%)
- Fallback: Works without Ollama (falls back to exact matching)
- No mock data used in production paths
- Configs in `./config/` are enforced end to end

**Deliverables:**
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests in `/tests/` covering:
  - Happy path: semantic search finds relevant truths
  - Failing path: graceful fallback when embeddings unavailable
  - Edge case: empty truth index
  - Edge case: query with no matches above threshold
- If schemas change, include forward-compatible migration code

**Hard rules:**
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in mock tests
- UI vs CLI vs MCP endpoint parity for the feature
- Dual testing modes: Mock vs Live Data (runtime flag)
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies without approval (chromadb pre-approved)
- Keep code style consistent with existing codebase
- Keep documentation in sync with code changes
- Keep tests in sync with code changes
- Make sure there is no regression in existing functionality

**Implementation steps:**

1. **Design: Add Dependency**
   ```toml
   # pyproject.toml
   [project.dependencies]
   chromadb = "^0.4.0"
   ```

2. **Design: Embeddings Module**
   ```python
   # core/embeddings.py
   import aiohttp
   from typing import List, Optional

   class EmbeddingService:
       def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
           self.model = model
           self.base_url = base_url

       async def get_embedding(self, text: str) -> Optional[List[float]]:
           """Generate embedding via Ollama. Returns None if unavailable."""

       async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
           """Batch embedding generation."""

       async def is_available(self) -> bool:
           """Check if embedding service is reachable."""
   ```

3. **Design: Vector Store**
   ```python
   # core/vector_store.py
   import chromadb
   from typing import List, Dict, Optional

   class TruthVectorStore:
       def __init__(self, persist_dir: str = "./data/vector_store"):
           self.client = chromadb.PersistentClient(path=persist_dir)
           self.embedding_service = EmbeddingService()

       async def index_truths(self, family: str, truths: List[Dict]) -> int:
           """Index truth data for semantic search. Returns count indexed."""

       async def search(self, query: str, family: str, top_k: int = 5) -> List[Dict]:
           """Retrieve relevant truths above similarity threshold."""

       def clear_index(self, family: str) -> None:
           """Clear index for a family (for reindexing)."""

       def get_stats(self) -> Dict:
           """Return index statistics."""
   ```

4. **Design: Configuration**
   ```yaml
   # config/rag.yaml
   rag:
     enabled: true
     embedding_model: "nomic-embed-text"
     vector_store_path: "./data/vector_store"
     top_k: 5
     similarity_threshold: 0.7
     fallback_to_exact_match: true
     batch_size: 100
   ```

5. **Design: CLI Command**
   ```python
   # cli/main.py
   @app.command()
   def index_truths(
       family: str = typer.Option("all", help="Truth family to index"),
       force: bool = typer.Option(False, help="Force reindex")
   ):
       """Index truth data for semantic search."""
   ```

6. **Design: Truth Manager Integration**
   ```python
   # agents/truth_manager.py
   async def validate_with_rag(self, content: str, family: str) -> ValidationResult:
       claims = await self._extract_claims(content)
       issues = []
       for claim in claims:
           truths = await self.vector_store.search(claim, family, top_k=3)
           if not truths:
               # Fallback to exact matching
               truths = self._exact_match(claim, family)
           validation = await self._validate_claim(claim, truths)
           if not validation["valid"]:
               issues.append(validation["issue"])
       return ValidationResult(issues=issues)
   ```

7. **Tests required:**
   - `test_embedding_generation`
   - `test_embedding_batch`
   - `test_embedding_service_unavailable_fallback`
   - `test_index_truths`
   - `test_search_finds_relevant`
   - `test_search_respects_threshold`
   - `test_search_empty_index`
   - `test_clear_and_reindex`
   - `test_validate_with_rag_finds_issues`
   - `test_fallback_to_exact_match`
   - `test_rag_disabled_via_config`

8. **Documentation required:**
   - `docs/implementation/AGENTIC_RAG.md`

**Self-review (answer yes/no at the end):**
- [ ] Thorough implementation
- [ ] Systematic testing
- [ ] Wired UI and backend
- [ ] MCP usage intact
- [ ] CLI and Web in sync
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No regression in existing tests

**Runbook:**
```bash
# 1. Add dependency
pip install chromadb

# 2. Update pyproject.toml
# Add chromadb = "^0.4.0"

# 3. Create config
# Create config/rag.yaml

# 4. Create embeddings module
# Create core/embeddings.py

# 5. Create vector store
# Create core/vector_store.py

# 6. Add CLI command
# Edit cli/main.py

# 7. Integrate into truth manager
# Edit agents/truth_manager.py

# 8. Run new tests
pytest tests/core/test_vector_store.py tests/core/test_embeddings.py -v

# 9. Index truths
python -m cli.main index-truths --family all

# 10. Verify CLI validation
python -m cli.main validate --path ./test_content/

# 11. Verify Web
python main.py
# Open http://127.0.0.1:8000, run validation

# 12. Full test suite (no regression)
pytest -q

# 13. Measure recall
python -c "from tests.metrics import measure_truth_recall; print(measure_truth_recall())"

# 14. Update docs
# Create docs/implementation/AGENTIC_RAG.md
```

---

## Success Criteria Summary

| Task | Metric | Current | Target | Validation Command |
|------|--------|---------|--------|-------------------|
| TC-DP-001 | Latency (100 files) | ~30s | <15s | `python -m pytest tests/core/test_validator_router.py::test_benchmark` |
| TC-DP-002 | False positive rate | ~15% | <5% | `python -m pytest tests/agents/test_recommendation_critic.py::test_false_positive_rate` |
| TC-DP-003 | Truth match recall | ~70% | >90% | `python -m pytest tests/agents/test_truth_manager.py::test_recall` |

---

## Dependency Graph

```
TC-DP-001 (Parallel Execution)
    │
    │ (no dependencies, start immediately)
    ▼
TC-DP-002 (Reflection Pattern)
    │
    │ (can start in parallel with TC-DP-001)
    ▼
TC-DP-003 (Agentic RAG)
    │
    │ (depends on chromadb, can start after approval)
    ▼
COMPLETE
```

---

## Regression Test Matrix

Before marking any task complete, verify no regression:

```bash
# Core tests
pytest tests/core/ -v

# Agent tests
pytest tests/agents/ -v

# API tests
pytest tests/api/ -v

# CLI tests
pytest tests/cli/ -v

# E2E tests
pytest tests/e2e/ -v

# Full suite
pytest -q
```

Each task card requires all tests to pass before completion.
