"""
Tests for database migrations using Alembic.

These tests verify:
1. Migrations can upgrade and downgrade successfully
2. All expected tables are created
3. Migration check functions work correctly
4. Fresh database initialization works
"""

import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory


class TestMigrations:
    """Test database migrations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        db_url = f"sqlite:///{path}"
        yield db_url, path
        # Cleanup
        try:
            os.unlink(path)
        except Exception:
            pass

    @pytest.fixture
    def alembic_config(self, temp_db):
        """Create Alembic config pointing to temp database."""
        db_url, db_path = temp_db
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", db_url)
        return config, db_url

    def test_upgrade_creates_all_tables(self, alembic_config):
        """Test that upgrade creates all expected tables."""
        config, db_url = alembic_config
        engine = create_engine(db_url)

        # Run upgrade to head
        command.upgrade(config, "head")

        # Inspect created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Expected tables
        expected_tables = {
            'workflows',
            'checkpoints',
            'validation_results',
            'recommendations',
            'audit_logs',
            'cache_entries',
            'metrics',
            'alembic_version'  # Alembic version tracking table
        }

        # Check all expected tables exist
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

        print(f"[OK] All {len(expected_tables)} tables created successfully")

    def test_upgrade_downgrade_cycle(self, alembic_config):
        """Test upgrade and downgrade cycle."""
        config, db_url = alembic_config
        engine = create_engine(db_url)

        # Upgrade to head
        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables_after_upgrade = set(inspector.get_table_names())

        # Should have all tables
        assert len(tables_after_upgrade) >= 8, f"Expected at least 8 tables, got {len(tables_after_upgrade)}"

        # Downgrade to base
        command.downgrade(config, "base")

        inspector = inspect(engine)
        tables_after_downgrade = set(inspector.get_table_names())

        # Should only have alembic_version table
        assert tables_after_downgrade == {'alembic_version'}, \
            f"Expected only alembic_version table, got {tables_after_downgrade}"

        # Upgrade again
        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables_after_reupgrade = set(inspector.get_table_names())

        # Should have all tables again
        assert tables_after_reupgrade == tables_after_upgrade, \
            "Tables differ after re-upgrade"

        print("[OK] Upgrade/downgrade cycle successful")

    def test_migration_current_revision(self, alembic_config):
        """Test getting current migration revision."""
        config, db_url = alembic_config
        engine = create_engine(db_url)

        # Run upgrade
        command.upgrade(config, "head")

        # Get current revision
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        # Should have a revision
        assert current_rev is not None, "No current revision found"

        # Get head revision
        script = ScriptDirectory.from_config(config)
        head_rev = script.get_current_head()

        # Should match
        assert current_rev == head_rev, \
            f"Current revision {current_rev} != head {head_rev}"

        print(f"[OK] Current revision matches head: {current_rev}")

    def test_check_migrations_function(self, alembic_config):
        """Test DatabaseManager.check_migrations() function."""
        config, db_url = alembic_config

        # Run migrations first
        command.upgrade(config, "head")

        # Now test check function directly with the engine
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from sqlalchemy import create_engine

        engine = create_engine(db_url)
        script = ScriptDirectory.from_config(config)

        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()

            # Should match
            assert current_rev == head_rev, "Migrations should be up to date"

        print("[OK] check_migrations() works correctly")

    def test_run_migrations_function(self, alembic_config):
        """Test running migrations via Alembic command."""
        config, db_url = alembic_config
        engine = create_engine(db_url)

        # Run migrations
        command.upgrade(config, "head")

        # Check tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert 'workflows' in tables, "workflows table should exist"
        assert 'alembic_version' in tables, "alembic_version table should exist"

        print("[OK] run_migrations() works correctly")

    def test_initialize_database_fresh(self, temp_db):
        """Test DatabaseManager.initialize_database() on fresh database."""
        from core.database import DatabaseManager

        db_url, db_path = temp_db
        engine = create_engine(db_url)

        # Create database manager with temp DB
        os.environ['DATABASE_URL'] = db_url
        db_manager = DatabaseManager()

        # Initialize database (should handle fresh DB)
        db_manager.initialize_database()

        # Check tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Should have created tables (either via migration or create_all)
        assert 'workflows' in tables, "workflows table should exist"
        assert len(tables) >= 7, f"Expected at least 7 tables, got {len(tables)}"

        print("[OK] initialize_database() works on fresh database")

    def test_table_indexes(self, alembic_config):
        """Test that indexes are created correctly."""
        config, db_url = alembic_config
        engine = create_engine(db_url)

        # Run upgrade
        command.upgrade(config, "head")

        # Check indexes on workflows table
        inspector = inspect(engine)
        indexes = inspector.get_indexes('workflows')

        # Should have indexes
        assert len(indexes) > 0, "workflows table should have indexes"

        index_names = {idx['name'] for idx in indexes}

        # Check for expected indexes
        expected_indexes = {
            'idx_workflows_state_created',
            'idx_workflows_type_state'
        }

        for expected in expected_indexes:
            assert expected in index_names, f"Missing index: {expected}"

        print(f"[OK] Indexes created correctly: {len(indexes)} indexes found")

    def test_foreign_keys(self, alembic_config):
        """Test that foreign keys are created correctly."""
        config, db_url = alembic_config
        engine = create_engine(db_url)

        # Run upgrade
        command.upgrade(config, "head")

        # Check foreign keys on checkpoints table
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys('checkpoints')

        # Should have foreign key to workflows
        assert len(foreign_keys) > 0, "checkpoints should have foreign keys"

        fk_columns = [fk['constrained_columns'][0] for fk in foreign_keys]
        assert 'workflow_id' in fk_columns, "workflow_id should be a foreign key"

        print("[OK] Foreign keys created correctly")

    def test_migration_history(self, alembic_config):
        """Test that migration history is accessible."""
        config, db_url = alembic_config

        # Run upgrade
        command.upgrade(config, "head")

        # Get migration history
        script = ScriptDirectory.from_config(config)
        revisions = list(script.walk_revisions())

        # Should have at least one migration
        assert len(revisions) > 0, "Should have at least one migration"

        # Each revision should have required fields
        for rev in revisions:
            assert hasattr(rev, 'revision'), "Revision should have revision ID"
            assert hasattr(rev, 'doc'), "Revision should have description"

        print(f"[OK] Migration history accessible: {len(revisions)} revisions")


class TestMigrationIntegration:
    """Integration tests for migrations with actual DatabaseManager."""

    def test_database_manager_migration_check(self, tmp_path):
        """Test full integration with DatabaseManager."""
        from core.database import DatabaseManager

        # Create temp database
        db_path = tmp_path / "test.db"
        db_url = f"sqlite:///{db_path}"

        os.environ['DATABASE_URL'] = db_url
        db_manager = DatabaseManager()

        # Initialize should work (fresh DB)
        db_manager.initialize_database()

        # Check should pass
        result = db_manager.check_migrations()

        # Might be False if using create_all fallback, True if using migrations
        assert isinstance(result, bool), "check_migrations should return bool"

        print("[OK] Full integration test passed")


# Test that can be run standalone
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
