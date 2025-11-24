# TBCV Web Dashboard

Browser-based user interface for validation management, recommendation review, and workflow monitoring.

## Overview

The TBCV Web Dashboard provides a visual interface for:

- **Viewing validation results** with filtering and search
- **Reviewing recommendations** with approve/reject workflow
- **Monitoring workflows** in real-time
- **Managing system** through admin interface

## Accessing the Dashboard

### Starting the Server

```bash
# Start API server (dashboard included)
uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080

# Or using Python module
python -m tbcv.api.server
```

### Dashboard URLs

- **Main Dashboard**: http://localhost:8080/dashboard
- **Validations**: http://localhost:8080/dashboard/validations
- **Recommendations**: http://localhost:8080/dashboard/recommendations
- **Workflows**: http://localhost:8080/dashboard/workflows

## Dashboard Pages

### 1. Dashboard Home

**URL**: `/dashboard`

**Features**:
- **System Overview**: Quick stats and metrics
  - Total validations run
  - Total recommendations generated
  - Pending/approved/rejected/applied counts
  - Active workflows count

- **Recent Activity**:
  - 10 most recent validations
  - 10 pending recommendations
  - 10 active workflows

- **Quick Actions**:
  - Start new validation
  - Review pending recommendations
  - Monitor active workflows

**Example View**:
```
┌─────────────────────────────────────────┐
│ TBCV Dashboard                          │
├─────────────────────────────────────────┤
│ System Stats                            │
│ ├─ Validations: 1,234                   │
│ ├─ Recommendations: 5,678               │
│ ├─ Pending: 42                          │
│ └─ Active Workflows: 3                  │
├─────────────────────────────────────────┤
│ Recent Validations                      │
│ tutorial.md        ✓ Pass   2min ago    │
│ guide.md           ✗ Fail   5min ago    │
│ intro.md           ✓ Pass   8min ago    │
├─────────────────────────────────────────┤
│ Pending Recommendations                 │
│ Add AutoSave link      High   tutorial  │
│ Fix YAML frontmatter   Medium guide     │
└─────────────────────────────────────────┘
```

### 2. Validations List

**URL**: `/dashboard/validations`

**Features**:

- **Filtering**:
  - Status: completed, failed, pending
  - Severity: error, warning, info
  - File path: search by filename
  - Workflow ID: filter by workflow

- **Sorting**:
  - Creation date (newest/oldest)
  - File path (alphabetical)
  - Status

- **Pagination**:
  - Default: 20 results per page
  - Configurable: 10, 20, 50, 100

- **Actions**:
  - View validation details
  - View associated recommendations
  - Export validation report

**Query Parameters**:
```
/dashboard/validations?status=completed&severity=error&page=2&page_size=50
```

**Table Columns**:
- File Path
- Status (Pass/Fail)
- Issues Count
- Recommendations Count
- Created At
- Actions (View Details)

### 3. Validation Detail

**URL**: `/dashboard/validations/{validation_id}`

**Features**:

- **Validation Summary**:
  - File path and family
  - Overall status and confidence
  - Created timestamp
  - Workflow ID (if applicable)

- **Validation Results**:
  - Content validation issues
  - Fuzzy detection results (plugins detected)
  - LLM validation feedback
  - Truth validation results

- **Issues List**:
  - Level (error, warning, info)
  - Category (yaml, markdown, code, links, truth)
  - Message
  - Line number
  - Suggestion

- **Recommendations**:
  - All recommendations for this validation
  - Status (proposed, pending, approved, rejected, applied)
  - Quick approve/reject actions
  - View recommendation details

- **Enhancement Comparison** (for enhanced validations):
  - Side-by-side view: Original vs. Enhanced content
  - Unified diff view: Git-style diff
  - Enhancement statistics:
    - Lines added/removed/modified
    - Recommendations applied
  - Color-coded diff:
    - Green: Added lines
    - Red: Removed lines
    - Yellow: Modified lines
    - White: Unchanged lines
  - Applied recommendations list with details
  - Synchronized scrolling in side-by-side view
  - Line numbers for easy reference

