# TBCV API Examples

Comprehensive examples for all TBCV API endpoints with complete request/response samples in curl, Python, and JavaScript.

## Quick Start

### Basic Setup

**Python**:
```python
import requests
import json

BASE_URL = "http://localhost:8080"
headers = {"Content-Type": "application/json"}
```

**JavaScript**:
```javascript
const BASE_URL = "http://localhost:8080";
const headers = { "Content-Type": "application/json" };
```

**Bash**:
```bash
BASE_URL="http://localhost:8080"
```

---

## Health Check Examples

### Check System Health

**curl**:
```bash
curl -X GET http://localhost:8080/health \
  -H "Content-Type: application/json"
```

**Python**:
```python
response = requests.get(f"{BASE_URL}/health")
status = response.json()
print(f"System status: {status['status']}")
print(f"Agents registered: {status['agents_registered']}")
```

**JavaScript**:
```javascript
const response = await fetch(`${BASE_URL}/health`);
const status = await response.json();
console.log(`System status: ${status.status}`);
console.log(`Agents registered: ${status.agents_registered}`);
```

**Success Response (200)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-03T10:30:00.000Z",
  "agents_registered": 11,
  "database_connected": true,
  "schema_present": true,
  "version": "2.0.0"
}
```

---

## Validation Examples

### 1. Inline Content Validation

**Description**: Validate content directly without saving to a file.

**curl**:
```bash
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "---\ntitle: My Document\nauthor: John Doe\n---\n# Welcome\n\nThis is my document with AutoSave feature.",
    "file_path": "docs/welcome.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "truth", "links"]
  }'
```

**Python**:
```python
payload = {
    "content": "---\ntitle: My Document\nauthor: John Doe\n---\n# Welcome\n\nThis is my document with AutoSave feature.",
    "file_path": "docs/welcome.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "truth", "links"]
}
response = requests.post(f"{BASE_URL}/api/validate", json=payload)
result = response.json()
print(f"Validation ID: {result['validation_id']}")
print(f"Status: {result['status']}")
print(f"Issues found: {len(result.get('issues', []))}")
```

**JavaScript**:
```javascript
const payload = {
  content: "---\ntitle: My Document\nauthor: John Doe\n---\n# Welcome\n\nThis is my document with AutoSave feature.",
  file_path: "docs/welcome.md",
  family: "words",
  validation_types: ["yaml", "markdown", "truth", "links"]
};

