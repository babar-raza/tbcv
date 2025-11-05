# TBCV Process Flows

| **Title** | Process Flows |
|---|---|
| **Version** | auto |
| **Source** | Code analysis @ 2025-11-03T07:43:18Z |

## Overview

TBCV operates through well-defined process flows that coordinate multiple agents to achieve comprehensive content validation and enhancement. This document details the sequence diagrams and workflow patterns for the major system operations.

## Core Process Flows

### 1. Content Validation Workflow

The primary validation workflow processes content through multiple specialized agents to produce comprehensive quality assessments.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Server
    participant Orch as OrchestratorAgent
    participant TM as TruthManagerAgent
    participant FD as FuzzyDetectorAgent
    participant CV as ContentValidatorAgent
    participant CA as CodeAnalyzerAgent
    participant DB as Database

    Client->>API: POST /validate/content
    Note over Client,API: ContentValidationRequest

    API->>Orch: initiate_workflow(content, config)
    Orch->>DB: create_workflow(job_id, status="running")

    Note over Orch: Step 1: Truth Data Loading
    Orch->>TM: load_truth_data(family="words")
    TM->>TM: index_plugins() # B-tree indexing
    TM->>Orch: truth_data_ready

    Note over Orch: Step 2: Plugin Detection
    Orch->>FD: detect_plugins(content, truth_data)
    FD->>FD: fuzzy_match_text() # Multiple algorithms
    FD->>FD: calculate_confidence() # Weighted scoring
    FD->>Orch: detected_plugins[]

    Note over Orch: Step 3: Content Validation
    Orch->>CV: validate_content(content, plugins)
    CV->>CV: validate_yaml() # Frontmatter check
    CV->>CV: validate_markdown() # Structure analysis
    CV->>CV: validate_links() # URL accessibility
    CV->>Orch: validation_results

    Note over Orch: Step 4: Code Analysis (if applicable)
    alt content contains code
        Orch->>CA: analyze_code(code_blocks)
        CA->>CA: extract_ast() # Abstract syntax tree
        CA->>CA: analyze_document_flow() # Aspose patterns
        CA->>CA: check_security() # Vulnerability scan
        CA->>Orch: code_analysis_results
    end

    Note over Orch: Step 5: Results Aggregation
    Orch->>DB: save_validation_results(job_id, results)
    Orch->>DB: update_workflow(job_id, status="completed")
    Orch->>API: workflow_complete(results)

    API->>Client: 200 OK + ValidationReport
    Note over Client,API: JSON with issues, metrics, recommendations
````

### 2. Content Enhancement Workflow

The enhancement workflow builds upon validation results to automatically improve content quality and add intelligent plugin linking.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Server
    participant Orch as OrchestratorAgent
    participant CE as ContentEnhancerAgent
    participant DB as Database
    participant Cache

    Client->>API: POST /enhance/content
    Note over Client,API: EnhanceContentRequest (validation_id)

    API->>DB: get_validation_results(validation_id)
    DB->>API: validation_data

    API->>Orch: initiate_enhancement(validation_data)
    Orch->>DB: create_workflow(job_id, status="enhancing")

    Note over Orch: Step 1: Validation Data Analysis
    Orch->>CE: analyze_validation_results(validation_data)
    CE->>CE: identify_enhancement_opportunities()
    CE->>CE: prioritize_recommendations()
    CE->>Orch: enhancement_plan

    Note over Orch: Step 2: Plugin Linking
    Orch->>CE: add_plugin_links(content, detected_plugins)
    CE->>CE: find_first_occurrence() # Prevent over-linking
    CE->>Cache: get_link_template(plugin_id)
    CE->>CE: generate_markdown_links()
    CE->>Orch: linked_content

    Note over Orch: Step 3: Information Enhancement
    Orch->>CE: add_info_text(content, context)
    CE->>CE: generate_contextual_info() # Based on plugin usage
    CE->>CE: insert_at_optimal_position()
    CE->>Orch: enhanced_content

    Note over Orch: Step 4: Format Fixes
    Orch->>CE: apply_format_fixes(content)
    CE->>CE: fix_heading_hierarchy()
    CE->>CE: normalize_code_blocks()
    CE->>CE: standardize_lists()
    CE->>Orch: formatted_content

    Note over Orch: Step 5: Quality Verification
    Orch->>CE: verify_enhancements(original, enhanced)
    CE->>CE: check_link_validity()
    CE->>CE: validate_markdown_syntax()
    CE->>Orch: verification_results

    alt preview mode
        Orch->>API: return_preview(enhanced_content, changes)
        API->>Client: EnhancementPreview
    else apply mode
        Orch->>DB: save_enhanced_content(job_id, content)
        Orch->>DB: update_workflow(status="completed")
        API->>Client: EnhancementResult
    end
