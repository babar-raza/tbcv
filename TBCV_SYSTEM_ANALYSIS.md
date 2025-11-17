# TBCV System Analysis Report
**Date:** November 5, 2025  
**Analyst:** Claude  
**Focus Areas:** Validation & Enhancement Workflows, Architecture Assessment, Generic Validation Capability

---

## Executive Summary

TBCV is a sophisticated multi-agent content validation and enhancement platform designed primarily for Aspose plugin documentation. The system employs 6 specialized agents coordinated through Model Context Protocol (MCP) to validate content against truth tables and rules. **Critical Issue Identified:** The enhancement button failure is caused by an undefined variable (`enhancements`) in the MCP server's `_enhance()` method (line 263 in `svc/mcp_server.py`).

### Key Findings:
✅ **Strengths:** Well-architected agent system, comprehensive validation logic, extensible truth/rule system  
❌ **Critical Bug:** Enhancement feature is broken due to code error  
⚠️ **Architecture Gap:** Tight coupling to Aspose-specific logic limits generic validation capability  
📊 **Data Flow:** Solid database schema with workflow tracking and caching

---

## 1. System Architecture Overview

### 1.1 Agent Ecosystem (6 Agents, not 7 as claimed)

```
┌────────────────────────────────────────────────────────┐
│                    TBCV Agent Layer                     │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Truth        │  │ Fuzzy        │  │ Content      ││
│  │ Manager      │  │ Detector     │  │ Validator    ││
│  │ Agent        │  │ Agent        │  │ Agent        ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
│         ▲                ▲                  ▲          │
│         │                │                  │          │
│         └────────────────┼──────────────────┘          │
│                          │                             │
│                          ▼                             │
│              ┌──────────────────────┐                  │
│              │   Orchestrator       │                  │
│              │   Agent (Workflow    │                  │
│              │   Coordinator)       │                  │
│              └──────────────────────┘                  │
│                          ▲                             │
│         ┌────────────────┼────────────────┐           │
│         ▼                ▼                ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Code         │  │ Content      │  │ LLM          ││
│  │ Analyzer     │  │ Enhancer     │  │ Validator    ││
│  │ Agent        │  │ Agent        │  │ Agent        ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                         │
└────────────────────────────────────────────────────────┘
```

**ISSUE #1: Agent Count Mismatch**
- README claims 7 agents, but only 6 are defined
- Architecture diagrams show 6 agents consistently
- This is a documentation inconsistency, not a technical issue

### 1.2 Technology Stack
- **Backend:** Python 3.12+, FastAPI, SQLAlchemy
- **Database:** SQLite with comprehensive indexing
- **Caching:** Two-level (L1 memory LRU + L2 persistent SQLite)
- **Communication:** REST API, WebSocket (real-time updates), CLI
- **AI Integration:** Ollama for LLM-based validation/enhancement

---

## 2. Validation Flow Deep Dive

### 2.1 Validation Request Journey

```
User Request → FastAPI Endpoint → Orchestrator Agent
                                        ↓
                    ┌───────────────────┴─────────────────┐
                    ▼                                     ▼
            Truth Manager Agent                  Fuzzy Detector Agent
         (Load plugin definitions)             (Detect plugin usage)
                    │                                     │
                    └──────────────┬──────────────────────┘
                                   ▼
                        Content Validator Agent
                    (5 validation types + LLM)
                                   ↓
                          Database Storage
                                   ↓
                          Validation Result
```

### 2.2 Validation Components

#### A. Truth Manager Agent (`agents/truth_manager.py`)
**Responsibilities:**
- Load plugin truth data from JSON files (`truth/words.json`)
- B-tree indexing for O(log n) plugin lookups
- SHA-256 versioning for change detection
- Pattern compilation and caching

**Current Implementation:**
- ✅ Well-structured plugin definitions with metadata
- ✅ Efficient indexing mechanism
- ✅ Support for combination rules (e.g., "Converter requires Word Processor + PDF Processor")

**Truth Data Structure:**
```json
{
  "product": "Aspose.Words Plugins (.NET)",
  "core_rules": [
    "Feature plugins NEVER work alone...",
    "Load DOCX → Save PDF: requires Word Processor + PDF Processor + Converter"
  ],
  "plugins": [
    {
      "name": "Document Converter",
      "type": "feature",
      "works_alone": false,
      "requires": "Source and target File Processor plugins"
    }
  ]
}
```