const response = await fetch(`${BASE_URL}/api/validate`, {
  method: "POST",
  headers,
  body: JSON.stringify(payload)
});
const result = await response.json();
console.log(`Validation ID: ${result.validation_id}`);
console.log(`Status: ${result.status}`);
```

**Success Response (200)**:
```json
{
  "validation_id": "val-abc12345",
  "file_path": "docs/welcome.md",
  "status": "pass",
  "confidence": 0.92,
  "issues": [
    {
      "level": "warning",
      "category": "truth",
      "message": "Plugin 'AutoSave' detected but no documentation link provided",
      "line": 7,
      "suggestion": "Add link to AutoSave documentation: [AutoSave](https://example.com/autosave)"
    }
  ],
  "plugins_detected": 1,
  "plugins_declared": 0,
  "recommendations_generated": 3
}
```

**Error Response (422)**:
```json
{
  "error": "Validation failed",
  "type": "ValidationError",
  "validation_errors": [
    {
      "loc": ["body", "file_path"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### 2. Batch Validation

**Description**: Validate multiple files in a batch workflow.

**curl**:
```bash
curl -X POST http://localhost:8080/api/validate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      "docs/guide1.md",
      "docs/guide2.md",
      "docs/tutorial.md"
    ],
    "family": "words",
    "validation_types": ["yaml", "markdown", "truth"],
    "max_workers": 4
  }'
```

**Python**:
```python
payload = {
    "files": ["docs/guide1.md", "docs/guide2.md", "docs/tutorial.md"],
    "family": "words",
    "validation_types": ["yaml", "markdown", "truth"],
    "max_workers": 4
}
response = requests.post(f"{BASE_URL}/api/validate/batch", json=payload)
result = response.json()
print(f"Job ID: {result['job_id']}")
print(f"Workflow ID: {result['workflow_id']}")
print(f"Total files: {result['files_total']}")
```

**JavaScript**:
```javascript
const payload = {
  files: ["docs/guide1.md", "docs/guide2.md", "docs/tutorial.md"],
  family: "words",
  validation_types: ["yaml", "markdown", "truth"],
  max_workers: 4
};

const response = await fetch(`${BASE_URL}/api/validate/batch`, {
  method: "POST",
  headers,
  body: JSON.stringify(payload)
});
const result = await response.json();
console.log(`Job ID: ${result.job_id}`);
console.log(`Workflow ID: ${result.workflow_id}`);
```

**Success Response (202)**:
```json
{
  "job_id": "job-xyz789",
  "workflow_id": "wf-abc123",
  "status": "started",
  "files_total": 3,
  "files_validated": 0,
  "files_failed": 0
}
```

---

### 3. Detect Plugins

**Description**: Detect plugins in content without full validation.

**curl**:
```bash
curl -X POST http://localhost:8080/api/detect-plugins \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Enable AutoSave and Track Changes features. Use Find and Replace for bulk edits.",
    "family": "words"
  }'
```

**Python**:
```python
payload = {
    "content": "Enable AutoSave and Track Changes features. Use Find and Replace for bulk edits.",
    "family": "words"
}
response = requests.post(f"{BASE_URL}/api/detect-plugins", json=payload)
plugins = response.json()
for plugin in plugins['plugins_detected']:
    print(f"- {plugin['plugin_name']}: {plugin['confidence']:.2%}")
```

**JavaScript**:
```javascript
const payload = {
  content: "Enable AutoSave and Track Changes features. Use Find and Replace for bulk edits.",
  family: "words"
};

const response = await fetch(`${BASE_URL}/api/detect-plugins`, {
  method: "POST",
  headers,
  body: JSON.stringify(payload)
});
const result = await response.json();
result.plugins_detected.forEach(plugin => {
  console.log(`- ${plugin.plugin_name}: ${(plugin.confidence * 100).toFixed(2)}%`);
});
```

**Success Response (200)**:
```json
{
  "plugins_detected": [
    {
      "plugin_name": "AutoSave",
      "confidence": 0.95,
      "method": "fuzzy_detection"
    },
    {
      "plugin_name": "Track Changes",
      "confidence": 0.88,
      "method": "pattern_match"
    },
    {
      "plugin_name": "Find and Replace",
      "confidence": 0.82,
      "method": "keyword_match"
    }
  ],
  "total_count": 3
}
```

---

## Results and Recommendations Examples

### 4. List Validations with Filtering

**Description**: Retrieve validation results with various filters and pagination.

**curl**:
```bash
# Get failed validations from words family
curl -X GET "http://localhost:8080/api/validations?status=fail&family=words&limit=20&offset=0" \
  -H "Content-Type: application/json"

# Get validations with errors from past 24 hours
curl -X GET "http://localhost:8080/api/validations?severity=error&limit=50" \
  -H "Content-Type: application/json"
```

**Python**:
```python
# Get validations with specific status and severity
params = {
    "status": "completed",
    "severity": "error",
    "family": "words",
    "limit": 20,
    "offset": 0
}
response = requests.get(f"{BASE_URL}/api/validations", params=params)
results = response.json()
print(f"Total validations: {results['total']}")
for validation in results['results']:
    print(f"- {validation['file_path']}: {validation['status']}")
```

**JavaScript**:
```javascript
const params = new URLSearchParams({
  status: "completed",
  severity: "error",
  family: "words",
  limit: 20,
  offset: 0
});

const response = await fetch(`${BASE_URL}/api/validations?${params}`);
const results = await response.json();
console.log(`Total validations: ${results.total}`);
results.results.forEach(validation => {
  console.log(`- ${validation.file_path}: ${validation.status}`);
});
```

**Success Response (200)**:
```json
{
  "results": [
    {
      "id": "val-123",
      "file_path": "docs/tutorial.md",
      "status": "completed",
      "family": "words",
      "created_at": "2025-12-03T10:30:00.000Z",
      "validation_results": {
        "content_validation": {
          "confidence": 0.85,
          "issues_count": 3
        },
        "fuzzy_detection": {
          "plugins_detected": 2
        }
      },
      "recommendations_count": 5
    },
    {
      "id": "val-456",
      "file_path": "docs/guide.md",
      "status": "completed",
      "family": "words",
      "created_at": "2025-12-03T10:25:00.000Z",
      "validation_results": {
        "content_validation": {
          "confidence": 0.92,
          "issues_count": 1
        },
        "fuzzy_detection": {
          "plugins_detected": 1
        }
      },
      "recommendations_count": 2
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

---

### 5. Get Validation Details

**Description**: Retrieve detailed information about a specific validation result.

**curl**:
```bash
curl -X GET http://localhost:8080/api/validations/val-abc123 \
  -H "Content-Type: application/json"
```

**Python**:
```python
validation_id = "val-abc123"
response = requests.get(f"{BASE_URL}/api/validations/{validation_id}")
validation = response.json()
print(f"File: {validation['validation']['file_path']}")
print(f"Status: {validation['validation']['status']}")
print(f"Issues: {len(validation['validation']['validation_results']['content_validation']['issues'])}")
print(f"Recommendations: {len(validation['recommendations'])}")
```

**JavaScript**:
```javascript
const validationId = "val-abc123";
const response = await fetch(`${BASE_URL}/api/validations/${validationId}`);
const validation = await response.json();
console.log(`File: ${validation.validation.file_path}`);
console.log(`Status: ${validation.validation.status}`);
console.log(`Issues: ${validation.validation.validation_results.content_validation.issues.length}`);
```

**Success Response (200)**:
```json
{
  "validation": {
    "id": "val-123",
    "file_path": "docs/tutorial.md",
    "family": "words",
    "status": "completed",
    "created_at": "2025-12-03T10:30:00.000Z",
    "validation_results": {
      "content_validation": {
        "confidence": 0.85,
        "issues": [
          {
            "level": "error",
            "category": "yaml",
            "message": "Missing required field 'description'",
            "line": 2,
            "suggestion": "Add 'description: Brief description' to frontmatter"
          },
          {
            "level": "warning",
            "category": "truth",
            "message": "Plugin 'AutoSave' not documented",
            "line": 15,
            "suggestion": "Add plugin documentation link"
          }
        ]
      },
      "fuzzy_detection": {
        "plugins_detected": [
          {
            "name": "AutoSave",
            "confidence": 0.95
          }
        ]
      },
      "llm_validation": {
        "confidence": 0.78,
        "semantic_issues": []
      }
    }
  },
  "recommendations": [
    {
      "id": "rec-456",
      "status": "proposed",
      "severity": "high",
      "type": "plugin_link",
      "instruction": "Add hyperlink for AutoSave plugin",
      "confidence": 0.9,
      "created_at": "2025-12-03T10:30:00.000Z"
    }
  ]
}
```

---

### 6. List Recommendations

**Description**: Query recommendations with filtering by status, validation, type, and severity.

**curl**:
```bash
# Get all proposed recommendations for a specific validation
curl -X GET "http://localhost:8080/api/recommendations?validation_id=val-123&status=proposed&limit=10" \
  -H "Content-Type: application/json"

# Get high-severity recommendations
curl -X GET "http://localhost:8080/api/recommendations?severity=high&status=approved" \
  -H "Content-Type: application/json"
```

**Python**:
```python
params = {
    "validation_id": "val-123",
    "status": "proposed",
    "severity": "high",
    "limit": 20
}
response = requests.get(f"{BASE_URL}/api/recommendations", params=params)
recommendations = response.json()
print(f"Total recommendations: {recommendations['total']}")
for rec in recommendations['recommendations']:
    print(f"[{rec['severity'].upper()}] {rec['instruction']}")
```

**JavaScript**:
```javascript
const params = new URLSearchParams({
  validation_id: "val-123",
  status: "proposed",
  severity: "high",
  limit: 20
});

const response = await fetch(`${BASE_URL}/api/recommendations?${params}`);
const recommendations = await response.json();
recommendations.recommendations.forEach(rec => {
  console.log(`[${rec.severity.toUpperCase()}] ${rec.instruction}`);
});
```

**Success Response (200)**:
```json
{
  "recommendations": [
    {
      "id": "rec-123",
      "validation_id": "val-123",
      "status": "proposed",
      "type": "plugin_link",
      "severity": "high",
      "instruction": "Add hyperlink for AutoSave plugin at line 15",
      "rationale": "First mention of AutoSave should be hyperlinked to documentation",
      "confidence": 0.95,
      "created_at": "2025-12-03T10:30:00.000Z"
    },
    {
      "id": "rec-124",
      "validation_id": "val-123",
      "status": "proposed",
      "type": "info_text",
      "severity": "medium",
      "instruction": "Add explanation of Track Changes feature",
      "rationale": "Feature is mentioned but not explained",
      "confidence": 0.82,
      "created_at": "2025-12-03T10:30:30.000Z"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

---

### 7. Review Single Recommendation

**Description**: Approve or reject a specific recommendation.

**curl**:
```bash
curl -X POST http://localhost:8080/api/recommendations/rec-456/review \
  -H "Content-Type: application/json" \
  -d '{
    "status": "accepted",
    "reviewer": "editor@example.com",
    "notes": "Approved for documentation v2.0 release"
  }'
```

**Python**:
```python
payload = {
    "status": "accepted",
    "reviewer": "editor@example.com",
    "notes": "Approved for documentation v2.0 release"
}
response = requests.post(
    f"{BASE_URL}/api/recommendations/rec-456/review",
    json=payload
)
result = response.json()
print(f"Status: {'✓ Approved' if result['success'] else '✗ Failed'}")
print(f"Recommendation: {result['recommendation_id']}")
print(f"New status: {result['status']}")
```

**JavaScript**:
```javascript
const payload = {
  status: "accepted",
  reviewer: "editor@example.com",
  notes: "Approved for documentation v2.0 release"
};

const response = await fetch(
  `${BASE_URL}/api/recommendations/rec-456/review`,
  {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  }
);
const result = await response.json();
console.log(`Status: ${result.success ? "✓ Approved" : "✗ Failed"}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "recommendation_id": "rec-456",
  "status": "approved",
  "reviewed_at": "2025-12-03T10:35:00.000Z"
}
```

---

### 8. Bulk Review Recommendations

**Description**: Approve or reject multiple recommendations at once.

**curl**:
```bash
curl -X POST http://localhost:8080/api/recommendations/bulk-review \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": ["rec-123", "rec-124", "rec-125"],
    "action": "accepted",
    "reviewer": "editor@example.com",
    "notes": "Bulk approval for release 2.0"
  }'
```

**Python**:
```python
payload = {
    "recommendation_ids": ["rec-123", "rec-124", "rec-125"],
    "action": "accepted",
    "reviewer": "editor@example.com",
    "notes": "Bulk approval for release 2.0"
}
response = requests.post(
    f"{BASE_URL}/api/recommendations/bulk-review",
    json=payload
)
result = response.json()
print(f"Processed: {result['processed']}")
print(f"Approved: {result['accepted']}")
print(f"Rejected: {result['rejected']}")
```

**JavaScript**:
```javascript
const payload = {
  recommendation_ids: ["rec-123", "rec-124", "rec-125"],
  action: "accepted",
  reviewer: "editor@example.com",
  notes: "Bulk approval for release 2.0"
};

const response = await fetch(
  `${BASE_URL}/api/recommendations/bulk-review`,
  {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  }
);
const result = await response.json();
console.log(`Processed: ${result.processed}`);
console.log(`Approved: ${result.accepted}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "processed": 3,
  "accepted": 3,
  "rejected": 0,
  "results": [
    {
      "recommendation_id": "rec-123",
      "status": "approved"
    },
    {
      "recommendation_id": "rec-124",
      "status": "approved"
    },
    {
      "recommendation_id": "rec-125",
      "status": "approved"
    }
  ]
}
```

---

## Enhancement Examples

### 9. Enhance Content

**Description**: Apply approved recommendations to content and get enhanced version.

**curl**:
```bash
curl -X POST http://localhost:8080/api/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "validation_id": "val-123",
    "file_path": "docs/tutorial.md",
    "content": "---\ntitle: Tutorial\n---\n# Tutorial\n\nEnable AutoSave feature for automatic saving.",
    "recommendations": ["rec-456", "rec-789"],
    "preview": false
  }'
```

**Python**:
```python
payload = {
    "validation_id": "val-123",
    "file_path": "docs/tutorial.md",
    "content": "---\ntitle: Tutorial\n---\n# Tutorial\n\nEnable AutoSave feature for automatic saving.",
    "recommendations": ["rec-456", "rec-789"],
    "preview": False
}
response = requests.post(f"{BASE_URL}/api/enhance", json=payload)
result = response.json()
print(f"Success: {result['success']}")
print(f"Applied: {result['applied_count']}")
print(f"Enhanced content length: {len(result['enhanced_content'])} chars")
print("\nDiff:")
print(result['diff'])
```

**JavaScript**:
```javascript
const payload = {
  validation_id: "val-123",
  file_path: "docs/tutorial.md",
  content: "---\ntitle: Tutorial\n---\n# Tutorial\n\nEnable AutoSave feature for automatic saving.",
  recommendations: ["rec-456", "rec-789"],
  preview: false
};

const response = await fetch(`${BASE_URL}/api/enhance`, {
  method: "POST",
  headers,
  body: JSON.stringify(payload)
});
const result = await response.json();
console.log(`Success: ${result.success}`);
console.log(`Applied: ${result.applied_count}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Applied 2 recommendations, skipped 0",
  "enhanced_content": "---\ntitle: Tutorial\n---\n# Tutorial\n\nEnable [AutoSave](https://example.com/autosave) feature for automatic saving. This feature provides real-time data protection.",
  "diff": "--- original\n+++ enhanced\n@@ -4,1 +4,1 @@\n-Enable AutoSave feature for automatic saving.\n+Enable [AutoSave](https://example.com/autosave) feature for automatic saving. This feature provides real-time data protection.",
  "applied_count": 2,
  "skipped_count": 0,
  "results": [
    {
      "recommendation_id": "rec-456",
      "status": "applied",
      "reason": null
    },
    {
      "recommendation_id": "rec-789",
      "status": "applied",
      "reason": null
    }
  ]
}
```

---

### 10. Batch Enhancement

**Description**: Enhance multiple validations in parallel.

**curl**:
```bash
curl -X POST http://localhost:8080/api/enhance/batch \
  -H "Content-Type: application/json" \
  -d '{
    "validation_ids": ["val-123", "val-456", "val-789"],
    "parallel": true,
    "persist": true,
    "apply_all": true
  }'
```

**Python**:
```python
payload = {
    "validation_ids": ["val-123", "val-456", "val-789"],
    "parallel": True,
    "persist": True,
    "apply_all": True
}
response = requests.post(f"{BASE_URL}/api/enhance/batch", json=payload)
result = response.json()
print(f"Success: {result['success']}")
print(f"Total validations: {result['total_validations']}")
print(f"Successfully enhanced: {result['successful']}")
print(f"Failed: {result['failed']}")
```

**JavaScript**:
```javascript
const payload = {
  validation_ids: ["val-123", "val-456", "val-789"],
  parallel: true,
  persist: true,
  apply_all: true
};

const response = await fetch(`${BASE_URL}/api/enhance/batch`, {
  method: "POST",
  headers,
  body: JSON.stringify(payload)
});
const result = await response.json();
console.log(`Success: ${result.success}`);
console.log(`Successful: ${result.successful}`);
console.log(`Failed: ${result.failed}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "total_validations": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "validation_id": "val-123",
      "enhanced": true,
      "enhancements_applied": 2,
      "enhanced_content_length": 1250
    },
    {
      "validation_id": "val-456",
      "enhanced": true,
      "enhancements_applied": 1,
      "enhanced_content_length": 980
    },
    {
      "validation_id": "val-789",
      "enhanced": true,
      "enhancements_applied": 3,
      "enhanced_content_length": 1500
    }
  ]
}
```

---

### 11. Enhancement Comparison

**Description**: Get detailed before/after comparison of enhancement changes.

**curl**:
```bash
curl -X GET http://localhost:8080/api/validations/val-123/enhancement-comparison \
  -H "Content-Type: application/json"
```

**Python**:
```python
response = requests.get(
    f"{BASE_URL}/api/validations/val-123/enhancement-comparison"
)
comparison = response.json()
print(f"Original length: {comparison['stats']['original_length']}")
print(f"Enhanced length: {comparison['stats']['enhanced_length']}")
print(f"Lines added: {comparison['stats']['lines_added']}")
print(f"Lines removed: {comparison['stats']['lines_removed']}")
print(f"Lines modified: {comparison['stats']['lines_modified']}")
print(f"Recommendations applied: {comparison['stats']['recommendations_applied']}")
```

**JavaScript**:
```javascript
const response = await fetch(
  `${BASE_URL}/api/validations/val-123/enhancement-comparison`
);
const comparison = await response.json();
console.log(`Original length: ${comparison.stats.original_length}`);
console.log(`Enhanced length: ${comparison.stats.enhanced_length}`);
console.log(`Lines added: ${comparison.stats.lines_added}`);
console.log(`Lines removed: ${comparison.stats.lines_removed}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "validation_id": "val-123",
  "file_path": "docs/tutorial.md",
  "original_content": "---\ntitle: Tutorial\n---\n# Tutorial\n\nEnable AutoSave for automatic saving.",
  "enhanced_content": "---\ntitle: Tutorial\nauthor: System\n---\n# Tutorial\n\nEnable [AutoSave](https://example.com/autosave) for automatic saving.\n\nAutoSave is a powerful feature that provides real-time data protection.",
  "diff_lines": [
    {
      "line_number_original": 2,
      "line_number_enhanced": 2,
      "content": "author: System",
      "change_type": "added",
      "recommendation_ids": ["rec-789"]
    },
    {
      "line_number_original": 6,
      "line_number_enhanced": 6,
      "content": "Enable [AutoSave](https://example.com/autosave) for automatic saving.",
      "change_type": "modified",
      "recommendation_ids": ["rec-456"]
    }
  ],
  "stats": {
    "original_length": 89,
    "enhanced_length": 195,
    "lines_added": 2,
    "lines_removed": 0,
    "lines_modified": 1,
    "recommendations_applied": 2,
    "recommendations_total": 2,
    "enhancement_timestamp": "2025-12-03T10:35:00.000Z"
  },
  "applied_recommendations": [
    {
      "id": "rec-456",
      "title": "Add plugin link",
      "instruction": "Add hyperlink to AutoSave documentation",
      "confidence": 0.95,
      "status": "applied"
    }
  ],
  "status": "success"
}
```

---

## Workflow Examples

### 12. Directory Validation Workflow

**Description**: Start validation for entire directory with pattern matching.

**curl**:
```bash
curl -X POST http://localhost:8080/workflows/validate-directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./docs",
    "file_pattern": "*.md",
    "workflow_type": "validate_file",
    "max_workers": 8,
    "family": "words",
    "recursive": true
  }'
```

**Python**:
```python
payload = {
    "directory_path": "./docs",
    "file_pattern": "*.md",
    "workflow_type": "validate_file",
    "max_workers": 8,
    "family": "words",
    "recursive": True
}
response = requests.post(
    f"{BASE_URL}/workflows/validate-directory",
    json=payload
)
workflow = response.json()
print(f"Job ID: {workflow['job_id']}")
print(f"Workflow ID: {workflow['workflow_id']}")
print(f"Total files: {workflow['directory_path']}")
print(f"Status: {workflow['status']}")
```

**JavaScript**:
```javascript
const payload = {
  directory_path: "./docs",
  file_pattern: "*.md",
  workflow_type: "validate_file",
  max_workers: 8,
  family: "words",
  recursive: true
};

const response = await fetch(
  `${BASE_URL}/workflows/validate-directory`,
  {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  }
);
const workflow = await response.json();
console.log(`Workflow ID: ${workflow.workflow_id}`);
console.log(`Total files: ${workflow.files_total}`);
```

**Success Response (202)**:
```json
{
  "job_id": "job-123",
  "workflow_id": "wf-456",
  "status": "started",
  "directory_path": "./docs",
  "files_total": 45,
  "file_pattern": "*.md",
  "recursive": true
}
```

---

### 13. Get Workflow Status

**Description**: Check the current status and progress of a workflow.

**curl**:
```bash
curl -X GET http://localhost:8080/workflows/wf-456 \
  -H "Content-Type: application/json"
```

**Python**:
```python
response = requests.get(f"{BASE_URL}/workflows/wf-456")
workflow = response.json()
print(f"Workflow ID: {workflow['workflow_id']}")
print(f"Type: {workflow['type']}")
print(f"State: {workflow['state']}")
print(f"Progress: {workflow['progress_percent']}%")
print(f"Step {workflow['current_step']} of {workflow['total_steps']}")
```

**JavaScript**:
```javascript
const response = await fetch(`${BASE_URL}/workflows/wf-456`);
const workflow = await response.json();
console.log(`Workflow ID: ${workflow.workflow_id}`);
console.log(`State: ${workflow.state}`);
console.log(`Progress: ${workflow.progress_percent}%`);
console.log(`Step ${workflow.current_step} of ${workflow.total_steps}`);
```

**Success Response (200)**:
```json
{
  "workflow_id": "wf-456",
  "type": "validate_directory",
  "state": "running",
  "started_at": "2025-12-03T10:00:00.000Z",
  "progress_percent": 60,
  "current_step": 27,
  "total_steps": 45,
  "metadata": {
    "directory_path": "./docs",
    "files_total": 45,
    "files_validated": 27,
    "files_failed": 2,
    "errors": [
      "docs/broken.md: FileNotFoundError"
    ]
  },
  "checkpoints": [
    {
      "name": "workflow_start",
      "timestamp": "2025-12-03T10:00:00.000Z"
    },
    {
      "name": "file_scanning_complete",
      "timestamp": "2025-12-03T10:00:05.000Z"
    }
  ]
}
```

---

### 14. Control Workflow (Pause/Resume/Cancel)

**Description**: Control running workflow execution.

**curl**:
```bash
# Pause workflow
curl -X POST http://localhost:8080/workflows/wf-456/control \
  -H "Content-Type: application/json" \
  -d '{"action": "pause"}'

# Resume workflow
curl -X POST http://localhost:8080/workflows/wf-456/control \
  -H "Content-Type: application/json" \
  -d '{"action": "resume"}'

# Cancel workflow
curl -X POST http://localhost:8080/workflows/wf-456/control \
  -H "Content-Type: application/json" \
  -d '{"action": "cancel"}'
```

**Python**:
```python
# Pause
response = requests.post(
    f"{BASE_URL}/workflows/wf-456/control",
    json={"action": "pause"}
)
result = response.json()
print(f"Action: Pause - State: {result['state']}")

# Resume
response = requests.post(
    f"{BASE_URL}/workflows/wf-456/control",
    json={"action": "resume"}
)
result = response.json()
print(f"Action: Resume - State: {result['state']}")
```

**JavaScript**:
```javascript
// Pause
let response = await fetch(`${BASE_URL}/workflows/wf-456/control`, {
  method: "POST",
  headers,
  body: JSON.stringify({ action: "pause" })
});
let result = await response.json();
console.log(`State: ${result.state}`);

// Resume
response = await fetch(`${BASE_URL}/workflows/wf-456/control`, {
  method: "POST",
  headers,
  body: JSON.stringify({ action: "resume" })
});
result = await response.json();
console.log(`State: ${result.state}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "workflow_id": "wf-456",
  "state": "paused",
  "progress_percent": 60,
  "current_step": 27,
  "total_steps": 45,
  "message": "Workflow paused successfully"
}
```

---

## WebSocket Real-Time Updates

### 15. Subscribe to Workflow Progress

**Description**: Get real-time updates as workflow progresses.

**JavaScript**:
```javascript
const workflowId = "wf-456";
const ws = new WebSocket(`ws://localhost:8080/ws/${workflowId}`);

ws.onopen = () => {
  console.log("Connected to workflow updates");
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress_percent}%`);
  console.log(`State: ${update.state}`);
  console.log(`Step ${update.current_step}/${update.total_steps}`);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Workflow connection closed");
};
```

**Python** (using websockets library):
```python
import asyncio
import websockets
import json

async def monitor_workflow(workflow_id):
    uri = f"ws://localhost:8080/ws/{workflow_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                data = await websocket.recv()
                update = json.loads(data)
                print(f"Progress: {update['progress_percent']}%")
                print(f"State: {update['state']}")
            except websockets.exceptions.ConnectionClosed:
                break

# Usage
asyncio.run(monitor_workflow("wf-456"))
```

**Message Format**:
```json
{
  "type": "workflow_update",
  "workflow_id": "wf-456",
  "state": "running",
  "progress_percent": 75,
  "current_step": 34,
  "total_steps": 45,
  "timestamp": "2025-12-03T10:05:00.000Z"
}
```

---

## Admin and Monitoring Examples

### 16. Get System Status

**Description**: Get comprehensive system health and metrics.

**curl**:
```bash
curl -X GET http://localhost:8080/admin/status \
  -H "Content-Type: application/json"
```

**Python**:
```python
response = requests.get(f"{BASE_URL}/admin/status")
status = response.json()
print(f"System: {status['status']}")
print(f"Uptime: {status['uptime_seconds']}s")
print(f"Agents: {status['agents']['registered']} registered, {status['agents']['active']} active")
print(f"Database: {status['database']['validations_count']} validations")
print(f"Cache hit rate (L1): {status['cache']['hit_rate']:.2%}")
```

**JavaScript**:
```javascript
const response = await fetch(`${BASE_URL}/admin/status`);
const status = await response.json();
console.log(`System: ${status.status}`);
console.log(`Agents: ${status.agents.active} active`);
console.log(`Database validations: ${status.database.validations_count}`);
```

**Success Response (200)**:
```json
{
  "status": "healthy",
  "uptime_seconds": 7200,
  "agents": {
    "registered": 11,
    "active": 11,
    "busy": 2
  },
  "database": {
    "connected": true,
    "tables": 8,
    "validations_count": 450,
    "recommendations_count": 1200
  },
  "cache": {
    "l1_size": "128MB",
    "l2_size": "512MB",
    "hit_rate": 0.87
  },
  "workflows": {
    "active": 2,
    "pending": 5,
    "completed_today": 42
  }
}
```

---

### 17. Clear Cache

**Description**: Clear system caches for performance optimization.

**curl**:
```bash
curl -X POST http://localhost:8080/admin/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"cache_level": "all"}'
```

**Python**:
```python
response = requests.post(
    f"{BASE_URL}/admin/cache/clear",
    json={"cache_level": "all"}
)
result = response.json()
print(f"Success: {result['success']}")
print(f"L1 cleared: {result['l1_cleared']}")
print(f"L2 cleared: {result['l2_cleared']}")
```

**JavaScript**:
```javascript
const response = await fetch(`${BASE_URL}/admin/cache/clear`, {
  method: "POST",
  headers,
  body: JSON.stringify({ cache_level: "all" })
});
const result = await response.json();
console.log(`Success: ${result.success}`);
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Cache cleared",
  "l1_cleared": true,
  "l2_cleared": true
}
```

---

## Export Examples

### 18. Export Validation Results

**Description**: Export validation data in multiple formats.

**curl**:
```bash
# Export as JSON
curl -X GET "http://localhost:8080/api/export/validation/val-123?format=json" \
  -H "Content-Type: application/json" \
  -o validation_val-123.json

# Export as CSV
curl -X GET "http://localhost:8080/api/export/validation/val-123?format=csv" \
  -H "Content-Type: application/json" \
  -o validation_val-123.csv

# Export as YAML
curl -X GET "http://localhost:8080/api/export/validation/val-123?format=yaml" \
  -H "Content-Type: application/json" \
  -o validation_val-123.yaml
```

**Python**:
```python
# Export as JSON
response = requests.get(
    f"{BASE_URL}/api/export/validation/val-123?format=json"
)
with open("validation_val-123.json", "wb") as f:
    f.write(response.content)

# Export as CSV
response = requests.get(
    f"{BASE_URL}/api/export/validation/val-123?format=csv"
)
with open("validation_val-123.csv", "wb") as f:
    f.write(response.content)
```

**JavaScript**:
```javascript
// Export as JSON
const response = await fetch(
  `${BASE_URL}/api/export/validation/val-123?format=json`
);
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = "validation_val-123.json";
a.click();
```

**Success Response (200)**: Downloads file with appropriate content-type.

---

## Complete Workflow Example

### End-to-End: Validate → Review → Enhance → Export

**Python**:
```python
import requests
import json
import time

BASE_URL = "http://localhost:8080"

# Step 1: Validate content
print("1. Validating content...")
validation_payload = {
    "content": "---\ntitle: Tutorial\n---\n# Tutorial\n\nUse AutoSave to save automatically.",
    "file_path": "tutorial.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "truth", "links"]
}
response = requests.post(f"{BASE_URL}/api/validate", json=validation_payload)
validation = response.json()
validation_id = validation['validation_id']
print(f"   Validation ID: {validation_id}")
print(f"   Status: {validation['status']}")
print(f"   Issues: {len(validation.get('issues', []))}")

# Step 2: Get recommendations
print("\n2. Fetching recommendations...")
response = requests.get(
    f"{BASE_URL}/api/validations/{validation_id}"
)
validation_details = response.json()
recommendations = validation_details['recommendations']
print(f"   Found {len(recommendations)} recommendations")
for rec in recommendations[:3]:
    print(f"   - [{rec['severity']}] {rec['instruction']}")

# Step 3: Approve recommendations
if recommendations:
    print("\n3. Approving recommendations...")
    rec_ids = [r['id'] for r in recommendations[:3]]
    payload = {
        "recommendation_ids": rec_ids,
        "action": "accepted",
        "reviewer": "script@example.com",
        "notes": "Auto-approved via workflow"
    }
    response = requests.post(
        f"{BASE_URL}/api/recommendations/bulk-review",
        json=payload
    )
    result = response.json()
    print(f"   Approved: {result['accepted']} recommendations")

# Step 4: Enhance content
print("\n4. Enhancing content...")
enhance_payload = {
    "validation_id": validation_id,
    "file_path": "tutorial.md",
    "content": validation_payload['content'],
    "preview": False
}
response = requests.post(f"{BASE_URL}/api/enhance", json=enhance_payload)
enhancement = response.json()
print(f"   Success: {enhancement['success']}")
print(f"   Applied: {enhancement['applied_count']} recommendations")

# Step 5: Export results
print("\n5. Exporting results...")
response = requests.get(
    f"{BASE_URL}/api/export/validation/{validation_id}?format=json"
)
with open(f"validation_{validation_id}.json", "wb") as f:
    f.write(response.content)
print(f"   Exported to validation_{validation_id}.json")

print("\n✓ Workflow complete!")
```

**JavaScript**:
```javascript
const BASE_URL = "http://localhost:8080";

async function runWorkflow() {
  try {
    // Step 1: Validate
    console.log("1. Validating content...");
    let response = await fetch(`${BASE_URL}/api/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: "---\ntitle: Tutorial\n---\n# Tutorial\n\nUse AutoSave to save automatically.",
        file_path: "tutorial.md",
        family: "words",
        validation_types: ["yaml", "markdown", "truth", "links"]
      })
    });
    const validation = await response.json();
    const validationId = validation.validation_id;
    console.log(`   Validation ID: ${validationId}`);

    // Step 2: Get recommendations
    console.log("2. Fetching recommendations...");
    response = await fetch(`${BASE_URL}/api/validations/${validationId}`);
    const details = await response.json();
    const recommendations = details.recommendations;
    console.log(`   Found ${recommendations.length} recommendations`);

    // Step 3: Approve recommendations
    if (recommendations.length > 0) {
      console.log("3. Approving recommendations...");
      const recIds = recommendations.slice(0, 3).map(r => r.id);
      response = await fetch(`${BASE_URL}/api/recommendations/bulk-review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recommendation_ids: recIds,
          action: "accepted",
          reviewer: "script@example.com",
          notes: "Auto-approved via workflow"
        })
      });
      const result = await response.json();
      console.log(`   Approved: ${result.accepted} recommendations`);
    }

    // Step 4: Enhance
    console.log("4. Enhancing content...");
    response = await fetch(`${BASE_URL}/api/enhance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        validation_id: validationId,
        file_path: "tutorial.md",
        content: "---\ntitle: Tutorial\n---\n# Tutorial\n\nUse AutoSave to save automatically.",
        preview: false
      })
    });
    const enhancement = await response.json();
    console.log(`   Applied: ${enhancement.applied_count} recommendations`);

    console.log("\n✓ Workflow complete!");
  } catch (error) {
    console.error("Error:", error);
  }
}

