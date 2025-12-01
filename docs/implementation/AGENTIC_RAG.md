# Agentic RAG Implementation

## Overview

TBCV implements **Agentic RAG (Retrieval-Augmented Generation)** for semantic truth validation. This pattern enables semantic search over truth data, allowing the system to find relevant truth entries even when queries don't exactly match the stored text.

## Architecture

```
                    ┌─────────────────────────────────┐
                    │         TRUTH MANAGER           │
                    │     (TruthManagerAgent)         │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                    │      RAG LAYER (Optional)       │
                    │                                 │
                    │  ┌──────────────────────────┐  │
                    │  │    Embedding Service     │  │
                    │  │    (nomic-embed-text)    │  │
                    │  └────────────┬─────────────┘  │
                    │               │                 │
                    │  ┌────────────▼─────────────┐  │
                    │  │     Vector Store         │  │
                    │  │ (ChromaDB / In-Memory)   │  │
                    │  └────────────┬─────────────┘  │
                    │               │                 │
                    │  ┌────────────▼─────────────┐  │
                    │  │   Semantic Search        │  │
                    │  │   (Cosine Similarity)    │  │
                    │  └──────────────────────────┘  │
                    │                                 │
                    │          ▲ Fallback ▲           │
                    │               │                 │
                    │  ┌────────────┴─────────────┐  │
                    │  │   Exact/Fuzzy Match      │  │
                    │  │   (Traditional Search)    │  │
                    │  └──────────────────────────┘  │
                    └─────────────────────────────────┘
```

## Key Components

### EmbeddingService (`core/embeddings.py`)

Generates vector embeddings via Ollama:

```python
from core.embeddings import get_embedding_service

service = get_embedding_service()

# Single embedding
result = await service.get_embedding("word processor plugin")
if result.embedding:
    print(f"Dimension: {len(result.embedding)}")  # 768 for nomic

# Batch embeddings
results = await service.get_embeddings_batch(["text1", "text2"])
```

Features:
- Ollama integration (nomic-embed-text model)
- Embedding caching with TTL
- Batch processing for efficiency
- Graceful fallback when unavailable

### TruthVectorStore (`core/vector_store.py`)

Stores and retrieves truth data using vector similarity:

```python
from core.vector_store import get_truth_vector_store

store = get_truth_vector_store()

# Index truth data
await store.index_truths("words", truths_list)

# Search
results = await store.search(
    query="document conversion plugin",
    family="words",
    top_k=5,
    similarity_threshold=0.7
)
```

Features:
- Multiple backends (ChromaDB, in-memory)
- Family-based indexing
- Configurable similarity thresholds
- Automatic fallback to exact matching

### TruthManagerAgent Integration

The TruthManagerAgent exposes RAG functionality via MCP handlers:

```python
# Index truths for RAG
await truth_manager.handle_index_for_rag({
    "family": "words",
    "clear_existing": True
})

# Semantic search
result = await truth_manager.handle_search_with_rag({
    "query": "convert word to pdf",
    "family": "words",
    "top_k": 5
})

# Check RAG status
status = await truth_manager.handle_get_rag_status({})
```

## Configuration (`config/rag.yaml`)

```yaml
rag:
  enabled: true

  embedding:
    model: "nomic-embed-text"
    base_url: "http://localhost:11434"
    batch_size: 100
    dimension: 768

  vector_store:
    backend: "chromadb"  # or "memory"
    persist_dir: "./data/vector_store"
    collection_prefix: "tbcv_truth"

  search:
    top_k: 5
    similarity_threshold: 0.7
    include_metadata: true

  fallback:
    enabled: true
    on_embedding_failure: true
    on_no_results: true

  cache:
    enabled: true
    ttl_seconds: 86400
    max_entries: 10000
```

## CLI Commands

```bash
# Index truth data for semantic search
python -m cli.main rag index --family words

# Index all families
python -m cli.main rag index --all-families

# Search using semantic similarity
python -m cli.main rag search "word document conversion" --family words

# Check RAG status
python -m cli.main rag status

# Clear the vector index
python -m cli.main rag clear --family words
```