**Example Layout**:
```
┌─────────────────────────────────────────┐
│ Validation: tutorial.md                 │
├─────────────────────────────────────────┤
│ Status: Failed                          │
│ Confidence: 75%                         │
│ Created: 2025-11-19 16:48:00            │
│ Workflow: wf-abc123                     │
├─────────────────────────────────────────┤
│ Issues (3)                              │
│ ✗ [YAML] Missing title field    Line 1 │
│ ⚠ [Truth] Plugin not declared   Line 15│
│ ℹ [Link] Broken link detected   Line 42│
├─────────────────────────────────────────┤
│ Recommendations (5)                     │
│ Add AutoSave hyperlink    [Approve][Reject]
│ Fix YAML frontmatter      [Approve][Reject]
├─────────────────────────────────────────┤
│ Enhancement Comparison                  │
│ [Side-by-Side View] [Unified Diff]     │
│ ─────────────────────────────────────── │
│ Statistics                              │
│ Added: 15 │ Removed: 5 │ Modified: 10  │
│ Recommendations Applied: 3/5            │
│ ─────────────────────────────────────── │
│ Original Content    │ Enhanced Content  │
│ ─────────────────── │ ───────────────── │
│ 1  # Tutorial       │ 1  # Tutorial     │
│ 2  Old text         │ 2  Updated text   │
│ 3                   │ 3                 │
└─────────────────────────────────────────┘
```

### 4. Recommendations List

**URL**: `/dashboard/recommendations`

**Features**:

- **Filtering**:
  - Status: proposed, pending, approved, rejected, applied
  - Type: plugin_link, info_text, formatting, etc.
  - Severity: low, medium, high
  - Validation ID: filter by source validation

- **Bulk Actions**:
  - Select multiple recommendations
  - Bulk approve selected
  - Bulk reject selected
  - Export selection

- **Sorting**:
  - Creation date
  - Confidence score
  - Severity
  - Status

- **Pagination**: 20 per page (configurable)

**Query Parameters**:
```
/dashboard/recommendations?status=proposed&type=plugin_link&page=1
```

**Table Columns**:
- Recommendation ID
- Validation (file path)
- Type
- Severity
- Instruction (preview)
- Confidence
- Status
- Actions (Review, View Details)

**Bulk Review Form**:
```html
☑ Select All

[✓] rec-123  Add AutoSave link      High   0.95
[✓] rec-456  Fix frontmatter        Medium 0.88
[ ] rec-789  Update formatting      Low    0.72

[Approve Selected] [Reject Selected]
```

### 5. Recommendation Detail

**URL**: `/dashboard/recommendations/{recommendation_id}`

**Features**:

- **Recommendation Info**:
  - ID and status
  - Type and severity
  - Instruction and rationale
  - Confidence score
  - Associated validation (with link)

- **Review Form**:
  - Approve/Reject buttons
  - Reviewer name field
  - Review notes textarea
  - Submit review

- **Audit Trail**:
  - Creation timestamp
  - Review timestamp
  - Reviewer identity
  - Status changes
  - Review notes

- **Related Context**:
  - Validation details (collapsed)
  - Original content snippet
  - Proposed change preview

**Example Layout**:
```
┌─────────────────────────────────────────┐
│ Recommendation: rec-456                 │
├─────────────────────────────────────────┤
│ Status: Proposed                        │
│ Type: plugin_link                       │
│ Severity: High                          │
│ Confidence: 95%                         │
├─────────────────────────────────────────┤
│ Instruction:                            │
│ Add hyperlink for AutoSave plugin at    │
│ line 15 (first mention)                 │
│                                         │
│ Rationale:                              │
│ First mention of plugin should be       │
│ hyperlinked per documentation style     │
│ guide                                   │
├─────────────────────────────────────────┤
│ Review Action                           │
│ Reviewer: [admin@example.com]           │
│ Notes: [                               ]│
│        [                               ]│
│ [Approve] [Reject] [Mark Pending]       │
├─────────────────────────────────────────┤
│ Audit Trail                             │
│ Created     2025-11-19 16:48  system    │
│ Reviewed    -                 -         │
└─────────────────────────────────────────┘
```