runWorkflow();
```

---

## Error Handling Examples

### Common Error Scenarios

**400 Bad Request - Invalid Parameters**:
```json
{
  "error": "Invalid request parameters",
  "type": "MCPInvalidParamsError",
  "code": -32602,
  "data": {
    "field": "family",
    "message": "Invalid choice: must be one of: words, cells, slides, pdf"
  }
}
```

**404 Not Found**:
```json
{
  "error": "Validation not found",
  "type": "MCPResourceNotFoundError",
  "code": -32001,
  "data": {
    "validation_id": "invalid-id"
  }
}
```

**422 Validation Error**:
```json
{
  "error": "Content validation failed",
  "type": "MCPValidationError",
  "code": -32000,
  "data": {
    "file_path": "test.md",
    "issues_count": 1,
    "issues": [
      {
        "level": "error",
        "category": "yaml",
        "message": "Invalid YAML frontmatter",
        "line": 1
      }
    ]
  }
}
```

**Python Error Handling**:
```python
try:
    response = requests.post(f"{BASE_URL}/api/validate", json=payload)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    if e.response.status_code == 422:
        issues = error_data.get('data', {}).get('issues', [])
        print(f"Validation error: {len(issues)} issues found")
        for issue in issues:
            print(f"  - [{issue['level']}] {issue['message']}")
    elif e.response.status_code == 404:
        print("Resource not found")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
