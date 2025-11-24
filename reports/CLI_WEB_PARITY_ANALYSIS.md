# TBCV Feature Parity Analysis: Core vs CLI vs Web UI

**Generated:** 2025-11-21
**Version:** TBCV 2.0.0
**Purpose:** Comprehensive analysis of feature availability across Core Application, CLI, and Web UI interfaces

---

## Executive Summary

**Total Core Features Identified:** 50+
**MCP Integration:** Full (All agents communicate via MCP)
**CLI Coverage:** ~85% of user-facing features
**Web UI Coverage:** ~90% of user-facing features

### Key Findings

✅ **Well Covered:**
- Content validation (all interfaces)
- Recommendation management (all interfaces)
- Workflow orchestration (all interfaces)
- Real-time updates (Web UI only)
- Configuration management (both CLI and Web)

⚠️ **Gaps Identified:**
- Cache management (Web only - no CLI equivalent)
- Admin operations (Web only - partial CLI)
- System diagnostics (Web only - limited CLI)
- WebSocket monitoring (Web only)
- Background job status (Web only)

---

## 1. CORE APPLICATION FEATURES

### 1.1 Agent System (8 Agents)

| Agent | Purpose | MCP | CLI Access | Web Access |
|-------|---------|-----|------------|------------|
| **TruthManagerAgent** | Plugin truth data management | ✅ | ✅ (indirect) | ✅ (indirect) |
| **FuzzyDetectorAgent** | Fuzzy pattern matching for plugins | ✅ | ✅ (indirect) | ✅ (via `/api/detect-plugins`) |
| **ContentValidatorAgent** | Generic content validation | ✅ | ✅ (`validate-file`, `validate`) | ✅ (`POST /api/validate`) |
| **ContentEnhancerAgent** | Content enhancement | ✅ | ✅ (`enhance`) | ✅ (`POST /api/enhance`) |
| **LLMValidatorAgent** | Semantic validation via Ollama | ✅ | ✅ (indirect) | ✅ (indirect) |
| **RecommendationAgent** | Generate recommendations | ✅ | ✅ (indirect) | ✅ (`POST .../recommendations/generate`) |
| **EnhancementAgent** | Apply approved recommendations | ✅ | ✅ (`recommendations enhance`) | ✅ (`POST /api/enhance/{validation_id}`) |
| **OrchestratorAgent** | Multi-agent workflow coordination | ✅ | ✅ (`validate`, `batch`) | ✅ (`POST /workflows/validate-directory`) |

**Parity Score:** 8/8 agents accessible via both interfaces ✅

---

### 1.2 Validation Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Single File Validation** | ✅ | ✅ `validate-file` | ✅ `POST /api/validate` | Full parity |
| **Batch/Directory Validation** | ✅ | ✅ `validate-directory`, `batch` | ✅ `POST /workflows/validate-directory` | Full parity |
| **Validation Types Selection** | ✅ 7 types | ✅ `--types` flag | ✅ API parameter | Full parity |
| **Confidence Threshold** | ✅ | ✅ `--confidence` flag | ✅ API parameter | Full parity |
| **Two-Stage Validation** | ✅ Heuristic + LLM | ✅ Automatic | ✅ Automatic | Full parity |
| **Validation History** | ✅ | ❌ Not available | ✅ `GET /api/validations/history/{file_path}` | **CLI Gap** |
| **Re-validation** | ✅ | ❌ Not available | ✅ `POST /api/validations/{id}/revalidate` | **CLI Gap** |
| **Validation Comparison** | ✅ Before/after | ❌ Not available | ✅ Built into detail view | **CLI Gap** |
| **Validation Diff Viewer** | ✅ | ❌ Text only | ✅ Side-by-side visual | Web UI advantage |
| **Import Folder** | ✅ | ✅ `validate-directory` | ✅ `POST /api/validations/import` | Different approach |
| **Approve/Reject Validation** | ✅ | ❌ Not direct command | ✅ `POST /api/validations/{id}/approve` | **CLI Gap** |
| **Bulk Approve/Reject** | ✅ | ❌ Not available | ✅ `POST /api/validations/bulk/approve` | **CLI Gap** |
| **Validation Report** | ✅ | ✅ `--output`, `--format` | ✅ `GET /api/validations/{id}/report` | Full parity |

**Parity Score:** 9/13 features in CLI, 13/13 in Web UI
**CLI Coverage:** 69% | **Web Coverage:** 100%

---