### 6. Workflows List

**URL**: `/dashboard/workflows`

**Features**:

- **Filtering**:
  - State: pending, running, paused, completed, failed, cancelled
  - Type: validate_file, validate_directory, full_validation, content_update

- **Real-Time Updates**:
  - Auto-refresh for running workflows
  - Progress bars
  - Live status updates

- **Sorting**:
  - Start time (newest/oldest)
  - State
  - Progress percentage

- **Actions**:
  - View workflow details
  - Pause/Resume workflow
  - Cancel workflow
  - Delete completed workflow

**Query Parameters**:
```
/dashboard/workflows?state=running&page=1
```

**Table Columns**:
- Workflow ID
- Type
- State
- Progress (%)
- Started At
- Duration
- Actions (View, Pause/Resume, Cancel)

**Example with Progress Bars**:
```
Workflow ID      Type             State    Progress
─────────────────────────────────────────────────────
wf-abc123    validate_dir    Running  ████████░░ 75%
wf-def456    validate_file   Paused   ████░░░░░░ 40%
wf-ghi789    full_validation Complete ██████████ 100%
```

### 7. Workflow Detail

**URL**: `/dashboard/workflows/{workflow_id}`

**Features**:

- **Workflow Summary**:
  - ID and type
  - State and progress
  - Start/end timestamps
  - Duration
  - Metadata (directory path, file count, etc.)

- **Progress Details**:
  - Current step
  - Total steps
  - Files processed
  - Files failed
  - Error messages

- **Validation Results**:
  - List of all validations created by workflow
  - Links to validation details
  - Success/failure breakdown

- **Workflow Controls**:
  - Pause button (if running)
  - Resume button (if paused)
  - Cancel button (if running/paused)
  - Delete button (if completed/failed)

- **Checkpoints**:
  - Timeline of workflow events
  - Detection start/end
  - Validation start/end
  - Enhancement start/end

- **Real-Time Updates**:
  - Auto-refresh every 2 seconds for active workflows
  - WebSocket connection for instant updates

**Example Layout**:
```
┌─────────────────────────────────────────┐
│ Workflow: wf-abc123                     │
├─────────────────────────────────────────┤
│ Type: validate_directory                │
│ State: Running                          │
│ Progress: 75% (34/45 files)             │
│ Duration: 5m 32s                        │
│                                         │
│ ████████████████████░░░░░ 75%           │
│                                         │
│ [Pause] [Cancel]                        │
├─────────────────────────────────────────┤
│ Details                                 │
│ Directory: ./content                    │
│ Pattern: *.md                           │
│ Files validated: 34                     │
│ Files failed: 2                         │
│ Errors:                                 │
│   - missing.md: FileNotFoundError       │
│   - timeout.md: ValidationTimeout       │
├─────────────────────────────────────────┤
│ Checkpoints                             │
│ ✓ Workflow started    16:00:00          │
│ ✓ Detection started   16:00:05          │
│ ✓ Detection complete  16:02:15          │
│ ▶ Validation running  16:02:20          │
└─────────────────────────────────────────┘
```

### 8. Audit Logs (Future)

**URL**: `/dashboard/audit` (currently disabled)

**Planned Features**:
- User action logging
- Agent action tracking
- Content change history
- Approval/rejection audit trail
- Export audit logs

**Note**: This feature is currently being redesigned and will be available in a future release.

## Dashboard Features

### Filtering and Search

All list views support:

**Filter by Status**:
```html
Status: [All ▼] [Completed] [Failed] [Pending]
```

**Search Box**:
```html
Search: [____________] [🔍]
```

**Date Range**:
```html
From: [2025-11-01] To: [2025-11-19]
```

### Pagination

Standard pagination controls:
```html
Showing 1-20 of 234 results

[◀ Previous] Page 1 of 12 [Next ▶]

Show: [20 ▼] per page
```

### Sorting

Click column headers to sort:
```
File Path ▲  Status ▼  Created At  Actions
```

### Bulk Actions