## Usage Examples

### Basic RAG Search

```python
from agents.truth_manager import TruthManagerAgent

truth_manager = TruthManagerAgent("truth_manager")

# First, ensure truths are indexed
await truth_manager.handle_load_truth_data({"family": "words"})
await truth_manager.handle_index_for_rag({"family": "words"})

# Now search semantically
result = await truth_manager.handle_search_with_rag({
    "query": "how to save document as PDF",
    "family": "words",
    "top_k": 5
})

for match in result["results"]:
    print(f"Score: {match['score']:.3f} - {match['text']}")
```

### With Fallback

```python
# RAG search with automatic fallback
result = await truth_manager.handle_search_with_rag({
    "query": "SaveFormat.Pdf",  # Exact pattern might work better with fallback
    "family": "words"
})

if result["fallback_used"]:
    print("Used traditional search (RAG unavailable or no results)")
else:
    print("Used semantic RAG search")
```

## Data Flow

### Indexing Flow

```
Truth JSON Files
        │
        ▼
┌───────────────────┐
│ Load & Parse      │
│ (TruthManager)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Extract Text      │
│ (index_fields)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Generate          │
│ Embeddings        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Store in          │
│ Vector Store      │
└───────────────────┘
```

### Search Flow

```
User Query
        │
        ▼
┌───────────────────┐
│ Generate Query    │
│ Embedding         │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Vector Search     │
│ (Cosine Sim)      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐
│ Results Above     │────►│ Return Results    │
│ Threshold?        │ Yes │                   │
└─────────┬─────────┘     └───────────────────┘
          │ No
          ▼
┌───────────────────┐     ┌───────────────────┐
│ Fallback          │────►│ Traditional       │
│ Enabled?          │ Yes │ Search            │
└─────────┬─────────┘     └───────────────────┘
          │ No
          ▼
┌───────────────────┐
│ Return Empty      │
└───────────────────┘
```

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Embedding (single) | ~50-100ms | Via Ollama |
| Embedding (cached) | <1ms | From memory cache |
| Batch embeddings | ~500ms/100 | Concurrent processing |
| Vector search | ~10ms | In-memory |
| Vector search (ChromaDB) | ~20-50ms | Depends on index size |

## Fallback Behavior

The system gracefully falls back to traditional search when:

1. **RAG disabled**: `rag.enabled: false` in config
2. **Ollama unavailable**: Embedding service not reachable
3. **No results**: Query returns no results above threshold
4. **Embedding error**: Failed to generate query embedding

Fallback uses the existing `handle_search_plugins` method with fuzzy/exact matching.

## Requirements

### Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull embedding model
ollama pull nomic-embed-text

# Verify
ollama list
```

### Optional: ChromaDB

```bash
pip install chromadb
```

Without ChromaDB, the in-memory backend is used (data not persisted).

## Testing

```bash
# Run RAG tests
pytest tests/core/test_embeddings.py tests/core/test_vector_store.py -v

# Run with coverage
pytest tests/core/test_embeddings.py tests/core/test_vector_store.py --cov=core.embeddings --cov=core.vector_store
```

## Monitoring

### RAG Status

```bash
python -m cli.main rag status
```

Returns:
- Enabled status
- Indexed document count
- Available families
- Embedding dimension
- Last update timestamp

### Cache Statistics

```python
from core.embeddings import get_embedding_service

service = get_embedding_service()
stats = service.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## Troubleshooting

### Ollama Not Available

```
Failed to embed query: Embedding service not available
```

Solution: Ensure Ollama is running (`ollama serve`) and the model is pulled.

### Low Similarity Scores

If semantic search returns poor results:
1. Lower `similarity_threshold` in config
2. Check that truths are properly indexed
3. Verify embedding model is appropriate for content

### Index Not Found

```
No results found
```

Solution: Run `python -m cli.main rag index --family words` to index truths.

## Related Documentation

- [Design Patterns Plan](../../plans/design_patterns.md)
- [Truth Manager](./truth_manager.md)
- [Testing Guide](../testing.md)