### 1.3 Recommendation Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **List Recommendations** | ✅ | ✅ `recommendations list` | ✅ `GET /api/recommendations` | Full parity |
| **Filter by Status** | ✅ | ✅ `--status` | ✅ Query param | Full parity |
| **Filter by Type** | ✅ | ❌ Not available | ✅ Query param | **CLI Gap** |
| **Filter by Validation ID** | ✅ | ✅ `--validation-id` | ✅ Query param | Full parity |
| **Show Recommendation Detail** | ✅ | ✅ `recommendations show` | ✅ `GET /api/recommendations/{id}` | Full parity |
| **Approve Recommendations** | ✅ | ✅ `recommendations approve` | ✅ `POST /api/recommendations/{id}/review` | Full parity |
| **Reject Recommendations** | ✅ | ✅ `recommendations reject` | ✅ `POST /api/recommendations/{id}/review` | Full parity |
| **Bulk Review** | ✅ | ✅ Multiple IDs | ✅ `POST /api/recommendations/bulk-review` | Full parity |
| **Generate Recommendations** | ✅ | ❌ Automatic only | ✅ `POST /api/validations/{id}/recommendations/generate` | **CLI Gap** |
| **Rebuild Recommendations** | ✅ | ❌ Not available | ✅ `POST /api/validations/{id}/rebuild_recommendations` | **CLI Gap** |
| **Delete Recommendation** | ✅ | ❌ Not available | ✅ `DELETE /api/validations/{vid}/recommendations/{rid}` | **CLI Gap** |
| **Apply Recommendations** | ✅ | ✅ `recommendations enhance` | ✅ `POST /api/enhance/{validation_id}` | Full parity |
| **Auto-Apply High Confidence** | ✅ | ❌ Not available | ✅ `POST /api/enhance/auto-apply` | **CLI Gap** |
| **Audit Trail** | ✅ | ❌ Not visible | ✅ Visible in detail view | **CLI Gap** |
| **Reviewer Attribution** | ✅ | ✅ `--reviewer` flag | ✅ Automatic | Full parity |
| **Review Notes** | ✅ | ✅ `--notes` flag | ✅ Form field | Full parity |

**Parity Score:** 10/16 features in CLI, 16/16 in Web UI
**CLI Coverage:** 63% | **Web Coverage:** 100%

---

### 1.4 Content Enhancement Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Plugin Link Insertion** | ✅ | ✅ `enhance --plugin-links` | ✅ Auto with enhancement | Full parity |
| **Informational Text Addition** | ✅ | ✅ `enhance --info-text` | ✅ Auto with enhancement | Full parity |
| **Dry Run / Preview** | ✅ | ✅ `enhance --dry-run` | ✅ `recommendations enhance --preview` | Full parity |
| **Backup Before Enhancement** | ✅ | ✅ `enhance --backup` | ✅ `recommendations enhance --backup` | Full parity |
| **Safety Gating** | ✅ Rewrite threshold | ✅ `enhance --force` override | ✅ Automatic | Full parity |
| **Blocked Topics Filtering** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Validation-Aware Strategy** | ✅ Surgical vs Heavy | ✅ Automatic | ✅ Automatic | Full parity |
| **Recommendation-Based Enhancement** | ✅ | ✅ `recommendations enhance` | ✅ `POST /api/enhance/{validation_id}` | Full parity |
| **Batch Enhancement** | ✅ | ❌ Loop required | ✅ `POST /api/enhance/batch` | **CLI Gap** |
| **Selective Recommendation Application** | ✅ | ❌ All or none | ✅ Checkbox selection in UI | **CLI Gap** |
| **Apply In Place vs Patch** | ✅ | ❌ In-place only | ✅ Mode parameter | **CLI Gap** |

**Parity Score:** 8/11 features in CLI, 11/11 in Web UI
**CLI Coverage:** 73% | **Web Coverage:** 100%

---

### 1.5 Workflow Orchestration Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Start Workflow** | ✅ | ✅ `validate`, `batch` | ✅ `POST /workflows/validate-directory` | Full parity |
| **List Workflows** | ✅ | ❌ Not available | ✅ `GET /workflows` | **CLI Gap** |
| **Get Workflow Status** | ✅ | ✅ Real-time progress | ✅ `GET /workflows/{id}` | Full parity |
| **Get Workflow Report** | ✅ | ✅ `--report-file` | ✅ `GET /workflows/{id}/report` | Full parity |
| **Get Workflow Summary** | ✅ | ✅ `--summary-only` | ✅ `GET /workflows/{id}/summary` | Full parity |
| **Pause Workflow** | ✅ | ❌ Not available | ✅ `POST /workflows/{id}/control` | **CLI Gap** |
| **Resume Workflow** | ✅ | ❌ Not available | ✅ `POST /workflows/{id}/control` | **CLI Gap** |
| **Cancel Workflow** | ✅ | ❌ Ctrl+C only | ✅ `POST /workflows/{id}/control` | **CLI Gap** |
| **Delete Workflow** | ✅ | ❌ Not available | ✅ `DELETE /workflows/{id}` | **CLI Gap** |
| **Bulk Delete Workflows** | ✅ | ❌ Not available | ✅ `POST /workflows/delete` | **CLI Gap** |
| **Cancel Batch Workflows** | ✅ | ❌ Not available | ✅ `POST /workflows/cancel-batch` | **CLI Gap** |
| **Workflow State Tracking** | ✅ 6 states | ✅ Progress display | ✅ Full state machine | Full parity |
| **Checkpoint Support** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Recovery from Failures** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Continue on Error** | ✅ | ✅ `--continue-on-error` | ✅ Default behavior | Full parity |
| **Active Workflows Admin** | ✅ | ❌ Not available | ✅ `GET /admin/workflows/active` | **CLI Gap** |

**Parity Score:** 9/16 features in CLI, 16/16 in Web UI
**CLI Coverage:** 56% | **Web Coverage:** 100%