```

**JavaScript Error Handling**:
```javascript
try {
  const response = await fetch(`${BASE_URL}/api/validate`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json();
    console.error(`Error ${response.status}: ${error.error}`);

    if (error.type === "MCPValidationError") {
      const issues = error.data.issues;
      console.log(`Validation errors: ${issues.length}`);
    }
    return;
  }

  const result = await response.json();
  // Process result
} catch (error) {
  console.error("Request failed:", error);
}
```

---

## Performance Tips

1. **Batch Operations**: Use batch endpoints for multiple files instead of sequential calls
2. **Pagination**: Always use limit and offset for large result sets
3. **Filtering**: Filter results on the server side rather than retrieving and filtering locally
4. **WebSocket**: Subscribe to WebSocket for long-running workflows instead of polling
5. **Caching**: Enable caching for frequently accessed validation results
6. **Parallel Processing**: Use `parallel: true` for batch operations

---

---

## Error Response Examples

### 19. Request Timeout Error

**Description**: When a request exceeds the timeout limit (30 seconds).

**Response (504 Gateway Timeout)**:
```json
{
  "error": "Request timed out after 30 seconds",
  "type": "MCPTimeoutError",
  "data": {
    "timeout_seconds": 30,
    "operation": "content_validation",
    "suggestion": "Try with smaller content or use batch processing"
  },
  "meta": {
    "path": "/api/validate",
    "method": "POST",
    "timestamp": "2025-12-05T14:45:00Z"
  }
}
```

### 20. Missing Required Field

**Description**: When a required request field is missing.

**curl Request**:
```bash
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test content"
  }'
