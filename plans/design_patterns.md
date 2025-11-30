# Design Patterns Gap Analysis & Implementation Plan

## Current State

TBCV implements **5 of 7** ideal patterns for a content validation system:

| Pattern | Status | Accuracy |
|---------|--------|----------|
| Sequential Pipeline | Implemented | 9/10 |
| Multi-Agent Supervisor | Implemented | 9/10 |
| Parallel/Scatter-Gather | Implemented | 8.5/10 |
| Evaluator/Guardrail | Implemented | 9/10 |
| Router/Dispatcher | Implemented | 8/10 |
| **Agentic RAG** | **Not Implemented** | - |
| **Reflection (Self-Critique)** | **Partial** | 7/10 |

---

## Gap 1: Agentic RAG for Truth Lookups

### Current Problem

Truth validation loads JSON files into memory and performs exact/fuzzy matching:

```python
# Current approach in truth_manager.py
def load_truths(self, family: str) -> Dict:
    with open(f"truth/{family}_truth.json") as f:
        return json.load(f)
```

**Limitations:**
- No semantic understanding of truth data
- Exact string matching misses paraphrased content
- Cannot query external knowledge bases
- Large truth files consume memory

### Proposed Solution

Implement vector-based retrieval for truth data with LLM-augmented validation.

### Implementation Steps

#### Step 1: Add Vector Store Infrastructure

**File:** `core/vector_store.py`

```python
from typing import List, Dict, Optional
import hashlib

class TruthVectorStore:
    """Vector store for semantic truth retrieval."""

    def __init__(self, embedding_model: str = "nomic-embed-text"):
        self.embedding_model = embedding_model
        self.index = {}  # family -> vector index

    async def index_truths(self, family: str, truths: List[Dict]) -> int:
        """Index truth data for semantic search."""
        pass

    async def search(self, query: str, family: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant truths for a query."""
        pass

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        pass
```

#### Step 2: Integrate with Truth Manager

**File:** `agents/truth_manager.py`

Add RAG-based truth lookup alongside existing exact matching:

```python
async def validate_with_rag(self, content: str, family: str) -> ValidationResult:
    """Use RAG to find relevant truths and validate content."""

    # 1. Extract claims from content
    claims = await self._extract_claims(content)

    # 2. For each claim, retrieve relevant truths
    for claim in claims:
        relevant_truths = await self.vector_store.search(
            query=claim,
            family=family,
            top_k=3
        )

        # 3. LLM validates claim against retrieved truths
        validation = await self._validate_claim_against_truths(
            claim, relevant_truths
        )

    return ValidationResult(...)
```

#### Step 3: Add Embedding Generation

**File:** `core/embeddings.py`

```python
import aiohttp

async def get_embedding(text: str, model: str = "nomic-embed-text") -> List[float]:
    """Generate embedding via Ollama."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text}
        ) as resp:
            data = await resp.json()
            return data["embedding"]
```

#### Step 4: Create Truth Indexing CLI Command

**File:** `cli/main.py`

```python
@app.command()
def index_truths(family: str = "all"):
    """Index truth data for semantic search."""
    # Load truths and generate embeddings
    # Store in vector index
```

### Configuration

**File:** `config/rag.yaml`

```yaml
rag:
  enabled: true
  embedding_model: "nomic-embed-text"
  vector_store: "chromadb"  # or "faiss", "qdrant"
  top_k: 5
  similarity_threshold: 0.7
  fallback_to_exact_match: true
```

### Dependencies

```toml
# pyproject.toml additions
chromadb = "^0.4.0"  # or faiss-cpu, qdrant-client
```

---

## Gap 2: True Reflection Pattern for Recommendations

### Current Problem

Recommendations are generated in a single pass without self-critique:

```
Validation Issues → RecommendationAgent → Recommendations (stored)
```

**Limitations:**
- No quality check on recommendations
- False positives persist
- Recommendations may be impractical or redundant

### Proposed Solution

Add a critique-and-refine loop before persisting recommendations.

### Implementation Steps

#### Step 1: Add Recommendation Critic

**File:** `agents/recommendation_critic.py`

```python
class RecommendationCriticAgent(BaseAgent):
    """Critiques and refines recommendations before persistence."""

    async def critique(self, recommendation: Dict, context: Dict) -> Dict:
        """
        Evaluate a recommendation and return critique.

        Checks:
        - Is the recommendation actionable?
        - Does it actually fix the issue?
        - Is it too vague or too specific?
        - Are there unintended side effects?
        - Is it redundant with other recommendations?
        """
        prompt = self._build_critique_prompt(recommendation, context)
        response = await self.llm.generate(prompt)
        return self._parse_critique(response)

    async def refine(self, recommendation: Dict, critique: Dict) -> Dict:
        """Refine recommendation based on critique."""
        if critique["quality_score"] >= 0.8:
            return recommendation  # Good enough

        prompt = self._build_refinement_prompt(recommendation, critique)
        refined = await self.llm.generate(prompt)
        return self._parse_recommendation(refined)
```

#### Step 2: Integrate into Recommendation Flow

**File:** `agents/recommendation_agent.py`

```python
async def generate_recommendations(self, validation, content, context):
    """Generate and refine recommendations with reflection."""

    # Stage 1: Generate initial recommendations
    raw_recommendations = await self._generate_raw(validation, content)

    # Stage 2: Critique each recommendation
    refined_recommendations = []
    for rec in raw_recommendations:
        critique = await self.critic.critique(rec, context)

        if critique["should_discard"]:
            self.logger.info(f"Discarding low-quality recommendation: {rec['id']}")
            continue

        if critique["needs_refinement"]:
            rec = await self.critic.refine(rec, critique)

        rec["critique_score"] = critique["quality_score"]
        refined_recommendations.append(rec)

    # Stage 3: Deduplicate
    final_recommendations = self._deduplicate(refined_recommendations)

    return final_recommendations
```