---

### 1.6 System Management Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Agent Status Check** | ✅ | ✅ `check-agents` | ✅ `GET /agents` | Full parity |
| **Agent Registry View** | ✅ | ❌ Not available | ✅ `GET /registry/agents` | **CLI Gap** |
| **System Status** | ✅ | ✅ `status` | ✅ `GET /status` | Full parity |
| **Health Check** | ✅ | ❌ Not available | ✅ `GET /health` | **CLI Gap** |
| **Readiness Probe** | ✅ | ❌ Not available | ✅ `GET /health/ready` | **CLI Gap** |
| **Liveness Probe** | ✅ | ❌ Not available | ✅ `GET /health/live` | **CLI Gap** |
| **Agent Reload** | ✅ | ❌ Not available | ✅ `POST /admin/agents/reload/{id}` | **CLI Gap** |
| **Cache Statistics** | ✅ | ❌ Not available | ✅ `GET /admin/cache/stats` | **CLI Gap** |
| **Cache Clear** | ✅ | ❌ Not available | ✅ `POST /admin/cache/clear` | **CLI Gap** |
| **Cache Cleanup** | ✅ | ❌ Not available | ✅ `POST /admin/cache/cleanup` | **CLI Gap** |
| **Cache Rebuild** | ✅ | ❌ Not available | ✅ `POST /admin/cache/rebuild` | **CLI Gap** |
| **Performance Report** | ✅ | ❌ Not available | ✅ `GET /admin/reports/performance` | **CLI Gap** |
| **Health Report** | ✅ | ❌ Not available | ✅ `GET /admin/reports/health` | **CLI Gap** |
| **Garbage Collection** | ✅ | ❌ Not available | ✅ `POST /admin/system/gc` | **CLI Gap** |
| **Maintenance Mode** | ✅ | ❌ Not available | ✅ `POST /admin/maintenance/enable` | **CLI Gap** |
| **System Checkpoint** | ✅ | ❌ Not available | ✅ `POST /admin/system/checkpoint` | **CLI Gap** |

**Parity Score:** 2/16 features in CLI, 16/16 in Web UI
**CLI Coverage:** 13% | **Web Coverage:** 100%

---

### 1.7 Data & Persistence Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Read File Content** | ✅ | ✅ Direct file access | ✅ `GET /api/files/read` | Full parity |
| **Database Persistence** | ✅ SQLite | ✅ Automatic | ✅ Automatic | Full parity |
| **Validation History Storage** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Recommendation Storage** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Workflow State Storage** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Audit Logging** | ✅ | ❌ Not visible | ✅ `GET /api/audit` | **CLI Gap** |
| **Checkpoint Persistence** | ✅ | ✅ Automatic | ✅ Automatic | Full parity |
| **Cache (L1 + L2)** | ✅ | ✅ Used | ✅ Used + Admin | Full parity (admin Web only) |
| **Metrics Storage** | ✅ | ✅ Used | ✅ Used | Full parity |

**Parity Score:** 7/9 features in CLI, 9/9 in Web UI
**CLI Coverage:** 78% | **Web Coverage:** 100%

---

### 1.8 Real-Time & Live Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **WebSocket Support** | ✅ | ❌ N/A | ✅ `/ws/{workflow_id}` | Web only by design |
| **Server-Sent Events (SSE)** | ✅ | ❌ N/A | ✅ `/api/stream/updates` | Web only by design |
| **Live Dashboard Updates** | ✅ | ❌ N/A | ✅ Real-time metrics | Web only by design |
| **Live Activity Feed** | ✅ | ❌ N/A | ✅ Event stream | Web only by design |
| **Workflow Progress Updates** | ✅ | ✅ Console progress | ✅ WebSocket progress | Different approach |
| **Toast Notifications** | ✅ | ❌ N/A | ✅ UI toasts | Web only by design |
| **Connection Status Indicator** | ✅ | ❌ N/A | ✅ UI indicator | Web only by design |

**Parity Score:** 1/7 features in CLI (console progress), 7/7 in Web UI
**Note:** Most real-time features are Web UI-specific by design

---

### 1.9 Configuration Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Load Configuration File** | ✅ YAML | ✅ `--config` flag | ✅ Server loads | Full parity |
| **Environment Variables** | ✅ `TBCV_*` | ✅ Supported | ✅ Supported | Full parity |
| **Plugin Family Selection** | ✅ 5 families | ✅ `--family` flag | ✅ UI dropdown | Full parity |
| **Validation Types Config** | ✅ 7 types | ✅ `--types` flag | ✅ UI checkboxes | Full parity |
| **Worker Count Config** | ✅ | ✅ `--workers` flag | ✅ UI input | Full parity |
| **Confidence Threshold Config** | ✅ | ✅ `--confidence` flag | ✅ API parameter | Full parity |
| **Cache Control** | ✅ | ✅ `--no-cache` flag | ❌ Not exposed | **Web Gap** |
| **Log Level Config** | ✅ | ✅ `--verbose` flag | ❌ Not exposed | **Web Gap** |
| **Quiet Mode** | ✅ | ✅ `--quiet` flag | ❌ N/A | CLI only |
| **Recursive Mode** | ✅ | ✅ `--recursive` flag | ❌ Always recursive | CLI advantage |
| **File Pattern Config** | ✅ | ✅ `--pattern` flag | ✅ UI input | Full parity |
| **Continue on Error** | ✅ | ✅ `--continue-on-error` | ✅ Default | Full parity |
| **Backup Creation** | ✅ | ✅ `--backup` flag | ✅ Checkbox/default | Full parity |
| **Force Override** | ✅ | ✅ `--force` flag | ❌ Not exposed | **Web Gap** |
| **Output Format Config** | ✅ | ✅ `--format` flag | ❌ JSON always | CLI advantage |
| **Output File Path** | ✅ | ✅ `--output` flag | ❌ Download/API only | CLI advantage |