#### B. Fuzzy Detector Agent (`agents/fuzzy_detector.py`)
**Responsibilities:**
- Multi-algorithm fuzzy matching (Levenshtein, Jaro-Winkler, Ratio)
- Context-aware detection with configurable windows
- Confidence scoring (default threshold: 85%)

**Algorithm Details:**
- Uses multiple fuzzy matching algorithms for robust detection
- Configurable similarity thresholds per family
- Pattern-based detection with regex support

#### C. Content Validator Agent (`agents/content_validator.py`)
**Responsibilities:**
- **6 Validation Types:**
  1. **YAML** - Frontmatter validation against truth/rule constraints
  2. **Markdown** - Structure analysis (headings, lists, code blocks)
  3. **Code** - Pattern matching for API usage, security issues
  4. **Links** - URL accessibility validation
  5. **Structure** - Document hierarchy and organization
  6. **LLM** - AI-powered contextual validation (via Ollama)

**Current Flow:**
```python
async def handle_validate_content(params):
    # 1. Load context
    truth_context = await self._load_truth_context(family)
    rule_context = await self._load_rule_context(family)
    plugin_context = await self._get_plugin_context(content, family)
    
    # 2. Run validations
    for validation_type in ["yaml", "markdown", "code", "links", "structure"]:
        result = await self._validate_X(content, contexts...)
        all_issues.extend(result.issues)
    
    # 3. Store results
    await self._store_validation_result(...)
    
    return validation_result
```

**Issues with Current Implementation:**
```python
# Line 158-160 in content_validator.py
truth_context = await self._load_truth_context(family)
rule_context = await self._load_rule_context(family)
plugin_context = await self._get_plugin_context(content, family)
```

**ISSUE #2: Context Loading May Be Incomplete**
- `_load_truth_context()` and `_load_rule_context()` are marked as "stubs" in comments
- May not fully implement generic rule loading for non-Aspose families
- Need to verify these methods actually load from `truth/` and `rules/` directories

### 2.3 Rules System (`rules/words.json`)

**Current Structure:**
```json
{
  "plugin_aliases": {
    "word_processor": ["Word Processor", "Words", "Document"]
  },
  "api_patterns": {
    "document_creation": ["new Document\\(", "var\\s+\\w+\\s*=\\s*new Document"],
    "save_operations": ["\\.Save\\s*\\(", "SaveFormat\\."]
  },
  "dependencies": {
    "document_converter": ["word_processor"],
    "pdf_processor": ["document_converter"]
  },
  "code_quality_rules": {
    "forbidden_patterns": {
      "hardcoded_paths": ["C:\\\\", "/Users/"],
      "magic_numbers": ["\\b\\d{3,}\\b"]
    }
  }
}
```

**Analysis:**
✅ Well-organized rule categories  
✅ Regex-based pattern matching  
✅ Dependency tracking  
❌ **Tightly coupled to Aspose/C# patterns** - limits generic use

---

## 3. Enhancement Flow Analysis

### 3.1 Enhancement Request Journey

```
User clicks "Enhance" → API /api/enhance/{validation_id}
                              ↓
                    MCP Server._enhance()
                              ↓
                    [BUG HERE: Line 263]
                              ↓
                    Load validation record
                              ↓
                    Read original file
                              ↓
                    Call Ollama LLM for enhancement
                              ↓
                    Write enhanced content
                              ↓
                    Update validation status
```

### 3.2 CRITICAL BUG IDENTIFIED 🐛

**Location:** `svc/mcp_server.py`, line 263

```python
def _enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
    ids = params.get("ids", [])
    enhanced_count = 0
    errors = []
    
    for validation_id in ids:
        try:
            # ... validation logic ...
            # ... enhancement logic ...
            
            enhanced_count += 1
            enhancements.append(audit_entry)  # ❌ BUG: 'enhancements' undefined!
            
        except Exception as e:
            errors.append(f"Error enhancing {validation_id}: {str(e)}")
    
    return {
        "success": True,
        "enhanced_count": enhanced_count,
        "errors": errors
    }
```

**Problem:** Variable `enhancements` is never initialized before line 263