```

**Response (422 Unprocessable Entity)**:
```json
{
  "error": "Validation failed",
  "type": "ValidationError",
  "validation_errors": [
    {
      "loc": ["body", "file_path"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "meta": {
    "path": "/api/validate",
    "method": "POST",
    "timestamp": "2025-12-05T14:45:30Z"
  }
}
```

### 21. Content Validation Error (YAML Issue)

**Description**: When content has validation issues like invalid YAML.

**curl Request**:
```bash
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "---\ntitle: \"Unclosed quote\n---\n# Content",
    "file_path": "test.md",
    "family": "words"
  }'
```

**Response (422 Unprocessable Entity)**:
```json
{
  "error": "Content validation failed",
  "type": "MCPValidationError",
  "code": -32000,
  "data": {
    "file_path": "test.md",
    "issues_count": 1,
    "issues": [
      {
        "level": "error",
        "category": "yaml",
        "code": "YAML-001",
        "message": "Invalid YAML frontmatter: unclosed quoted string",
        "line_number": 2,
        "column": 8,
        "suggestion": "Close the quoted string",
        "auto_fixable": false
      }
    ]
  },
  "meta": {
    "path": "/api/validate",
    "method": "POST",
    "timestamp": "2025-12-05T14:46:00Z"
  }
}
```

### 22. Workflow State Transition Error

**Description**: When attempting invalid workflow state transition.

**curl Request**:
```bash
curl -X POST http://localhost:8080/workflows/wf-completed/pause \
  -H "Content-Type: application/json"
```

**Response (400 Bad Request)**:
```json
{
  "error": "Invalid state transition",
  "type": "MCPInvalidParamsError",
  "code": -32602,
  "data": {
    "workflow_id": "wf-completed",
    "current_state": "completed",
    "requested_action": "pause",
    "allowed_actions": ["resume"]
  },
  "meta": {
    "path": "/workflows/wf-completed/pause",
    "method": "POST",
    "timestamp": "2025-12-05T14:46:30Z"
  }
}
```

---

## Advanced Examples

### 23. Revalidate Previous Validation

**Description**: Rerun validation on previously validated content with new parameters.

**curl Request**:
```bash
curl -X POST http://localhost:8080/api/validations/val-123/revalidate \
  -H "Content-Type: application/json" \
  -d '{
    "validation_types": ["yaml", "markdown", "code", "links", "structure"],
    "force": true
  }'
```

**Python Request**:
```python
response = requests.post(
    f"{BASE_URL}/api/validations/val-123/revalidate",
    json={
        "validation_types": ["yaml", "markdown", "code", "links", "structure"],
        "force": True
    }
)
result = response.json()
print(f"Revalidation ID: {result['validation_id']}")
print(f"Previous issues: {result['previous_issues_count']}")
print(f"New issues: {result['new_issues_count']}")
```

**Success Response (200)**:
```json
{
  "success": true,
  "validation_id": "val-123-revalidated",
  "original_validation_id": "val-123",
  "previous_status": "completed",
  "new_status": "completed",
  "previous_issues_count": 2,
  "new_issues_count": 1,
  "improvements": [
    {
      "issue_type": "plugin_link",
      "status": "resolved"
    }
  ],
  "new_recommendations": 1
}
```

### 24. List Validations by File Path History

**Description**: Get validation history for a specific file across time.

**curl Request**:
```bash
curl -X GET "http://localhost:8080/api/validations/history/docs/guide.md?limit=10" \
  -H "Content-Type: application/json"
```

**Python Request**:
```python
file_path = "docs/guide.md"
response = requests.get(
    f"{BASE_URL}/api/validations/history/{file_path}",
    params={"limit": 10}
)
history = response.json()
print(f"File: {file_path}")
print(f"Total validations: {len(history['validations'])}")
print(f"Trend: {history['improvement_trend']}")
for val in history['validations']:
    print(f"  {val['created_at']}: {val['status']} ({val['issues_count']} issues)")
```

**Success Response (200)**:
```json
{
  "file_path": "docs/guide.md",
  "total_validations": 5,
  "improvement_trend": "improving",
  "validations": [
    {
      "id": "val-123",
      "created_at": "2025-12-05T14:30:00.000Z",
      "status": "completed",
      "issues_count": 1,
      "recommendations_count": 2
    },
    {
      "id": "val-122",
      "created_at": "2025-12-04T10:15:00.000Z",
      "status": "completed",
      "issues_count": 3,
      "recommendations_count": 5
    }
  ]
}
```

### 25. Generate New Recommendations

**Description**: Generate additional recommendations for existing validation.

**curl Request**:
```bash
curl -X POST http://localhost:8080/api/validations/val-123/recommendations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "regenerate": false,
    "types": ["plugin_link", "info_text", "structure_improvement"]
  }'