**Parity Score:** 16/16 in CLI, 11/16 in Web UI
**CLI Coverage:** 100% | **Web Coverage:** 69%

---

### 1.10 Utility Features

| Feature | Core | CLI | Web UI | Notes |
|---------|------|-----|--------|-------|
| **Plugin Detection** | ✅ Fuzzy | ✅ Indirect | ✅ `POST /api/detect-plugins` | Web has direct endpoint |
| **Test File Creation** | ✅ | ✅ `test` command | ❌ Not available | **Web Gap** |
| **API Endpoint Probing** | ✅ | ✅ `probe-endpoints` | ❌ Not available | **Web Gap** |
| **Validation Notes** | ✅ | ❌ Not available | ✅ `GET /validation-notes` | **CLI Gap** |
| **Statistics Dashboard** | ✅ | ❌ Limited | ✅ `GET /api/stats` | **CLI Gap** |

**Parity Score:** 2/5 in CLI, 3/5 in Web UI
**CLI Coverage:** 40% | **Web Coverage:** 60%

---

## 2. MCP (MODEL CONTEXT PROTOCOL) USAGE

### 2.1 MCP Integration Summary

**MCP Implementation Level:** FULL ✅

All 8 agents in the TBCV system are MCP-enabled and communicate via the Model Context Protocol.

### 2.2 MCP Components

| Component | Location | Purpose | CLI Uses | Web Uses |
|-----------|----------|---------|----------|----------|
| **MCPMessage** | agents/base.py | Standardized message format | ✅ Indirect | ✅ Indirect |
| **BaseAgent** | agents/base.py | Agent base class with MCP | ✅ All agents | ✅ All agents |
| **AgentContract** | agents/base.py | Capability declaration | ✅ All agents | ✅ All agents |
| **AgentRegistry** | agents/registry.py | Agent discovery/routing | ✅ Used | ✅ Used |
| **MCP Server** | svc/mcp_server.py | JSON-RPC 2.0 server | ❌ Not used | ✅ Used |
| **MCP Client** | api/services/mcp_client.py | Client library | ❌ Not used | ✅ Used |

### 2.3 MCP Features Used

| MCP Feature | Implementation | CLI | Web UI |
|-------------|----------------|-----|--------|
| **JSON-RPC 2.0 Messages** | MCPMessage dataclass | ✅ | ✅ |
| **Request/Response Pattern** | Message routing | ✅ | ✅ |
| **Notification Pattern** | Broadcast messages | ✅ | ✅ |
| **Contract System** | AgentContract | ✅ | ✅ |
| **Capability Advertisement** | AgentCapability | ✅ | ✅ |
| **Side Effect Declaration** | Contract field | ✅ | ✅ |
| **Dependency Management** | Contract field | ✅ | ✅ |
| **Timeout Handling** | Async with timeout | ✅ | ✅ |
| **Error Handling** | Structured errors | ✅ | ✅ |
| **Agent Discovery** | Registry lookup | ✅ | ✅ |

### 2.4 MCP Server Endpoints

| Endpoint | Method | CLI Access | Web Access | Notes |
|----------|--------|------------|------------|-------|
| **validate_folder** | JSON-RPC | ❌ | ✅ | Web only uses MCP server |
| **approve** | JSON-RPC | ❌ | ✅ | Web only uses MCP server |
| **reject** | JSON-RPC | ❌ | ✅ | Web only uses MCP server |
| **enhance** | JSON-RPC | ❌ | ✅ | Web only uses MCP server |

**Note:** CLI directly imports agents, while Web UI can use either direct imports OR MCP server

---

## 3. CONFIGURATION PARITY ANALYSIS

### 3.1 Configuration Files

| Configuration File | CLI Can Read | Web Can Read | CLI Can Modify | Web Can Modify |
|-------------------|--------------|--------------|----------------|----------------|
| **config/agent.yaml** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **config/enhancement.yaml** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **config/perf.json** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **config/seo.yaml** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **config/heading_sizes.yaml** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **config/tone.json** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **config/main.yaml** | ✅ | ✅ | ❌ Edit file | ❌ Edit file |
| **Environment overrides** | ✅ | ✅ | ✅ Env vars | ✅ Env vars |

**Neither CLI nor Web UI provides in-app configuration editing** ⚠️

### 3.2 Runtime Configuration Options