**Fix Required:**
```python
def _enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
    ids = params.get("ids", [])
    enhanced_count = 0
    errors = []
    enhancements = []  # ✅ ADD THIS LINE
    
    for validation_id in ids:
        # ... rest of the logic
```

**Impact:** Every click of the "Enhance" button will throw a `NameError` and fail

### 3.3 Content Enhancer Agent (`agents/content_enhancer.py`)

**Responsibilities:**
- First-occurrence plugin linking (prevents over-linking)
- Configurable link templates
- Format fixing (headings, code blocks, lists)
- **NEW:** Consumes validation results for guided enhancements

**Enhancement Types:**
1. **Plugin Links** - Add markdown links to plugin documentation
2. **Info Text** - Insert contextual information about plugin usage
3. **Format Fixes** - Standardize markdown formatting

**Validation Integration:**
```python
def _collect_validation_issues(self, file_path: Optional[str], severity_floor: str):
    if not file_path:
        return []
    
    rows = list_validation_results(file_path=file_path, limit=25)
    issues = []
    
    for r in rows:
        for item in (r.validation_results or []):
            sev = item.get("level", "info")
            if severity_meets_floor(sev, severity_floor):
                issues.append(item)
    
    return issues
```

**ISSUE #3: Enhancement Logic Incomplete**
- Enhancer agent reads validation results but doesn't fully use them
- The MCP server's `_enhance()` method uses Ollama directly without calling the ContentEnhancerAgent
- **Architecture inconsistency:** Should agent handle enhancement or MCP server?

---

## 4. Database Schema Analysis

### 4.1 Core Tables

#### Workflows Table
```sql
CREATE TABLE workflows (
    id VARCHAR(36) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    state ENUM('pending','running','paused','completed','failed','cancelled'),
    input_params TEXT,  -- JSON
    metadata TEXT,      -- JSON
    total_steps INTEGER,
    current_step INTEGER,
    progress_percent INTEGER,
    error_message TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    completed_at DATETIME
);
```

**Analysis:**
✅ Comprehensive workflow tracking  
✅ Progress monitoring capability  
✅ Proper indexing on state and created_at

#### ValidationResult Table
```sql
CREATE TABLE validation_results (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) REFERENCES workflows(id),
    file_path VARCHAR(1024),
    rules_applied TEXT,        -- JSON
    validation_results TEXT,   -- JSON
    notes TEXT,
    severity VARCHAR(20),
    status ENUM('pass','fail','warning','skipped','approved','rejected','enhanced'),
    content_hash VARCHAR(64),
    ast_hash VARCHAR(64),
    run_id VARCHAR(64),
    created_at DATETIME,
    updated_at DATETIME
);
```

**Analysis:**
✅ Strong schema design with proper foreign keys  
✅ Content hashing for change detection  
✅ Status tracking for approval workflow  
✅ Flexible JSON storage for dynamic validation results

**ISSUE #4: Missing Indexes**
- No index on `run_id` despite being used for batch filtering
- No composite index on `(workflow_id, status)` for common queries

#### Recommendation Table
```sql
CREATE TABLE recommendations (
    id VARCHAR(36) PRIMARY KEY,
    validation_id VARCHAR(36) REFERENCES validation_results(id),
    recommendation_type VARCHAR(50),
    description TEXT,
    automated_fix TEXT,  -- JSON
    confidence_score FLOAT,
    status ENUM('pending','accepted','rejected','applied'),
    created_at DATETIME,
    reviewed_at DATETIME
);
```

**Analysis:**
✅ Human-in-the-loop approval workflow supported  
✅ Automated fix suggestions stored  
❌ **Not integrated with enhancement flow** - recommendations exist but aren't consumed by enhancer

---

## 5. Generic Validation Assessment

### 5.1 Current State: Aspose-Specific

**Evidence of Tight Coupling:**

1. **Truth Files:** `truth/words.json` contains Aspose.Words specific plugins
2. **Rules:** `rules/words.json` has C# API patterns (`new Document\(`, `SaveFormat\.`)
3. **Code Analyzer:** Hardcoded Aspose pattern detection
4. **Validation Logic:** References to "Document", "SaveFormat", etc.

### 5.2 Path to Generic Validation

**Required Changes:**