Select multiple items for bulk operations:
```html
[Select All] [Deselect All]

[✓] Item 1
[✓] Item 2
[ ] Item 3

[Approve Selected] [Reject Selected] [Delete Selected]
```

### Real-Time Updates

**Auto-Refresh**:
- Workflows page: 2-second auto-refresh for active workflows
- Dashboard home: 10-second auto-refresh for stats

**WebSocket Connection** (optional):
```javascript
// Connect to workflow updates
const ws = new WebSocket('ws://localhost:8080/ws/wf-abc123');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  updateProgressBar(update.progress_percent);
};
```

**Server-Sent Events** (SSE):
```javascript
// Global updates stream
const eventSource = new EventSource('/api/stream/updates');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'workflow_update') {
    refreshWorkflowList();
  }
};
```

## User Workflows

### Reviewing Recommendations

**1. Navigate to Recommendations List**:
```
Dashboard → Recommendations → Filter by "proposed"
```

**2. Review Individual Recommendation**:
- Click recommendation ID to view details
- Read instruction and rationale
- Check confidence score
- Review related validation context
- Enter reviewer name and notes
- Click "Approve" or "Reject"

**3. Bulk Review**:
- Select checkboxes for multiple recommendations
- Click "Approve Selected" or "Reject Selected"
- Enter reviewer name and bulk notes
- Submit bulk review

**4. Verify Applied**:
- Navigate to Recommendations
- Filter by "applied" status
- Verify changes were applied successfully

### Monitoring Validation Workflow

**1. Start Directory Validation** (via CLI or API):
```bash
tbcv validate-directory ./content --family words
```

**2. Navigate to Workflows**:
```
Dashboard → Workflows → Filter by "running"
```

**3. View Workflow Details**:
- Click workflow ID
- Monitor progress bar
- View real-time file processing
- Check for errors

**4. Review Results**:
- Wait for completion (or pause/cancel)
- Click "View Validations" link
- Review validation results
- Approve/reject recommendations

### Investigating Validation Issues

**1. Navigate to Validations**:
```
Dashboard → Validations → Filter by "failed"
```

**2. View Validation Detail**:
- Click validation ID
- Review issues list
- Check error messages and line numbers
- View suggestions

**3. Fix Issues**:
- Open file in editor
- Address issues based on suggestions
- Re-validate file

**4. Track Recommendations**:
- View recommendations for validation
- Approve fixes
- Apply recommendations

## Customization

### Template Customization

Templates are located in `templates/` directory:

**Available Templates**:
- `base.html` - Base template with common layout
- `dashboard_home.html` - Dashboard home page
- `validations_list.html` - Validations list
- `validation_detail.html` - Validation detail
- `recommendations_list.html` - Recommendations list
- `recommendation_detail.html` - Recommendation detail
- `workflows_list.html` - Workflows list
- `workflow_detail.html` - Workflow detail

**Customization Example**:
```html
<!-- templates/dashboard_home.html -->
{% extends "base.html" %}

{% block title %}TBCV Dashboard{% endblock %}

{% block content %}
<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Total Validations</h3>
    <p class="stat-value">{{ stats.total_validations }}</p>
  </div>
  <!-- More stat cards -->
</div>
{% endblock %}
```

### Styling

**CSS Location**: `static/css/` (if configured)

**Bootstrap Integration**: Templates use Bootstrap 5 classes

**Custom Styles**:
```html
<!-- Add to base.html -->
<style>
.stat-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin: 10px;
}

.stat-value {
  font-size: 2em;
  font-weight: bold;
  color: #007bff;
}
</style>
```

### Configuration

Dashboard configuration in `config/main.yaml`:

```yaml
server:
  enable_dashboard: true
  dashboard_page_size: 20
  dashboard_auto_refresh: true
  dashboard_auto_refresh_interval: 2  # seconds
```

## Security Considerations

**Current State**: The dashboard has no authentication.

**Production Recommendations**:

1. **Add Authentication**:
   - JWT token authentication
   - Session-based authentication
   - OAuth2 integration

2. **Add Authorization**:
   - Role-based access control (RBAC)
   - Viewer role (read-only)
   - Reviewer role (approve/reject)
   - Admin role (full access)