```

### 3. Batch Processing Workflow

For handling multiple files efficiently with parallel processing and progress tracking.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Server
    participant Orch as OrchestratorAgent
    participant Workers as Worker Pool
    participant DB as Database
    participant WS as WebSocket

    Client->>API: POST /validate/batch
    Note over Client,API: BatchValidationRequest (files[], max_workers)

    API->>Orch: initiate_batch_workflow(files, config)
    Orch->>DB: create_batch_job(job_id, total_files)

    Note over Orch: Step 1: Work Distribution
    Orch->>Orch: chunk_files(files, max_workers)

    loop for each file chunk
        Orch->>Workers: process_file_chunk(chunk)

        par Worker Processing
            Workers->>Workers: validate_file_1()
        and
            Workers->>Workers: validate_file_2()
        and
            Workers->>Workers: validate_file_n()
        end

        Workers->>Orch: chunk_results
        Orch->>DB: update_progress(processed_count)

        Note over Orch: Real-time Progress Updates
        Orch->>WS: broadcast_progress(job_id, progress%)
        WS->>Client: progress_update
    end

    Note over Orch: Step 2: Results Aggregation
    Orch->>Orch: aggregate_results(all_chunks)
    Orch->>Orch: generate_batch_metrics()

    Orch->>DB: save_batch_results(job_id, aggregated_results)
    Orch->>DB: update_batch_job(status="completed")

    Orch->>API: batch_complete(summary_results)
    API->>Client: BatchValidationResult

    Note over Client: Can export detailed results via /export endpoints
```

### 4. External Code Integration Workflow

For fetching and analyzing code from external sources like GitHub gists and repositories.

```mermaid
sequenceDiagram
    participant User
    participant CA as CodeAnalyzerAgent
    participant GitHub as GitHub API
    participant Cache
    participant Security as Security Scanner

    User->>CA: analyze_external_code(url)
    Note over User,CA: URL could be gist, repo, or direct file

    CA->>CA: parse_url_type()

    alt GitHub Gist URL
        CA->>GitHub: GET /gists/{gist_id}
        GitHub->>CA: gist_data
        CA->>CA: extract_code_files()
    else GitHub Repository URL
        CA->>GitHub: GET /repos/{owner}/{repo}/contents/{path}
        GitHub->>CA: file_content
    else Direct File URL
        CA->>CA: fetch_url_content()
    end

    Note over CA: Step 1: Code Validation
    CA->>CA: validate_code_syntax()
    CA->>Security: scan_for_vulnerabilities()
    Security->>CA: security_report

    Note over CA: Step 2: Caching Strategy
    CA->>Cache: check_analysis_cache(url_hash)
    alt cache miss
        CA->>CA: perform_full_analysis()
        CA->>Cache: store_analysis_results()
    else cache hit
        Cache->>CA: cached_results
    end

    Note over CA: Step 3: Document Flow Analysis
    CA->>CA: detect_document_type() # Aspose product detection
    CA->>CA: extract_operations_sequence()
    CA->>CA: analyze_processing_pattern()

    Note over CA: Step 4: Generate Insights
    CA->>CA: generate_code_observations()
    CA->>CA: identify_best_practices()
    CA->>CA: suggest_improvements()

    CA->>User: CodeAnalysisResult
    Note over User,CA: Includes flow analysis, security scan, recommendations
```

### 5. Workflow Management and Control

For managing long-running workflows with pause, resume, and cancellation capabilities.