| Setting | CLI | Web UI | Notes |
|---------|-----|--------|-------|
| **Plugin Family** | ✅ `--family` | ✅ UI/API param | Full parity |
| **Validation Types** | ✅ `--types` | ✅ UI checkboxes | Full parity |
| **Confidence Threshold** | ✅ `--confidence` | ✅ API param | Full parity |
| **Worker Count** | ✅ `--workers` | ✅ UI input | Full parity |
| **File Pattern** | ✅ `--pattern` | ✅ UI input | Full parity |
| **Recursive Search** | ✅ `--recursive` | ✅ Always on | CLI more flexible |
| **Output Format** | ✅ `--format` | ❌ JSON only | CLI only |
| **Log Level** | ✅ `--verbose` | ❌ Server config | CLI only |
| **Cache Control** | ✅ `--no-cache` | ❌ Not exposed | CLI only |
| **Continue on Error** | ✅ `--continue-on-error` | ✅ Default | Full parity |
| **Backup Creation** | ✅ `--backup` | ✅ Checkbox | Full parity |
| **Force Override** | ✅ `--force` | ❌ Not exposed | CLI only |
| **Preview/Dry Run** | ✅ `--dry-run`, `--preview` | ✅ Checkbox | Full parity |

**Configuration Parity:** ~85% overlap, CLI has more low-level control options

---

## 4. COMPREHENSIVE GAP ANALYSIS

### 4.1 Features ONLY in CLI

| Feature | Command | Why Not in Web UI |
|---------|---------|-------------------|
| **Test File Creation** | `test` | Development utility |
| **API Endpoint Probing** | `probe-endpoints` | Development/diagnostic utility |
| **Cache Disable** | `--no-cache` | Low-level control |
| **Log Level Control** | `--verbose` | Runtime diagnostic |
| **Quiet Mode** | `--quiet` | CLI-specific UX |
| **Custom Output Format** | `--format json/text/yaml` | CLI display flexibility |
| **Custom Output File** | `--output` | CLI workflow integration |
| **Force Safety Override** | `--force` | Expert/dangerous option |

**Total:** 8 CLI-exclusive features (mostly CLI-specific utilities)

---

### 4.2 Features ONLY in Web UI

| Feature | Endpoint/Page | Why Not in CLI |
|---------|---------------|----------------|
| **Validation History View** | `GET /api/validations/history/{path}` | Visual timeline/trend |
| **Re-validation** | `POST /api/validations/{id}/revalidate` | Comparison workflow |
| **Visual Diff Viewer** | Dashboard validation detail | Visual comparison |
| **Bulk Operations** | Multiple endpoints | Batch UI interactions |
| **Approve/Reject Validations** | `POST /api/validations/{id}/approve` | Human review workflow |
| **Generate Recommendations** | `POST .../recommendations/generate` | On-demand generation |
| **Rebuild Recommendations** | `POST .../rebuild_recommendations` | Force regeneration |
| **Delete Recommendation** | `DELETE .../recommendations/{id}` | Cleanup operation |
| **Auto-Apply Recommendations** | `POST /api/enhance/auto-apply` | High-confidence automation |
| **Filter by Rec Type** | Query param | UI filtering |
| **Batch Enhancement** | `POST /api/enhance/batch` | Bulk processing |
| **Selective Rec Application** | UI checkboxes | Interactive selection |
| **Apply In-Place vs Patch** | Mode parameter | Output mode selection |
| **List Workflows** | `GET /workflows` | Historical view |
| **Pause/Resume Workflow** | `POST /workflows/{id}/control` | Long-running control |
| **Cancel Workflow** | `POST /workflows/{id}/control` | Runtime control |
| **Delete Workflows** | `DELETE /workflows/{id}` | Cleanup operation |
| **Bulk Delete Workflows** | `POST /workflows/delete` | Bulk cleanup |
| **Active Workflows Admin** | `GET /admin/workflows/active` | Admin monitoring |
| **Agent Registry View** | `GET /registry/agents` | System introspection |
| **Health Checks** | `GET /health/*` | K8s/monitoring |
| **Agent Reload** | `POST /admin/agents/reload/{id}` | Hot reload |
| **Cache Management** | Multiple endpoints | Admin operations |
| **Performance Reports** | `GET /admin/reports/performance` | System monitoring |
| **Health Reports** | `GET /admin/reports/health` | System monitoring |
| **Garbage Collection** | `POST /admin/system/gc` | Memory management |
| **Maintenance Mode** | `POST /admin/maintenance/*` | Operational control |
| **System Checkpoint** | `POST /admin/system/checkpoint` | State management |
| **Audit Log Viewing** | `GET /api/audit` | Historical tracking |
| **Validation Notes** | `GET /validation-notes` | Annotation system |
| **Statistics Dashboard** | `GET /api/stats` | Visual metrics |
| **WebSocket Updates** | `WS /ws/*` | Real-time push |
| **SSE Stream** | `GET /api/stream/updates` | Live events |
| **Live Dashboard** | Real-time updates | Visual monitoring |
| **Activity Feed** | Live event stream | Recent activity |
| **Toast Notifications** | UI component | User feedback |

