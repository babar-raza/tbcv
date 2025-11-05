# TBCV Requirements Mapping

## Extracted Atomic Requirements by Plane

| REQ_ID | Plane | Subsystem | Description | Test Strategy |
|--------|-------|-----------|-------------|---------------|
| **AGENTIC PLANE** |
| A01 | Agentic | Validation | Validate content against truth tables and rulesets stored as JSON files, organized by family | Unit tests with sample JSON files, family detection tests |
| A02 | Agentic | Validation | Detect product family automatically from path or content hints, with safe fallback | Unit tests with various file paths and content samples |
| A03 | Agentic | Validation | Enforce JSON Schema compliance on truth tables at startup; abort early if schemas fail | Startup tests with valid/invalid schemas, error handling tests |
| A04 | Agentic | Validation | Maintain deterministic, idempotent execution — repeated runs yield identical results | Integration tests with multiple runs on same input |
| A05 | Agentic | Validation | Validate YAML front-matter and Markdown body separately | Unit tests for YAML parser and Markdown validation |
| A06 | Agentic | Validation | YAML: only validate selected keys configured per family | Unit tests with family-specific key validation |
| A07 | Agentic | Validation | Markdown: apply two-stage validation — heuristics first, LLM for overall evaluation | Integration tests with mock LLM, heuristic validation tests |
| A08 | Agentic | Validation | Support batch selection/filtering by family, severity, or path | Integration tests with batch operations |
| A09 | Agentic | Validation | Operate locally by default, compatible with optional LLM backends | Unit tests with/without LLM backend |
| A10 | Agentic | Integrity | Detect and flag statements that defy truth or omit required details | Unit tests with truth-defying content samples |
| A11 | Agentic | Integrity | Preserve byte-perfect structure — shortcodes, anchors, code blocks, front-matter delimiters | Integration tests with complex structured content |
| A12 | Agentic | Integrity | Use fuzzy detection (aliases, regex) for plugin and feature recognition | Unit tests with fuzzy matching scenarios |
| A13 | Agentic | Integrity | Validate code snippets by cross-checking API or plugin references | Unit tests with code snippet validation |
| A14 | Agentic | Quality | Maintain ≥ 90% owner identification accuracy | Performance tests with accuracy metrics |
| A15 | Agentic | Quality | Achieve full sentence-level coverage | Unit tests ensuring all sentences are processed |
| A16 | Agentic | Quality | Preserve rewrite safety and structural fidelity under all edits | Integration tests with before/after comparisons |
| A17 | Agentic | Enhancement | Trigger enhancement only after approval, manually or in batch | Integration tests with approval workflow |
| A18 | Agentic | Enhancement | Support dry-run and write modes with identical reports | Unit tests comparing dry-run vs write mode outputs |
| A19 | Agentic | Enhancement | Apply edits to text only, masking/unmasking structure for safety | Unit tests with masking/unmasking logic |
| A20 | Agentic | Enhancement | Enforce canonical phrasing and house-style rules (e.g., no em-dash) | Unit tests with style rule enforcement |
| A21 | Agentic | Enhancement | Insert dependency notes idempotently at fixed policy locations | Unit tests with dependency note insertion |
| A22 | Agentic | Enhancement | Respect rewrite-ratio and blocked-topic gates; refuse unsafe edits | Unit tests with safety gate enforcement |
| A23 | Agentic | Enhancement | Guarantee idempotence — re-running enhancer makes no additional changes | Integration tests with multiple enhancement runs |
| A24 | Agentic | Enhancement | Produce unified diffs, timing logs, and error summaries | Unit tests for output format validation |
| A25 | Agentic | Enhancement | Output identical structured reports for dry-run and write modes | Unit tests comparing report structures |
| **DATA PLANE** |
| D01 | Data | Persistence | Persist validation results, enhancement outcomes, and risk assessments in durable relational store | Database integration tests |
| D02 | Data | Persistence | Record approval states with timestamps, actors, and reviewer comments | Database tests with approval workflow |
| D03 | Data | Persistence | Keep detailed run logs (inputs, configs, timings, results, errors) | Integration tests with logging verification |
| D04 | Data | Persistence | Maintain complete audit log of all dashboard and API actions | Integration tests with audit trail |
| D05 | Data | Persistence | Provide exportable reports (JSON or Markdown) with diffs and KPIs | Integration tests with report generation |
| D06 | Data | Persistence | Integrate seamlessly into CI/CD pipelines for automated ingestion | Integration tests with CI/CD simulation |
| D07 | Data | Caching | Implement shared L2 cache with stable keying for deterministic reuse | Unit tests with cache operations |
| D08 | Data | Caching | Preserve content determinism; prevent stale-cache side effects | Integration tests with cache invalidation |
| D09 | Data | Caching | Record and expose cache hit/miss ratios and latency metrics | Performance tests with metrics validation |
| D10 | Data | Caching | Enable cache visibility via metric hooks and dashboards | Integration tests with metrics exposure |
| D11 | Data | Performance | First-run speed: 5–8 s / file | Performance tests with timing validation |
| D12 | Data | Performance | Warm-cache speed: 1–2 s / file | Performance tests with cache warmup |
| D13 | Data | Performance | Cache hit rate: ≥ 60% | Performance tests with hit rate measurement |
| D14 | Data | Performance | Throughput: 400–600 files / hour (4 workers) | Load tests with worker parallelization |
| **ORCHESTRATION PLANE** |
| O01 | Orchestration | CLI/API | All functions callable from CLI or FastAPI without changing working directory | Integration tests from various working directories |
| O02 | Orchestration | CLI/API | Maintain stable CLI flags; extend via non-breaking options | CLI regression tests |
| O03 | Orchestration | API | Validation API — list validations, fetch diffs, query severity and risk flags | API integration tests |
| O04 | Orchestration | API | Enhancement API — approve/reject items, trigger enhancer runs, stream progress | API integration tests with workflow |
| O05 | Orchestration | API | WebSockets — real-time progress, pause/resume, checkpoint recovery | WebSocket integration tests |
| O06 | Orchestration | Execution | Parallel processing enabled for high throughput | Performance tests with parallel execution |
| O07 | Orchestration | Roles | Reviewer role — approve/reject | Role-based access tests |
| O08 | Orchestration | Roles | Operator role — run enhancer, pause/resume jobs | Role-based access tests |
| O09 | Orchestration | Roles | Auditor role — view-only, export history | Role-based access tests |
| O10 | Orchestration | Security | Apply rate limits and sandboxing for LLM-intensive modules | Security tests with rate limiting |
| O11 | Orchestration | Metrics | Track throughput, latency, error rate, cache performance, and family distribution | Metrics collection tests |
| O12 | Orchestration | Metrics | Integrate with structured logging and performance counters for observability | Logging integration tests |
| **CONFIGURATION PLANE** |
| C01 | Configuration | Stack | Use FastAPI, Uvicorn/Starlette, WebSockets for API & Realtime | Framework integration tests |
| C02 | Configuration | Stack | Use Pydantic + JSON Schema for Config & Validation | Configuration validation tests |
| C03 | Configuration | Stack | Use SQL + migrations; Redis optional for Database & Jobs | Database migration tests |
| C04 | Configuration | Stack | Use YAML (front-matter), Markdown parser, regex, BeautifulSoup for Parsing & Markup | Parser integration tests |
| C05 | Configuration | Stack | Use Fuzzy matching; optional vector DB for Search / Recall | Search functionality tests |
| C06 | Configuration | Stack | Use pytest (asyncio + coverage), rich/tqdm, structured logging for Developer Experience | Test framework validation |
| C07 | Configuration | Stack | Use tree-sitter (optional), aiofiles for Performance Utilities | Performance utility tests |
| C08 | Configuration | Validation | Centralize JSON Schema definitions for all truth tables | Schema validation tests |
| C09 | Configuration | Validation | Maintain rule families mapping to each product line | Rule family mapping tests |
| C10 | Configuration | Validation | Validate both YAML front-matter and Markdown structures per schema | Schema-based validation tests |
| C11 | Configuration | Testing | Achieve ≥ 95% coverage including integration and performance tests | Coverage measurement tests |
| C12 | Configuration | Testing | Test rewrite-ratio enforcement | Unit tests for rewrite ratio limits |
| C13 | Configuration | Testing | Test mask/unmask safety | Unit tests for structure preservation |
| C14 | Configuration | Testing | Test schema validation | Unit tests for schema compliance |
| C15 | Configuration | Testing | Test deterministic idempotence | Integration tests for idempotent behavior |
| **INTEGRATION PLANE** |
| I01 | Integration | Dashboard | Inbox view listing pending validations with metadata | UI integration tests |
| I02 | Integration | Dashboard | Detail view: side-by-side masked original vs proposed text with unified diff tab | UI integration tests |
| I03 | Integration | Dashboard | Batch actions: multi-select → Approve/Reject → Run Enhancer | UI workflow tests |
| I04 | Integration | Control | Require human checkpoint before write ("changes planned") | Approval workflow tests |
| I05 | Integration | Control | Provide run controls (start, pause, resume) with real-time WebSocket updates | WebSocket control tests |
| I06 | Integration | Control | Display per-file timings, status, and outcomes | UI display tests |
| I07 | Integration | History | Offer filterable history (date, family, actor, status) | Database query tests |
| I08 | Integration | History | Export complete audit history for review | Export functionality tests |
| I09 | Integration | Metrics | Dashboard widgets: throughput, cache rates, avg file time, error counts, recent incidents | Metrics display tests |
| I10 | Integration | Access | Enforce role-based permissions | Authorization tests |
| I11 | Integration | Access | Log every action in immutable audit trail | Audit logging tests |
| I12 | Integration | Access | Support UI dry-run mode for visual diff preview without writes | UI dry-run tests |
| I13 | Integration | Review | Display live Inbox queue with file metadata | Queue display tests |
| I14 | Integration | Review | Filter and sort by family, date, severity, or gating result | Filter/sort functionality tests |
| I15 | Integration | Approval | Actions: Accept, Reject, Defer with state transitions | State machine tests |
| I16 | Integration | Approval | Batch approval with multi-select | Batch operation tests |
| I17 | Integration | Approval | All actions timestamped + audited | Audit trail tests |
| I18 | Integration | Enhancement | Trigger Enhancer Run from dashboard (single-file or batch) | Enhancement trigger tests |
| I19 | Integration | Enhancement | Modes: dry_run, write, threshold override | Mode switching tests |
| I20 | Integration | Enhancement | Real-time WebSocket progress stream with per-file status, ETA, and errors | WebSocket progress tests |
| I21 | Integration | Enhancement | Enforce rewrite-ratio, blocked-topics, and dependency rules in dashboard | Rule enforcement tests |
| I22 | Integration | Enhancement | Produce unified diffs, validation scores, and structured logs from dashboard | Output format tests |
| I23 | Integration | Monitoring | Real-time job progress board showing cache use, throughput, latency, file timings | Progress monitoring tests |
| I24 | Integration | Monitoring | Widgets for pending vs approved counts, enhancer throughput, LLM usage, cache hit rates | Widget functionality tests |
| I25 | Integration | Auditing | Full history tab with filters by actor, date, family, and action type | History filtering tests |
| I26 | Integration | Auditing | Exportable reports (JSON/Markdown/CSV) | Export format tests |
| I27 | Integration | Auditing | Immutable audit log ensuring traceability of every operation | Audit immutability tests |
| I28 | Integration | Permissions | Reviewer role: view/approve/reject/defer | Role permission tests |
| I29 | Integration | Permissions | Operator role: execute enhancer, pause/resume | Role permission tests |
| I30 | Integration | Permissions | Auditor role: read-only with export rights | Role permission tests |
| I31 | Integration | Permissions | UCOP Auth Layer enforcing secure role mapping | Authentication integration tests |
| **CROSS-PLANE PERFORMANCE** |
| P01 | Performance | Metrics | First run: 5–8 s / file | Performance benchmarking tests |
| P02 | Performance | Metrics | Warm run: 1–2 s / file | Cache performance tests |
| P03 | Performance | Metrics | Throughput: 400–600 files / hour (4 workers) | Load testing with worker scaling |
| P04 | Performance | Metrics | Cache hit rate: ≥ 60% | Cache efficiency tests |
| P05 | Performance | Metrics | Owner accuracy: ≥ 90% | Accuracy measurement tests |
| P06 | Performance | Metrics | Test coverage: ≥ 95% | Coverage measurement and enforcement |
| P07 | Performance | Metrics | Rewrite safety: 100% structure preservation | Structure preservation tests |