```

**Python Request**:
```python
response = requests.post(
    f"{BASE_URL}/api/validations/val-123/recommendations/generate",
    json={
        "regenerate": False,
        "types": ["plugin_link", "info_text"]
    }
)
result = response.json()
print(f"New recommendations generated: {result['recommendations_generated']}")
print(f"Validation ID: {result['validation_id']}")
```

**Success Response (200)**:
```json
{
  "success": true,
  "validation_id": "val-123",
  "recommendations_generated": 3,
  "recommendations": [
    {
      "id": "rec-789",
      "type": "structure_improvement",
      "severity": "low",
      "instruction": "Add section headers for better navigation",
      "confidence": 0.78
    }
  ]
}
```

### 26. Auto-Apply High-Confidence Recommendations

**Description**: Automatically apply only high-confidence recommendations to content.

**curl Request**:
```bash
curl -X POST http://localhost:8080/api/enhance/auto-apply \
  -H "Content-Type: application/json" \
  -d '{
    "validation_id": "val-123",
    "content": "---\ntitle: Guide\n---\n# Guide\n\nEnable AutoSave feature.",
    "confidence_threshold": 0.85,
    "max_recommendations": 5
  }'
```

**Python Request**:
```python
response = requests.post(
    f"{BASE_URL}/api/enhance/auto-apply",
    json={
        "validation_id": "val-123",
        "content": "---\ntitle: Guide\n---\n# Guide\n\nEnable AutoSave feature.",
        "confidence_threshold": 0.85,
        "max_recommendations": 5
    }
)
result = response.json()
print(f"Applied: {result['applied_count']} high-confidence recommendations")
print(f"Enhanced content length: {len(result['enhanced_content'])} chars")
```

**Success Response (200)**:
```json
{
  "success": true,
  "enhanced_content": "---\ntitle: Guide\n---\n# Guide\n\nEnable [AutoSave](https://docs.example.com/features/autosave) feature.",
  "applied_count": 2,
  "skipped_count": 1,
  "skipped_reason": "confidence below threshold",
  "confidence_threshold": 0.85
}
```

### 27. Import Validation Results

**Description**: Import validation results from external source.

**curl Request**:
```bash
curl -X POST http://localhost:8080/api/validations/import \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "external_validation.md",
    "validation_results": {
      "content_validation": {
        "confidence": 0.88,
        "issues": []
      }
    },
    "metadata": {
      "source": "external_tool",
      "version": "1.0"
    }
  }'
