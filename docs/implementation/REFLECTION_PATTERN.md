# Reflection Pattern Implementation

## Overview

TBCV implements the **Reflection (Self-Critique) Pattern** to improve recommendation quality before persistence. This pattern adds a critique-and-refine loop that evaluates recommendations, discards low-quality ones, and refines those that need improvement.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

     Validation Issues
            │
            ▼
┌─────────────────────┐
│ RecommendationAgent │
│ (generate raw recs) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ RecommendationCritic│◄────│   Critique Prompts  │
│   (self-critique)   │     │ recommendation_     │
└──────────┬──────────┘     │ critique.json       │
           │                └─────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌───────┐    ┌─────────┐
│Discard│    │ Refine  │──┐
└───────┘    └────┬────┘  │
                  │       │ (max 2 iterations)
                  ◄───────┘
                  │
                  ▼
          ┌─────────────┐
          │ Deduplicate │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │   Persist   │
          └─────────────┘
```

## Key Components

### RecommendationCriticAgent (`agents/recommendation_critic.py`)

The critic agent evaluates recommendations on multiple quality dimensions:

```python
class RecommendationCriticAgent(BaseAgent):
    async def critique(self, recommendation: Dict, context: Dict) -> CritiqueResult:
        """Evaluate recommendation quality."""

    async def refine(self, recommendation: Dict, critique: Dict) -> Dict:
        """Improve recommendation based on critique."""

    def deduplicate(self, recommendations: List[Dict]) -> List[Dict]:
        """Remove semantically similar recommendations."""
```

### CritiqueResult

Quality assessment structure:

```python
@dataclass
class CritiqueResult:
    actionable: bool           # Can someone implement this?
    actionable_reason: str
    fixes_issue: bool          # Will it resolve the problem?
    fixes_issue_reason: str
    specific: bool             # Is scope specific enough?
    specific_reason: str
    side_effects: List[str]    # Potential unintended consequences
    quality_score: float       # 0.0-1.0 weighted score
    should_discard: bool       # Below discard threshold?
    needs_refinement: bool     # Needs improvement?
    refinement_suggestions: str
```

## Quality Dimensions

Recommendations are evaluated on four weighted dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Actionable | 0.3 | Can the recommendation be implemented? |
| Fixes Issue | 0.3 | Does it actually resolve the problem? |
| Specific | 0.2 | Is the scope specific enough to act on? |
| Side Effects | 0.2 | Are there unintended consequences? |

## Quality Thresholds

```yaml
thresholds:
  quality_threshold: 0.7    # Accept without refinement
  discard_threshold: 0.3    # Discard if below
  similarity_threshold: 0.85 # Deduplication similarity
```

### Decision Logic

```
if quality_score < 0.3:
    → DISCARD (too low quality)
elif quality_score < 0.7:
    → REFINE (needs improvement)
else:
    → ACCEPT (good enough)
```

## Banned Phrases

The following vague phrases are automatically flagged:

- "review and fix"
- "check and update"
- "ensure proper"
- "make sure"

Recommendations containing these phrases are marked as non-actionable.

## Configuration (`config/reflection.yaml`)

```yaml
reflection:
  enabled: true

  thresholds:
    quality_threshold: 0.7
    discard_threshold: 0.3
    similarity_threshold: 0.85

  refinement:
    max_iterations: 2
    use_llm: true
    llm_model: "mistral"
    temperature: 0.3

  deduplication:
    enabled: true
    method: "fuzzy"  # exact | fuzzy | semantic
    compare_fields:
      - instruction
      - scope

  dimensions:
    actionable:
      weight: 0.3
    fixes_issue:
      weight: 0.3
    specific:
      weight: 0.2
    side_effects:
      weight: 0.2

  rules:
    require_rationale: true
    min_instruction_length: 20
    max_instruction_length: 500
    banned_phrases:
      - "review and fix"
      - "check and update"
      - "ensure proper"