3. **Add HTTPS**:
   ```bash
   uvicorn tbcv.api.server:app \
     --ssl-keyfile=key.pem \
     --ssl-certfile=cert.pem
   ```

4. **Add Rate Limiting**:
   - Prevent abuse
   - Limit bulk operations
   - Throttle API calls

5. **Add CSRF Protection**:
   ```python
   from fastapi_csrf_protect import CsrfProtect
   ```

## Performance Optimization

### Database Queries

**Pagination**:
- Limit results per page
- Use offset-based pagination
- Add database indexes

**Filtering**:
- Add indexes for filtered columns (status, created_at, etc.)
- Optimize WHERE clauses

**Joins**:
- Minimize N+1 queries
- Use eager loading for relationships

### Caching

**Page Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_dashboard_stats():
    # Expensive calculation
    return stats
```

**Browser Caching**:
```html
<meta http-equiv="Cache-Control" content="max-age=300">
```

### Frontend Optimization

**Lazy Loading**:
- Load images on scroll
- Pagination instead of infinite scroll

**Minification**:
- Minify CSS/JS
- Compress HTML

**CDN**:
- Serve static assets from CDN
- Use Bootstrap CDN

## Troubleshooting

### Dashboard Not Loading

**Issue**: 404 error when accessing `/dashboard`

**Solution**:
1. Verify dashboard router is imported:
   ```python
   # In api/server.py
   from api.dashboard import router as dashboard_router
   app.include_router(dashboard_router)
   ```

2. Check templates directory exists:
   ```bash
   ls templates/
   ```

3. Verify Jinja2 templates installed:
   ```bash
   pip install jinja2
   ```

### Template Not Found Error

**Issue**: `TemplateNotFound: dashboard_home.html`

**Solution**:
1. Check template file exists:
   ```bash
   ls templates/dashboard_home.html
   ```

2. Verify template directory path:
   ```python
   # In api/dashboard.py
   TEMPLATE_DIR = Path("templates")
   ```

3. Run from correct working directory:
   ```bash
   cd /path/to/tbcv
   uvicorn tbcv.api.server:app
   ```

### Slow Page Load

**Issue**: Dashboard pages load slowly

**Solution**:
1. Add database indexes:
   ```sql
   CREATE INDEX idx_validation_created ON validation_results(created_at);
   CREATE INDEX idx_validation_status ON validation_results(status);
   ```

2. Reduce page size:
   ```python
   page_size = 10  # Instead of 100
   ```

3. Add caching:
   ```python
   @lru_cache(maxsize=100)
   def get_validations_list():
       return db_manager.list_validation_results(limit=20)
   ```

### WebSocket Connection Failed

**Issue**: Real-time updates not working

**Solution**:
1. Check WebSocket route exists:
   ```bash
   curl http://localhost:8080/ws/wf-abc123
   ```

2. Verify browser WebSocket support:
   ```javascript
   if ('WebSocket' in window) {
     console.log('WebSocket supported');
   }
   ```

3. Check firewall/proxy settings:
   - Ensure WebSocket connections allowed
   - Configure proxy to pass WebSocket upgrade headers

## Browser Compatibility

**Supported Browsers**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Features Requiring Modern Browser**:
- WebSocket (real-time updates)
- Server-Sent Events (SSE)
- ES6 JavaScript

**Fallback for Older Browsers**:
- Disable auto-refresh
- Use manual refresh button
- Polling instead of WebSocket

## Mobile Responsiveness

**Bootstrap Responsive Design**:
- Mobile-first layout
- Responsive tables
- Collapsible filters
- Touch-friendly buttons

**Mobile Optimizations**:
- Smaller page sizes (10 instead of 20)
- Simplified tables (hide non-essential columns)
- Swipe gestures for pagination

## Related Documentation

- [API Reference](api_reference.md) - REST API documentation
- [Workflows](workflows.md) - Workflow types and execution
- [Troubleshooting](troubleshooting.md) - Common issues
- [Configuration](configuration.md) - Dashboard configuration options