#### A. Abstract the Family System
```python
# Current: Hardcoded "words" family
truth_context = await self._load_truth_context(family="words")

# Needed: Dynamic family loading
truth_context = await self._load_truth_context(family=user_specified_family)
```

#### B. Generalize Truth Schema
```json
{
  "family": "generic",  // or "python", "javascript", etc.
  "product": "Any Product",
  "entities": [  // was "plugins"
    {
      "name": "Entity Name",
      "type": "feature|component|library",
      "patterns": ["regex1", "regex2"],
      "dependencies": ["other_entity"]
    }
  ],
  "rules": [
    "Generic validation rule 1",
    "Generic validation rule 2"
  ]
}
```

#### C. Language-Agnostic Pattern Matching
```python
# Current: C#-specific
"api_patterns": {
    "document_creation": ["new Document\\("]
}

# Needed: Language templates
"api_patterns": {
    "csharp": {
        "class_instantiation": ["new {class}\\("]
    },
    "python": {
        "class_instantiation": ["{class}\\("]
    },
    "javascript": {
        "class_instantiation": ["new {class}\\(", "const .* = {class}\\("]
    }
}
```

### 5.3 Generic Validation Architecture Proposal

```
┌────────────────────────────────────────────────────┐
│           Generic Validation Engine                 │
├────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐      ┌──────────────────┐  │
│  │  Family Registry │      │  Rule Compiler   │  │
│  │  - Load families │      │  - Parse rules   │  │
│  │  - Validate      │      │  - Generate      │  │
│  │    schema        │      │    validators    │  │
│  └──────────────────┘      └──────────────────┘  │
│            │                         │             │
│            └──────────┬──────────────┘             │
│                       ▼                            │
│            ┌──────────────────┐                    │
│            │  Pattern Matcher │                    │
│            │  - Multi-language│                    │
│            │  - Fuzzy matching│                    │
│            │  - AST analysis  │                    │
│            └──────────────────┘                    │
│                       │                            │
│                       ▼                            │
│            ┌──────────────────┐                    │
│            │ Validation Engine│                    │
│            │ - Execute rules  │                    │
│            │ - Generate issues│                    │
│            └──────────────────┘                    │
│                                                     │
└────────────────────────────────────────────────────┘
```

---

## 6. System Issues & Gaps Summary

### 6.1 CRITICAL ISSUES (Fix Immediately)

| Issue | Location | Impact | Fix Complexity |
|-------|----------|--------|----------------|
| **Enhancement button breaks** | `svc/mcp_server.py:263` | HIGH - Feature unusable | LOW - 1 line |
| **Agent count mismatch** | `README.md` | LOW - Documentation only | LOW - Update docs |

### 6.2 MAJOR ISSUES (Address Soon)

| Issue | Location | Impact | Fix Complexity |
|-------|----------|--------|----------------|
| **Tight Aspose coupling** | Throughout codebase | MEDIUM - Limits generic use | HIGH - Major refactor |
| **Incomplete context loading** | `content_validator.py:299-320` | MEDIUM - May not load all rules | MEDIUM - Implement loaders |
| **Enhancement architecture gap** | `svc/mcp_server.py` vs `content_enhancer.py` | MEDIUM - Inconsistent design | MEDIUM - Choose one approach |
| **Unused recommendations** | `core/database.py` | LOW - Wasted feature | MEDIUM - Integrate with enhancer |

### 6.3 MINOR ISSUES (Nice to Have)

| Issue | Location | Impact | Fix Complexity |
|-------|----------|--------|----------------|
| **Missing database indexes** | `core/database.py` | LOW - Performance | LOW - Add indexes |
| **Hardcoded thresholds** | `agents/fuzzy_detector.py` | LOW - Inflexible | LOW - Move to config |
| **Limited error details** | Various agents | LOW - Harder debugging | MEDIUM - Enhance logging |

---

## 7. Loopholes & Missing Components

### 7.1 Security Loopholes

**No Authentication/Authorization**
- API endpoints are completely open
- No user management or access control
- Any user can enhance/approve/reject validations

**SQL Injection Risk (Low)**
- Using SQLAlchemy ORM properly
- But raw SQL in some places (e.g., `tools/` scripts)

**File System Access**
- Enhancement writes directly to file system
- No validation of file paths
- Could potentially overwrite unintended files

