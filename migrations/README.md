# Database Migrations

TBCV uses Alembic for database schema versioning and migrations.

## Overview

Database migrations provide:
- **Version control** for database schema changes
- **Reproducible deployments** across environments
- **Rollback capabilities** for safe schema evolution
- **Automated schema updates** on application startup

## Quick Start

### Check Current Migration Status

```bash
python -m tbcv migrate current
```

### View Migration History

```bash
python -m tbcv migrate history
```

### Upgrade to Latest Schema

```bash
python -m tbcv migrate upgrade
```

## Commands

### `migrate current`

Show the current migration revision applied to the database.

```bash
python -m tbcv migrate current
python -m tbcv migrate current --verbose
```

### `migrate history`

View the complete migration history.

```bash
python -m tbcv migrate history
python -m tbcv migrate history --verbose
python -m tbcv migrate history --range base:head
```

### `migrate upgrade`

Upgrade the database to a target revision (default: latest).

```bash
# Upgrade to latest
python -m tbcv migrate upgrade

# Upgrade to specific revision
python -m tbcv migrate upgrade --revision abc123

# Show SQL without executing
python -m tbcv migrate upgrade --sql
```

### `migrate downgrade`

Downgrade the database to a previous revision.

```bash
# Downgrade to specific revision (requires confirmation)
python -m tbcv migrate downgrade --revision abc123

# Skip confirmation prompt
python -m tbcv migrate downgrade --revision abc123 --yes

# Show SQL without executing
python -m tbcv migrate downgrade --revision abc123 --sql
```

### `migrate create`

Create a new migration.

```bash
# Auto-generate migration from model changes
python -m tbcv migrate create "add user preferences table"

# Create empty migration template
python -m tbcv migrate create "custom changes" --no-autogenerate

# Preview SQL without creating migration file
python -m tbcv migrate create "preview changes" --sql
```

### `migrate stamp`

Mark the database as being at a specific revision without running migrations.

```bash
# Stamp database as being at head
python -m tbcv migrate stamp head

# Stamp database with specific revision
python -m tbcv migrate stamp abc123

# Preview SQL
python -m tbcv migrate stamp head --sql
```

## Development Workflow

### Making Schema Changes

1. **Modify the model** in `core/database.py`:
   ```python
   class MyModel(Base):
       __tablename__ = "my_table"
       id = Column(String(36), primary_key=True)
       new_column = Column(String(100))  # New field
   ```

2. **Create migration**:
   ```bash
   python -m tbcv migrate create "add new_column to my_table"
   ```

3. **Review generated migration** in `migrations/versions/`:
   - Check `upgrade()` function
   - Check `downgrade()` function
   - Add any custom logic needed
   - Add data migrations if required

4. **Test upgrade**:
   ```bash
   python -m tbcv migrate upgrade
   ```

5. **Test downgrade** (optional but recommended):
   ```bash
   python -m tbcv migrate downgrade --revision <previous_revision>
   python -m tbcv migrate upgrade
   ```

6. **Commit migration file**:
   ```bash
   git add migrations/versions/<new_migration>.py
   git commit -m "migration: add new_column to my_table"
   ```

### Creating Data Migrations

For data migrations, edit the generated migration file:

```python
def upgrade() -> None:
    # Schema change
    op.add_column('users', sa.Column('role', sa.String(50)))

    # Data migration
    connection = op.get_bind()
    connection.execute(
        text("UPDATE users SET role = 'user' WHERE role IS NULL")
    )

def downgrade() -> None:
    # Remove column (data will be lost)
    op.drop_column('users', 'role')
```

## Deployment

### Automatic Migrations (Recommended)

Migrations run automatically on application startup via `DatabaseManager.initialize_database()`.

The startup sequence:
1. Check current migration revision
2. Compare with latest migration
3. Run pending migrations if needed
4. Fallback to `create_all()` for fresh databases

### Manual Migrations

For production deployments, you may want to run migrations manually before starting the application:

```bash
# Run migrations
python -m tbcv migrate upgrade

# Start application
python main.py --mode api
```

### Environment-Specific Configuration

Set `DATABASE_URL` environment variable:

```bash
# Development (SQLite)
export DATABASE_URL=sqlite:///./data/tbcv.db

# Production (PostgreSQL)
export DATABASE_URL=postgresql://user:pass@localhost/tbcv

# Run migrations
python -m tbcv migrate upgrade
```

## Troubleshooting

### Database Not Up to Date Warning

If you see "Database not up to date" warnings:

```bash
# Check current status
python -m tbcv migrate current

# See what migrations are pending
python -m tbcv migrate history

# Upgrade to latest
python -m tbcv migrate upgrade
```

### Migration Conflicts

If you have multiple feature branches with migrations:

1. **Rebase your branch** on main
2. **Merge migration conflicts** in version files
3. **Update revision IDs** if needed
4. **Test migrations** thoroughly

### Fresh Database Setup

For a completely fresh database:

```bash
# Delete existing database
rm data/tbcv.db

# Run migrations (will create fresh schema)
python -m tbcv migrate upgrade

# Or just start the application (auto-migration)
python main.py --mode api
```

### Resetting Migrations

To reset the migration history:

```bash
# Delete database
rm data/tbcv.db

# Delete migration versions
rm migrations/versions/*.py

# Create new initial migration
python -m tbcv migrate create "initial schema"

# Review and edit migration file
# Then apply it
python -m tbcv migrate upgrade
```

## Migration File Structure

```
migrations/
├── README.md              # This file
├── env.py                # Alembic environment configuration
├── script.py.mako        # Migration template
└── versions/             # Migration version files
    └── abc123_description.py
```

## Best Practices

1. **Always review auto-generated migrations** - Alembic may not detect all changes correctly
2. **Test both upgrade and downgrade** - Ensure migrations are reversible
3. **Keep migrations small** - One logical change per migration
4. **Use descriptive messages** - Makes history easier to understand
5. **Never edit applied migrations** - Create new migrations for fixes
6. **Commit migrations with code** - Keep schema and code in sync
7. **Test migrations on copy of production data** - Before deploying

## Current Schema

The TBCV database includes 7 core tables:

1. **workflows** - Workflow execution tracking
2. **checkpoints** - Workflow state checkpoints
3. **validation_results** - Validation outcomes
4. **recommendations** - Content improvement suggestions
5. **audit_logs** - Change audit trail
6. **cache_entries** - L2 cache storage
7. **metrics** - System metrics

Plus the Alembic version tracking table:
- **alembic_version** - Current migration revision

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [TBCV Database Schema](../docs/database-schema.md)
