# Utility Scripts

Operational utility scripts for database management, system checks, and recommendation workflows.

## Database Utilities

### check_db.py
Check database connectivity and schema integrity.

```bash
python scripts/utilities/check_db.py
```

Verifies:
- Database connection
- Table existence
- Basic data integrity

### check_schema.py
Validate database schema against expected structure.

```bash
python scripts/utilities/check_schema.py
```

Checks:
- Column definitions
- Table relationships
- Schema versioning

## Recommendation Utilities

### approve_recommendations.py
Bulk approve recommendations for a validation.

```bash
python scripts/utilities/approve_recommendations.py --validation-id <id>
python scripts/utilities/approve_recommendations.py --all
```

Options:
- `--validation-id` - Approve recommendations for specific validation
- `--all` - Approve all pending recommendations (use with caution)
- `--reviewer` - Set reviewer name

### check_all_recs.py
Check status of all recommendations in the system.

```bash
python scripts/utilities/check_all_recs.py
```

Displays:
- Total recommendations
- Status breakdown (pending/accepted/rejected)
- Validation IDs with pending recommendations

### check_rec_status.py
Check status of specific recommendations.

```bash
python scripts/utilities/check_rec_status.py --validation-id <id>
python scripts/utilities/check_rec_status.py --rec-id <id>
```

Shows:
- Recommendation details
- Current status
- Review notes

## Documentation Generation

### generate_docs.py
Generate API documentation from code.

```bash
python scripts/utilities/generate_docs.py
```

Generates:
- API endpoint documentation
- Schema definitions
- Example requests/responses

## System Initialization

### init.py
Initialize or reset system components.

```bash
python scripts/utilities/init.py [--component <name>]
```

Components:
- database
- cache
- truth-store

## Usage Notes

**Run from project root**:
```bash
# Good
python scripts/utilities/check_db.py

# Bad (may cause import errors)
cd scripts/utilities && python check_db.py
```

**Virtual environment**:
Ensure your virtual environment is activated before running scripts.

## Related Scripts

- **Maintenance scripts**: [scripts/maintenance/](../maintenance/) - System diagnostics and health checks
- **Testing scripts**: [scripts/testing/](../testing/) - Test runners and validation
- **Systemd scripts**: [scripts/systemd/](../systemd/) - Service management for Linux
- **Windows scripts**: [scripts/windows/](../windows/) - Service management for Windows

## Adding New Utilities

When adding new utility scripts:

1. Place in this directory
2. Add entry to this README
3. Use argparse for command-line arguments
4. Include --help text
5. Follow existing error handling patterns
6. Add to .gitignore if generates temporary files