### 7.2 Missing Components

**1. Version Control Integration**
- No Git integration for tracking changes
- Enhanced files overwrite originals without backup
- Can't rollback enhancements

**2. User Management**
- No concept of users or roles
- No audit trail of who approved/enhanced what
- Database has no user_id fields

**3. Configuration Validation**
- Truth and rule JSON files have no schema validation
- Invalid JSON crashes the system
- No validation of regex patterns in rules

**4. Batch Enhancement**
- Batch validation exists, but no batch enhancement
- Have to enhance files one by one
- Inefficient for large documentation sets

**5. API Rate Limiting**
- No rate limiting on expensive operations
- Could DOS the system with validation requests
- Ollama calls have no throttling

**6. Testing Coverage**
- Only smoke tests and basic unit tests
- No integration tests for full workflows
- Enhancement feature has minimal test coverage

### 7.3 Operational Gaps

**No Monitoring/Alerting**
- Basic metrics exist but no alerting
- No dashboards for system health
- WebSocket updates but no persistent logs for ops team

**No Backup/Recovery**
- SQLite database has no automated backups
- Enhanced files overwrite originals
- No disaster recovery plan

**No Multi-Tenancy**
- Single database for all users
- No tenant isolation
- Can't separate different teams' validations

---

## 8. Recommendations

### 8.1 Immediate Actions (Fix the Bug!)

```python
# File: svc/mcp_server.py
# Line: ~185

def _enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
    ids = params.get("ids", [])
    enhanced_count = 0
    errors = []
    enhancements = []  # ✅ ADD THIS LINE
    
    # ... rest of the method
```

### 8.2 Short-Term Improvements (Next Sprint)

1. **Complete Context Loading**
   - Implement `_load_truth_context()` and `_load_rule_context()` properly
   - Ensure they dynamically load from `truth/` and `rules/` directories
   - Add schema validation for truth/rule JSON files

2. **Add Database Indexes**
   ```sql
   CREATE INDEX idx_validation_run_id ON validation_results(run_id);
   CREATE INDEX idx_validation_workflow_status ON validation_results(workflow_id, status);
   CREATE INDEX idx_recommendations_validation_status ON recommendations(validation_id, status);
   ```

3. **Integrate Recommendations with Enhancement**
   - Modify MCP server to call ContentEnhancerAgent
   - Pass validation issues and recommendations to enhancer
   - Apply only approved recommendations

### 8.3 Medium-Term Refactoring (Next Quarter)

1. **Generic Validation Framework**
   - Create abstract base classes for Family, Entity, Rule
   - Implement dynamic family loading
   - Add language-specific pattern matchers

2. **Enhanced Security**
   - Add API authentication (API keys or OAuth)
   - Implement role-based access control
   - Add file path validation and sandboxing

3. **Batch Enhancement**
   - Implement batch enhancement endpoint
   - Add progress tracking via WebSocket
   - Support parallel enhancement with worker pools

### 8.4 Long-Term Vision (6-12 Months)

1. **Multi-Tenancy Support**
   - Add organization/team concept
   - Separate databases or tenant_id columns
   - Row-level security

2. **Version Control Integration**
   - Git integration for tracking changes
   - Create branches for enhancements
   - Pull request automation

3. **Advanced AI Features**
   - Fine-tune LLMs on documentation corpus
   - Implement reinforcement learning from human feedback
   - Multi-modal validation (images, diagrams)

---

## 9. Generic Validation Migration Path

### Phase 1: Foundation (2-3 weeks)
- [ ] Fix enhancement bug
- [ ] Create generic truth schema specification
- [ ] Implement schema validator for truth/rule files
- [ ] Add family registry system

### Phase 2: Abstraction (4-6 weeks)
- [ ] Refactor TruthManagerAgent for generic families
- [ ] Create language-agnostic pattern matcher
- [ ] Implement template system for rules
- [ ] Add support for Python, JavaScript families

### Phase 3: Migration (2-3 weeks)
- [ ] Convert existing "words" family to new schema
- [ ] Create migration scripts for truth/rule files
- [ ] Update all agents to use generic interfaces
- [ ] Comprehensive testing

### Phase 4: Validation (1-2 weeks)
- [ ] Test with multiple families
- [ ] Performance benchmarking
- [ ] Documentation updates
- [ ] User acceptance testing