**Total:** 35 Web UI-exclusive features (mostly admin, monitoring, and UI-specific)

---

### 4.3 Critical Gaps

#### CLI Missing Critical Features

1. **Validation Management:**
   - ❌ Cannot approve/reject validations directly
   - ❌ Cannot view validation history
   - ❌ Cannot re-validate content
   - ❌ Cannot compare before/after results

2. **Recommendation Management:**
   - ❌ Cannot force-generate recommendations
   - ❌ Cannot rebuild recommendations
   - ❌ Cannot delete individual recommendations
   - ❌ Cannot filter by recommendation type
   - ❌ Cannot auto-apply high-confidence recommendations

3. **Workflow Management:**
   - ❌ Cannot list historical workflows
   - ❌ Cannot pause/resume workflows
   - ❌ Cannot cancel running workflows (except Ctrl+C)
   - ❌ Cannot delete completed workflows
   - ❌ No workflow cleanup operations

4. **System Administration:**
   - ❌ No cache management commands
   - ❌ No agent reload capability
   - ❌ No health check commands
   - ❌ No performance reporting
   - ❌ No maintenance mode control

5. **Data Visualization:**
   - ❌ No visual diff viewer (text only)
   - ❌ No trend analysis
   - ❌ No statistics dashboard
   - ❌ Limited audit log access

#### Web UI Missing Features

1. **Development Utilities:**
   - ❌ No test file creation
   - ❌ No API endpoint probing

2. **Low-Level Control:**
   - ❌ No cache disable option
   - ❌ No log level runtime control
   - ❌ No force safety override (by design)

3. **Output Flexibility:**
   - ❌ No custom output format selection (JSON only)
   - ❌ No custom output file path (download or API only)

**Impact Assessment:**
- CLI gaps are **HIGH impact** for production operations
- Web UI gaps are **LOW impact** (mostly dev utilities)

---

## 5. FEATURE MATRIX SUMMARY

### 5.1 Overall Coverage Statistics

| Category | Total Features | CLI | Web UI | Both | CLI Only | Web Only |
|----------|----------------|-----|--------|------|----------|----------|
| **Agents** | 8 | 8 | 8 | 8 | 0 | 0 |
| **Validation** | 13 | 9 | 13 | 9 | 0 | 4 |
| **Recommendations** | 16 | 10 | 16 | 10 | 0 | 6 |
| **Enhancement** | 11 | 8 | 11 | 8 | 0 | 3 |
| **Workflows** | 16 | 9 | 16 | 9 | 0 | 7 |
| **System Mgmt** | 16 | 2 | 16 | 2 | 0 | 14 |
| **Data & Persistence** | 9 | 7 | 9 | 7 | 0 | 2 |
| **Real-Time** | 7 | 1 | 7 | 1 | 0 | 6 |
| **Configuration** | 16 | 16 | 11 | 11 | 5 | 0 |
| **Utilities** | 5 | 2 | 3 | 0 | 2 | 1 |
| **TOTAL** | **117** | **72** | **110** | **65** | **7** | **43** |

### 5.2 Interface Coverage Percentages

| Interface | Features Available | Coverage % | Unique Features |
|-----------|-------------------|------------|-----------------|
| **CLI** | 72 / 117 | **61.5%** | 7 (6.0%) |
| **Web UI** | 110 / 117 | **94.0%** | 43 (36.8%) |
| **Both** | 65 / 117 | **55.6%** | N/A |

### 5.3 Category Coverage Comparison

```
Agents:          CLI ████████████████████ 100%  Web ████████████████████ 100%
Validation:      CLI █████████████░░░░░░░  69%  Web ████████████████████ 100%
Recommendations: CLI ████████████░░░░░░░░  63%  Web ████████████████████ 100%
Enhancement:     CLI ██████████████░░░░░░  73%  Web ████████████████████ 100%
Workflows:       CLI ███████████░░░░░░░░░  56%  Web ████████████████████ 100%
System Mgmt:     CLI ██░░░░░░░░░░░░░░░░░░  13%  Web ████████████████████ 100%
Data:            CLI ███████████████░░░░░  78%  Web ████████████████████ 100%
Real-Time:       CLI ██░░░░░░░░░░░░░░░░░░  14%  Web ████████████████████ 100%
Configuration:   CLI ████████████████████ 100%  Web ███████████████░░░░░  69%
Utilities:       CLI ████████░░░░░░░░░░░░  40%  Web ████████████░░░░░░░░  60%
```

---

## 6. MCP USAGE BREAKDOWN

### 6.1 MCP-Enabled Features

**All core processing features use MCP** ✅

| Feature Category | Uses MCP | CLI Access | Web Access |
|------------------|----------|------------|------------|
| Content Validation | ✅ 100% | ✅ Via agents | ✅ Via agents |
| Fuzzy Detection | ✅ 100% | ✅ Via agents | ✅ Via agents |
| Truth Management | ✅ 100% | ✅ Via agents | ✅ Via agents |
| LLM Validation | ✅ 100% | ✅ Via agents | ✅ Via agents |
| Recommendations | ✅ 100% | ✅ Via agents | ✅ Via agents |
| Enhancement | ✅ 100% | ✅ Via agents | ✅ Via agents |
| Orchestration | ✅ 100% | ✅ Via agents | ✅ Via agents |