```mermaid
sequenceDiagram
    participant Admin
    participant API as FastAPI Server
    participant Orch as OrchestratorAgent
    participant DB as Database
    participant Workers as Active Workers

    Note over Admin: Monitor running workflows
    Admin->>API: GET /workflows
    API->>DB: get_active_workflows()
    DB->>API: workflow_list
    API->>Admin: WorkflowStatus[]

    Note over Admin: Control workflow execution
    Admin->>API: POST /workflows/{job_id}/control
    Note over Admin,API: WorkflowControlRequest (action: pause/resume/cancel)

    alt action = pause
        API->>Orch: pause_workflow(job_id)
        Orch->>Workers: signal_pause()
        Workers->>Workers: finish_current_task()
        Workers->>Orch: paused_at_checkpoint
        Orch->>DB: update_workflow(status="paused")

    else action = resume
        API->>Orch: resume_workflow(job_id)
        Orch->>DB: get_last_checkpoint(job_id)
        DB->>Orch: checkpoint_data
        Orch->>Workers: resume_from_checkpoint()
        Orch->>DB: update_workflow(status="running")

    else action = cancel
        API->>Orch: cancel_workflow(job_id)
        Orch->>Workers: signal_cancel()
        Workers->>Workers: cleanup_resources()
        Orch->>DB: save_partial_results()
        Orch->>DB: update_workflow(status="cancelled")
    end

    Orch->>API: control_result
    API->>Admin: WorkflowControlResponse
```

## Specialized Processing Patterns

### Error Handling and Retry Logic

```mermaid
flowchart TD
    A[Agent Task Start] --> B{Execute Operation}
    B -->|Success| C[Return Result]
    B -->|Failure| D{Error Type}

    D -->|Retryable| E{Retry Count < Max}
    D -->|Non-retryable| F[Log Error & Fail]

    E -->|Yes| G[Exponential Backoff]
    E -->|No| H[Log Max Retries & Fail]

    G --> I[Wait Period]
    I --> B

    C --> J[Success]
    F --> K[Failure]
    H --> K

    style A fill:#e3f2fd
    style C fill:#e8f5e8
    style F fill:#ffebee
    style H fill:#ffebee
```

### Cache Management Flow

```mermaid
flowchart TD
    A[Request Data] --> B{Check L1 Cache}
    B -->|Hit| C[Return L1 Data]
    B -->|Miss| D{Check L2 Cache}

    D -->|Hit| E[Update L1 Cache]
    D -->|Miss| F[Compute/Fetch Data]

    E --> G[Return L2 Data]
    F --> H[Store in L2 Cache]
    H --> I[Store in L1 Cache]
    I --> J[Return Fresh Data]

    K[Cache Invalidation] --> L{SHA-256 Check}
    L -->|Changed| M[Clear Related Caches]
    L -->|Unchanged| N[Keep Cache]

    style C fill:#e8f5e8
    style G fill:#e8f5e8
    style J fill:#e8f5e8
    style M fill:#fff3e0
```

### Plugin Detection Algorithm

```mermaid
flowchart TD
    A[Content Input] --> B[Extract Text Segments]
    B --> C[Load Truth Patterns]

    C --> D[Exact Match Detection]
    D --> E[Fuzzy Match Detection]
    E --> F[Pattern Match Detection]

    F --> G{Combine Results}
    G --> H[Calculate Confidence Scores]
    H --> I[Apply Combination Rules]
    I --> J[Filter by Threshold]

    J --> K[Rank by Confidence]
    K --> L[Return Detected Plugins]

    subgraph "Fuzzy Algorithms"
        M[Levenshtein Distance]
        N[Jaro-Winkler]
        O[Ratio Matching]
    end

    E --> M
    E --> N
    E --> O

    M --> G
    N --> G
    O --> G

    style A fill:#e3f2fd
    style L fill:#e8f5e8
    style G fill:#fff3e0
```

## Performance Characteristics

### Scalability Patterns

* **Horizontal Scaling:** Worker pool size configurable per workflow type
* **Vertical Scaling:** Memory and CPU intensive operations use background tasks
* **Cache Optimization:** Two-level cache reduces repeated computations by 70–90%
* **Database Efficiency:** Connection pooling and prepared statements

### Throughput Metrics

* **Single File Validation:** ~200–500 ms (depending on content size and complexity)
* **Batch Processing:** ~50–100 files per minute (with 4 workers)
* **Plugin Detection:** ~10–50 ms per content segment
* **Code Analysis:** ~1–5 s per code block (including external fetching)

### Resource Usage

* **Memory:** ~50–200 MB baseline + ~10 MB per active workflow
* **Storage:** SQLite database grows ~1–5 MB per 1000 validation results
* **Network:** External code fetching limited to 10 MB per file
* **CPU:** Agent processing is I/O bound, scales well with async operations

---

For implementation guidance, see:

* **[Architecture Overview](architecture.md)** — Component relationships
* **[Component Details](components.md)** — Individual module APIs
* **[Operations Guide](operations.md)** — Running and monitoring workflows