```

## Usage

### Basic Usage (Automatic)

When reflection is enabled, the RecommendationAgent automatically applies it:

```python
from agents.recommendation_agent import RecommendationAgent

agent = RecommendationAgent()
result = await agent.handle_generate_recommendations({
    "validation": validation_result,
    "content": content,
    "context": {"file_path": "doc.md"}
})

# Result includes reflection stats
print(f"Original: {result['reflection']['original_count']}")
print(f"Final: {result['reflection']['final_count']}")
print(f"Discarded: {result['reflection']['discarded_count']}")
```

### Explicit Reflection

Force reflection even if disabled in config:

```python
result = await agent.handle_generate_recommendations({
    "validation": validation_result,
    "content": content,
    "context": {},
    "use_reflection": True  # Force enable
})
```

### Direct Critic Usage

Use the critic directly for custom workflows:

```python
from agents.recommendation_critic import RecommendationCriticAgent

critic = RecommendationCriticAgent()

# Critique a single recommendation
critique = await critic.critique(recommendation, context)
if critique.needs_refinement:
    improved = await critic.refine(recommendation, critique.to_dict())

# Process a batch
result = await critic.handle_process_recommendations({
    "recommendations": recommendations,
    "context": context
})
```

## Critique Modes

### Rule-Based (Default)

Fast heuristic evaluation without LLM:

```yaml
refinement:
  use_llm: false
```

Checks:
- Banned phrase detection
- Instruction length validation
- Scope specificity
- Rationale presence

### LLM-Based

Semantic evaluation using Ollama:

```yaml
refinement:
  use_llm: true
  llm_model: "mistral"
```

Uses prompts from `prompts/recommendation_critique.json`.

## Deduplication

Three methods available:

| Method | Description | Speed |
|--------|-------------|-------|
| `exact` | Exact string match | Fastest |
| `fuzzy` | SequenceMatcher similarity | Fast |
| `semantic` | Embedding similarity | Slow |

```python
# Fuzzy example
similarity = SequenceMatcher(None, instruction1, instruction2).ratio()
if similarity >= 0.85:
    # Keep higher quality one
```

## Metrics

The reflection pipeline returns detailed statistics:

```python
{
    "recommendations": [...],
    "discarded_count": 2,      # Removed due to low quality
    "refined_count": 3,        # Improved through refinement
    "deduplicated_count": 1,   # Removed as duplicates
    "original_count": 10,
    "final_count": 4,
    "reflection_enabled": True
}
```

## Testing

```bash
# Run critic tests
pytest tests/agents/test_recommendation_critic.py -v

# Run specific test class
pytest tests/agents/test_recommendation_critic.py::TestRuleBasedCritique -v

# Run with coverage
pytest tests/agents/test_recommendation_critic.py --cov=agents.recommendation_critic
```

## Performance Characteristics

| Mode | Latency per Rec | Quality |
|------|-----------------|---------|
| Rule-based | ~1ms | Good |
| LLM (mistral) | ~500ms | Better |
| With refinement | 2-3x base | Best |

## Best Practices

1. **Start with rules**: Use rule-based mode for fast iteration
2. **Enable LLM for production**: Better quality for user-facing recommendations
3. **Tune thresholds**: Adjust based on false positive/negative rates
4. **Monitor metrics**: Track discard and refinement rates
5. **Update banned phrases**: Add domain-specific vague language

## Troubleshooting

### High Discard Rate

If too many recommendations are discarded:
- Lower `discard_threshold`
- Review banned phrases list
- Check if generators are producing vague recommendations

### Low Quality Scores

If scores are consistently low:
- Improve recommendation generators
- Add more rationale
- Use more specific scopes

### Slow Performance

If reflection is too slow:
- Disable LLM mode
- Reduce `max_iterations`
- Use `exact` deduplication

## Related Documentation

- [Recommendation Agent](./RECOMMENDATION_AGENT.md)
- [Design Patterns](../../plans/design_patterns.md)
- [Testing Guide](../testing.md)