```

**Success Response (201)**:
```json
{
  "success": true,
  "validation_id": "val-imported-123",
  "file_path": "external_validation.md",
  "imported_at": "2025-12-05T14:50:00.000Z"
}
```

### 28. Workflow Report

**Description**: Get detailed report for completed workflow.

**curl Request**:
```bash
curl -X GET http://localhost:8080/workflows/wf-456/report \
  -H "Content-Type: application/json"
```

**Python Request**:
```python
response = requests.get(f"{BASE_URL}/workflows/wf-456/report")
report = response.json()
print(f"Workflow: {report['workflow_id']}")
print(f"Status: {report['state']}")
print(f"Duration: {report['duration_seconds']}s")
print(f"Files validated: {report['stats']['files_validated']}")
print(f"Files failed: {report['stats']['files_failed']}")
print(f"Total issues found: {report['stats']['total_issues']}")
print(f"Total recommendations: {report['stats']['total_recommendations']}")
```

**Success Response (200)**:
```json
{
  "workflow_id": "wf-456",
  "type": "validate_directory",
  "state": "completed",
  "started_at": "2025-12-05T14:00:00.000Z",
  "completed_at": "2025-12-05T14:05:30.000Z",
  "duration_seconds": 330,
  "stats": {
    "files_total": 45,
    "files_validated": 43,
    "files_failed": 2,
    "total_issues": 87,
    "total_recommendations": 156,
    "issues_by_category": {
      "yaml": 25,
      "truth": 35,
      "markdown": 18,
      "links": 9
    }
  },
  "errors": [
    "docs/broken.md: FileNotFoundError",
    "docs/unreadable.md: PermissionError"
  ]
}
```

### 29. Get Agents and Capabilities

**Description**: List all registered agents and their capabilities.

**curl Request**:
```bash
curl -X GET http://localhost:8080/agents \
  -H "Content-Type: application/json"