## Summary by Plane

- **Agentic Plane**: 25 requirements (A01-A25) covering validation logic, integrity checks, quality gates, and enhancement workflows
- **Data Plane**: 14 requirements (D01-D14) covering persistence, caching, and performance targets  
- **Orchestration Plane**: 12 requirements (O01-O12) covering CLI/API parity, execution, roles, and observability
- **Configuration Plane**: 15 requirements (C01-C15) covering stack choices, validation config, and testing requirements
- **Integration Plane**: 31 requirements (I01-I31) covering dashboard functionality, controls, monitoring, and permissions
- **Cross-Plane Performance**: 7 requirements (P01-P07) covering performance metrics and targets

**Total Requirements**: 104 atomic, testable requirements across all planes

## Test Coverage Strategy

1. **Unit Tests**: Requirements A01-A25, C08-C15, D07-D10
2. **Integration Tests**: Requirements D01-D06, O01-O12, I01-I31  
3. **Performance Tests**: Requirements D11-D14, P01-P07
4. **API Tests**: Requirements O03-O05, I18-I22
5. **UI Tests**: Requirements I01-I03, I13-I14, I23-I24
6. **Security Tests**: Requirements O07-O10, I10-I11, I28-I31
7. **Database Tests**: Requirements D01-D06, I07-I08, I25-I27