#### Step 3: Add Critique Prompts

**File:** `prompts/recommendation_critique.yaml`

```yaml
critique_prompt: |
  You are a quality reviewer for content improvement recommendations.

  RECOMMENDATION:
  {recommendation}

  ORIGINAL ISSUE:
  {issue}

  CONTENT CONTEXT:
  {context}

  Evaluate this recommendation:
  1. Is it actionable? (Can someone implement it?)
  2. Does it fix the issue? (Will the problem be resolved?)
  3. Is it specific enough? (Not too vague?)
  4. Are there side effects? (Could it break something?)
  5. Quality score (0.0-1.0)

  Return JSON:
  {
    "actionable": true/false,
    "fixes_issue": true/false,
    "specific": true/false,
    "side_effects": ["list of concerns"],
    "quality_score": 0.0-1.0,
    "should_discard": true/false,
    "needs_refinement": true/false,
    "refinement_suggestions": "..."
  }

refinement_prompt: |
  Improve this recommendation based on the critique.

  ORIGINAL:
  {recommendation}

  CRITIQUE:
  {critique}

  Return an improved recommendation that addresses the concerns.
```

### Configuration

**File:** `config/reflection.yaml`

```yaml
reflection:
  enabled: true
  max_iterations: 2
  quality_threshold: 0.7
  discard_threshold: 0.3
  deduplicate: true
  similarity_threshold: 0.85
```

---

## Gap 3: Enhanced Parallel Execution

### Current Problem

Validators run somewhat in parallel, but could be more aggressive:

```python
# Current: File-level parallelism
await asyncio.gather(*[process_file(f) for f in files])

# Missing: Validator-level parallelism within each file
```

### Proposed Solution

Run independent validators concurrently for each file.

### Implementation Steps

#### Step 1: Identify Validator Dependencies

**File:** `config/validation_flow.yaml`

```yaml
validators:
  tier_1:  # Run in parallel (no dependencies)
    - yaml_validator
    - markdown_validator
    - link_validator
    - seo_validator

  tier_2:  # Run after tier_1 (depends on structure)
    - structure_validator
    - code_validator

  tier_3:  # Run after tier_2 (depends on content validation)
    - truth_validator
    - llm_validator
```

#### Step 2: Implement Tiered Parallel Execution

**File:** `core/validator_router.py`

```python
async def execute_tiered(self, content: str, context: Dict) -> List[ValidationResult]:
    """Execute validators in dependency tiers, parallel within tiers."""

    results = []

    for tier_name, validators in self.tiers.items():
        # Run all validators in this tier concurrently
        tier_results = await asyncio.gather(*[
            self._run_validator(v, content, context)
            for v in validators
            if self._should_run(v, context)
        ])

        results.extend(tier_results)

        # Check for early termination (critical errors)
        if self._has_critical_errors(tier_results):
            self.logger.warning(f"Critical error in {tier_name}, stopping")
            break

    return results
```

---

## Implementation Priority

| Gap | Priority | Effort | Impact |
|-----|----------|--------|--------|
| Enhanced Parallel Execution | P1 | Low | Medium |
| Reflection for Recommendations | P2 | Medium | High |
| Agentic RAG for Truths | P3 | High | High |

### Rationale

1. **Parallel Execution (P1)**: Low effort, immediate performance gains
2. **Reflection (P2)**: Medium effort, significantly improves recommendation quality
3. **RAG (P3)**: High effort (new infrastructure), but enables semantic truth matching

---

## Task Cards

### Task 1: Enhanced Parallel Execution

```
[ ] Update config/validation_flow.yaml with tier definitions
[ ] Modify core/validator_router.py for tiered execution
[ ] Add early termination on critical errors
[ ] Update tests for parallel execution
[ ] Benchmark performance improvement
```

### Task 2: Reflection Pattern

```
[ ] Create agents/recommendation_critic.py
[ ] Add prompts/recommendation_critique.yaml
[ ] Create config/reflection.yaml
[ ] Integrate critic into RecommendationAgent
[ ] Add deduplication logic
[ ] Update tests for reflection flow
[ ] Measure false positive reduction
```

### Task 3: Agentic RAG

```
[ ] Add chromadb/faiss dependency
[ ] Create core/vector_store.py
[ ] Create core/embeddings.py
[ ] Add config/rag.yaml
[ ] Create CLI command for truth indexing
[ ] Integrate RAG into TruthManager
[ ] Add fallback to exact matching
[ ] Update tests for RAG flow
[ ] Benchmark retrieval quality
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Validation latency (100 files) | ~30s | ~15s |
| Recommendation false positive rate | ~15% | ~5% |
| Truth match recall | ~70% | ~90% |
| Pattern coverage | 5/7 | 7/7 |

---

## Architecture After Implementation

```
                    ┌─────────────────┐
                    │     ROUTER      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ TIER 1  │         │ TIER 2  │         │ TIER 3  │
   │(parallel)│   ──►  │(parallel)│   ──►  │(parallel)│
   └─────────┘         └─────────┘         └─────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   AGGREGATOR    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  RAG + TRUTH    │◄──── Vector Store
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   LLM GATING    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ RECOMMENDATIONS │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   REFLECTION    │◄──── Critic Agent
                    │  (self-critique)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PERSIST      │
                    └─────────────────┘
```