---

## 10. Conclusion

### Overall Assessment: B+ Architecture, A- Implementation (with one critical bug)

**Strengths:**
- Well-designed multi-agent architecture
- Solid database schema with proper relationships
- Good separation of concerns between agents
- Comprehensive validation capabilities
- Extensible truth/rule system

**Weaknesses:**
- Enhancement feature is broken (critical bug)
- Tight coupling to Aspose-specific patterns
- Missing operational features (auth, monitoring, backups)
- Incomplete integration between components
- Limited test coverage

### Generic Validation Capability: Currently 30%, Can Be 90%

The system has excellent bones for generic validation. The agent architecture, truth/rule separation, and workflow management are all generic-ready. The main barrier is the Aspose-specific patterns hardcoded throughout. With focused refactoring (estimated 6-8 weeks), this could become a powerful generic validation platform.

### Next Steps:
1. **Fix the enhancement bug** (30 minutes)
2. **Test enhancement flow end-to-end** (1 day)
3. **Design generic truth schema** (1 week)
4. **Prototype with new family** (2 weeks)
5. **Decide on full migration** (after prototype validation)

---

## Appendix A: File Structure Analysis

```
tbcv/
├── agents/           # ✅ Well-organized, clear responsibilities
│   ├── base.py                  # Agent base class with MCP
│   ├── truth_manager.py         # Plugin truth data
│   ├── fuzzy_detector.py        # Pattern matching
│   ├── content_validator.py     # 6 validation types
│   ├── content_enhancer.py      # Enhancement logic
│   ├── code_analyzer.py         # Code analysis
│   └── orchestrator.py          # Workflow coordination
├── api/              # ✅ FastAPI server, well-structured
│   ├── server.py                # Main API endpoints
│   ├── dashboard.py             # Web UI
│   ├── websocket_endpoints.py   # Real-time updates
│   └── export_endpoints.py      # CSV/JSON exports
├── core/             # ✅ Solid infrastructure
│   ├── database.py              # SQLAlchemy models
│   ├── cache.py                 # Two-level caching
│   ├── config.py                # Configuration
│   ├── logging.py               # Structured logging
│   ├── rule_manager.py          # Rule loading
│   └── validation_store.py      # Validation persistence
├── svc/              # ⚠️ MCP server (has bug)
│   └── mcp_server.py            # JSON-RPC interface
├── truth/            # ✅ Plugin truth tables
│   └── words.json               # Aspose.Words definitions
├── rules/            # ✅ Validation rules
│   └── words.json               # Aspose.Words rules
├── cli/              # ✅ Command-line interface
│   └── main.py                  # CLI commands
├── tests/            # ⚠️ Limited coverage
│   ├── test_smoke_agents.py
│   ├── test_enhancer_consumes_validation.py
│   └── test_everything.py
└── templates/        # ✅ Web dashboard templates
    ├── validations_list.html
    ├── validation_detail.html
    └── dashboard_home.html
```

---

## Appendix B: API Endpoint Inventory

### Validation Endpoints
- `POST /api/validate/content` - Validate single content
- `POST /api/validate/file` - Validate single file
- `POST /api/validate/batch` - Batch validation
- `GET /api/validations` - List validations
- `GET /api/validations/{id}` - Get validation details

### Enhancement Endpoints (🐛 BROKEN)
- `POST /api/enhance/{validation_id}` - Enhance single validation
- `POST /api/validations/bulk/enhance` - Bulk enhancement

### Workflow Endpoints
- `POST /api/approve/{validation_id}` - Approve validation
- `POST /api/reject/{validation_id}` - Reject validation
- `POST /api/validations/bulk/approve` - Bulk approve
- `POST /api/validations/bulk/reject` - Bulk reject

### Dashboard Endpoints
- `GET /dashboard` - Main dashboard
- `GET /dashboard/workflows` - Workflow monitor
- `GET /dashboard/agents` - Agent status
- `GET /dashboard/logs` - Audit logs

### Agent Endpoints
- `POST /agents/validate` - Direct agent validation
- `POST /agents/enhance` - Direct agent enhancement
- `GET /agents/status` - All agents status
- `POST /agents/{agent_id}/ping` - Ping specific agent

---

**End of Analysis Report**