```

**Python Request**:
```python
response = requests.get(f"{BASE_URL}/agents")
agents = response.json()
print(f"Total agents: {agents['total_count']}")
for agent in agents['agents']:
    print(f"\n{agent['agent_id']} ({agent['agent_type']})")
    print(f"  Status: {agent['status']}")
    print(f"  Capabilities: {', '.join(agent['contract']['capabilities'])}")
```

**Success Response (200)**:
```json
{
  "agents": [
    {
      "agent_id": "orchestrator",
      "agent_type": "OrchestratorAgent",
      "status": "active",
      "contract": {
        "name": "Orchestrator",
        "version": "1.0",
        "capabilities": ["execute_workflow", "coordinate_agents"]
      }
    },
    {
      "agent_id": "content_validator",
      "agent_type": "ContentValidatorAgent",
      "status": "active",
      "contract": {
        "name": "ContentValidator",
        "version": "1.0",
        "capabilities": ["validate_content", "validate_yaml", "validate_markdown", "validate_links"]
      }
    },
    {
      "agent_id": "truth_manager",
      "agent_type": "TruthManagerAgent",
      "status": "active",
      "contract": {
        "name": "TruthManager",
        "version": "1.0",
        "capabilities": ["load_truth_data", "get_plugin_info"]
      }
    }
  ],
  "total_count": 11
}
```

### 30. List Active Workflows

**Description**: Get all currently running workflows.

**curl Request**:
```bash
curl -X GET http://localhost:8080/admin/workflows/active \
  -H "Content-Type: application/json"
```

**Python Request**:
```python
response = requests.get(f"{BASE_URL}/admin/workflows/active")
data = response.json()
print(f"Active workflows: {data['count']}")
for workflow in data['active_workflows']:
    print(f"  {workflow['workflow_id']}: {workflow['state']} ({workflow['progress_percent']}%)")
```

**Success Response (200)**:
```json
{
  "active_workflows": [
    {
      "workflow_id": "wf-456",
      "type": "validate_directory",
      "state": "running",
      "started_at": "2025-12-05T14:50:00.000Z",
      "progress_percent": 65,
      "current_step": 29,
      "total_steps": 45
    },
    {
      "workflow_id": "wf-789",
      "type": "enhance_batch",
      "state": "running",
      "started_at": "2025-12-05T14:45:00.000Z",
      "progress_percent": 40,
      "current_step": 4,
      "total_steps": 10
    }
  ],
  "count": 2
}
```

---

## Related Documentation

- [API Reference](./api_reference.md) - Complete API endpoint documentation
- [Workflows](./workflows.md) - Workflow management details
- [Web Dashboard](./web_dashboard.md) - Web UI documentation
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- [Architecture](./architecture.md) - System architecture details