### 6.2 MCP Communication Patterns

| Pattern | Implementation | CLI | Web UI |
|---------|----------------|-----|--------|
| **Direct Agent Import** | Import agent classes | ✅ Primary | ✅ Fallback |
| **MCP Server (JSON-RPC)** | Via mcp_server.py | ❌ | ✅ Primary |
| **MCP Client Library** | Via mcp_client.py | ❌ | ✅ Used |
| **Agent Registry** | Centralized lookup | ✅ | ✅ |
| **Contract Discovery** | Capability introspection | ✅ | ✅ |

**Key Insight:** CLI uses direct agent imports, Web UI can use either direct imports OR the MCP server

### 6.3 MCP Server Usage

| MCP Server Feature | Used By CLI | Used By Web | Notes |
|--------------------|-------------|-------------|-------|
| JSON-RPC Interface | ❌ | ✅ | Web primary interface |
| validate_folder method | ❌ | ✅ | Batch validation |
| approve method | ❌ | ✅ | Approval workflow |
| reject method | ❌ | ✅ | Rejection workflow |
| enhance method | ❌ | ✅ | Enhancement via MCP |
| Retry logic | ❌ | ✅ | Resilient operations |
| Fallback simulation | ❌ | ✅ | Graceful degradation |

**MCP Server is Web UI-specific** - CLI doesn't use the MCP server layer

---

## 7. CONFIGURATION AND SETTINGS PARITY

### 7.1 Agent Configuration (config/agent.yaml)

| Setting | CLI Can Use | Web Can Use | CLI Can Modify | Web Can Modify |
|---------|-------------|-------------|----------------|----------------|
| Message timeout | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Agent startup timeout | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Health check interval | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Performance metrics | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Per-agent enabled/disabled | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Cache TTL | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Concurrency limits | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Retry config | ✅ | ✅ | ❌ File edit | ❌ File edit |
| LLM provider settings | ✅ | ✅ | ❌ File edit | ❌ File edit |

**Parity:** Full read parity, no in-app modification in either interface

### 7.2 Enhancement Configuration (config/enhancement.yaml)

| Setting | CLI Can Use | Web Can Use | CLI Can Modify | Web Can Modify |
|---------|-------------|-------------|----------------|----------------|
| require_recommendations | ✅ | ✅ | ❌ File edit | ❌ File edit |
| min_recommendations | ✅ | ✅ | ❌ File edit | ❌ File edit |
| auto_generate_if_missing | ✅ | ✅ | ❌ File edit | ❌ File edit |
| generation_timeout | ✅ | ✅ | ❌ File edit | ❌ File edit |
| auto_apply_confidence_threshold | ✅ | ✅ | ❌ File edit | ❌ File edit |

**Parity:** Full read parity, no in-app modification

### 7.3 Performance Configuration (config/perf.json)

| Setting | CLI Can Use | Web Can Use | CLI Can Modify | Web Can Modify |
|---------|-------------|-------------|----------------|----------------|
| Max concurrent workflows | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Worker pool size | ✅ Via --workers | ✅ | ❌ File edit | ❌ File edit |
| Memory limit | ✅ | ✅ | ❌ File edit | ❌ File edit |
| CPU limit | ✅ | ✅ | ❌ File edit | ❌ File edit |
| File size thresholds | ✅ | ✅ | ❌ File edit | ❌ File edit |
| Response time targets | ✅ | ✅ | ❌ File edit | ❌ File edit |

**Parity:** Full read parity, worker count runtime override in CLI

### 7.4 Validation Configuration

| Setting | CLI Can Set | Web Can Set | Notes |
|---------|-------------|-------------|-------|
| Validation mode | ✅ Env var | ✅ Env var | two_stage/heuristic_only/llm_only |
| Validation types | ✅ --types | ✅ API param | Full parity |
| Confidence threshold | ✅ --confidence | ✅ API param | Full parity |
| LLM thresholds | ✅ Config file | ✅ Config file | No runtime override |
| Downgrade threshold | ❌ | ❌ | Config file only |
| Confirm threshold | ❌ | ❌ | Config file only |
| Upgrade threshold | ❌ | ❌ | Config file only |

**Parity:** Runtime settings have parity, static thresholds require file edits

### 7.5 Truth Data Configuration

| Setting | CLI Can Use | Web Can Use | CLI Can Modify | Web Can Modify |
|---------|-------------|-------------|----------------|----------------|
| Plugin family selection | ✅ --family | ✅ UI/API | ❌ | ❌ |
| Truth file paths | ✅ | ✅ | ❌ File system | ❌ File system |
| Truth data content | ✅ Read | ✅ Read | ❌ File edit | ❌ File edit |
| Plugin patterns | ✅ Read | ✅ Read | ❌ File edit | ❌ File edit |
| Combination rules | ✅ Read | ✅ Read | ❌ File edit | ❌ File edit |

**Parity:** Full read parity, no in-app truth data editing in either interface

### 7.6 Configuration Gaps

**Neither CLI nor Web UI provides:**
- ❌ In-app YAML configuration editing
- ❌ Runtime agent configuration modification
- ❌ Runtime threshold adjustment (beyond CLI flags)
- ❌ Truth data editing interface
- ❌ Plugin pattern management UI

**All configuration changes require:**
- File system access to edit YAML/JSON files
- Application restart (or agent reload for some settings)

---

## 8. RECOMMENDATIONS

### 8.1 High Priority CLI Enhancements

1. **Add Workflow Management Commands** (HIGH)
   ```bash
   tbcv workflows list [--state pending|running|completed]
   tbcv workflows show <workflow_id>
   tbcv workflows cancel <workflow_id>
   tbcv workflows delete <workflow_id> [--bulk]
   ```

2. **Add Validation Management Commands** (HIGH)
   ```bash
   tbcv validations list [--status] [--severity]
   tbcv validations show <validation_id>
   tbcv validations history <file_path>
   tbcv validations approve <validation_id>
   tbcv validations reject <validation_id>
   tbcv validations revalidate <validation_id>
   ```

3. **Enhanced Recommendation Commands** (MEDIUM)
   ```bash
   tbcv recommendations generate <validation_id>
   tbcv recommendations rebuild <validation_id>
   tbcv recommendations delete <recommendation_id>
   tbcv recommendations auto-apply <validation_id> [--threshold 0.95]
   ```

4. **Add System Admin Commands** (MEDIUM)
   ```bash
   tbcv admin cache stats
   tbcv admin cache clear [--l1] [--l2]
   tbcv admin agents status
   tbcv admin agents reload <agent_id>
   tbcv admin health [--full]
   ```

5. **Add Audit/History Commands** (LOW)
   ```bash
   tbcv audit list [--action] [--limit]
   tbcv audit show <recommendation_id>
   ```

### 8.2 Medium Priority Web UI Enhancements

1. **Add Configuration Editor** (MEDIUM)
   - In-app YAML editor for config files
   - Validation before save
   - Diff preview for changes
   - Agent reload trigger

2. **Add Development Utilities** (LOW)
   - Test file creation form
   - API endpoint tester (similar to probe-endpoints)

3. **Add Output Format Options** (LOW)
   - Download validation results in different formats
   - Export workflows as JSON/YAML/CSV

### 8.3 Low Priority Universal Enhancements

1. **Configuration Management System** (MEDIUM)
   - REST API for configuration read/write
   - Version control for config changes
   - Rollback capability
   - Validation before applying

2. **Truth Data Management** (LOW)
   - CRUD interface for plugin definitions
   - Pattern testing/validation
   - Import/export truth data
   - Version control for truth files

3. **Enhanced Monitoring** (LOW)
   - CLI equivalent of Web dashboard stats
   - Prometheus metrics export
   - Grafana dashboard templates

---

## 9. CONCLUSION

### 9.1 Summary Findings

1. **MCP Integration:** 100% complete across all agents ✅
2. **Overall Parity:** 55.6% of features available in both interfaces
3. **Web UI Dominance:** 94.0% feature coverage vs 61.5% CLI coverage
4. **Configuration Parity:** ~85% overlap, with CLI having more runtime controls

### 9.2 Key Strengths

**CLI:**
- ✅ Complete validation and enhancement workflows
- ✅ Comprehensive output format options
- ✅ Low-level runtime controls (cache, logging, etc.)
- ✅ Scriptable and automation-friendly
- ✅ Development utilities (test, probe-endpoints)

**Web UI:**
- ✅ Complete feature coverage for user workflows
- ✅ Real-time monitoring and updates
- ✅ Visual diff and comparison tools
- ✅ Bulk operations and batch processing
- ✅ System administration and maintenance
- ✅ Comprehensive audit and history views

### 9.3 Critical Gaps

**CLI Critical Gaps:**
- Workflow management and control
- Validation approval/rejection workflows
- Historical data viewing
- System administration

**Web UI Minor Gaps:**
- Development utilities
- Custom output formats
- Low-level runtime controls

### 9.4 Strategic Recommendations

**For Production Use:**
- Prioritize CLI workflow management commands
- Add CLI validation management for scripted approvals
- Enhance Web UI configuration management

**For Development:**
- CLI development utilities are sufficient
- Consider adding Web UI test harness

**For Operations:**
- Web UI admin features are comprehensive
- Add CLI equivalents for automation/scripting

### 9.5 Final Assessment

The TBCV application demonstrates:
- ✅ **Excellent MCP integration** - All agents fully MCP-enabled
- ✅ **Strong Web UI** - 94% feature coverage with rich UX
- ⚠️ **Good but incomplete CLI** - 61.5% coverage, missing workflow/admin features
- ✅ **Configuration parity** - Both interfaces can use all settings
- ⚠️ **No in-app configuration editing** - Gap in both interfaces

**Overall Grade:**
- MCP Integration: **A+ (100%)**
- Web UI: **A (94%)**
- CLI: **B- (61.5%)**
- Configuration Parity: **B+ (85%)**

**Primary Recommendation:** Focus on expanding CLI workflow and validation management commands to achieve >80% feature parity for production automation scenarios.

---

*End of Report*
