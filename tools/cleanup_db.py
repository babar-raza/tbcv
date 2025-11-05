#!/usr/bin/env python3
"""
Database cleanup utility for TBCV system.
Usage: python cleanup_db.py [--all | --validations | --recommendations | --workflows]
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import db_manager, Base
from sqlalchemy import text

def cleanup_all():
    """Drop all tables and recreate them (complete reset)."""
    print("⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    try:
        if db_manager.engine:
            Base.metadata.drop_all(bind=db_manager.engine)
            Base.metadata.create_all(bind=db_manager.engine)
            print("✓ Database reset complete - all tables recreated")
        else:
            print("❌ Database not available")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def cleanup_validations():
    """Delete all validation results and related recommendations."""
    try:
        with db_manager.get_session() as session:
            # Count before deletion
            from core.database import ValidationResult, Recommendation
            val_count = session.query(ValidationResult).count()
            rec_count = session.query(Recommendation).count()
            
            # Delete (recommendations will cascade)
            session.query(ValidationResult).delete()
            session.commit()
            
            print(f"✓ Deleted {val_count} validation results")
            print(f"✓ Deleted {rec_count} recommendations")
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup_recommendations():
    """Delete only recommendations, keep validation results."""
    try:
        with db_manager.get_session() as session:
            from core.database import Recommendation
            count = session.query(Recommendation).count()
            session.query(Recommendation).delete()
            session.commit()
            print(f"✓ Deleted {count} recommendations")
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup_workflows():
    """Delete all workflows."""
    try:
        with db_manager.get_session() as session:
            from core.database import Workflow
            count = session.query(Workflow).count()
            session.query(Workflow).delete()
            session.commit()
            print(f"✓ Deleted {count} workflows")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_stats():
    """Show current database statistics."""
    try:
        with db_manager.get_session() as session:
            from core.database import ValidationResult, Recommendation, Workflow, AuditLog
            
            val_count = session.query(ValidationResult).count()
            rec_count = session.query(Recommendation).count()
            wf_count = session.query(Workflow).count()
            audit_count = session.query(AuditLog).count()
            
            print("\n📊 Current Database Statistics:")
            print(f"   Validation Results: {val_count}")
            print(f"   Recommendations:    {rec_count}")
            print(f"   Workflows:          {wf_count}")
            print(f"   Audit Logs:         {audit_count}")
            print()
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TBCV Database Cleanup Utility")
    parser.add_argument("--all", action="store_true", help="Reset entire database")
    parser.add_argument("--validations", action="store_true", help="Delete validation results")
    parser.add_argument("--recommendations", action="store_true", help="Delete recommendations only")
    parser.add_argument("--workflows", action="store_true", help="Delete workflows")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    # Show stats first
    if args.stats or not any([args.all, args.validations, args.recommendations, args.workflows]):
        show_stats()
    
    if args.all:
        cleanup_all()
    elif args.validations:
        cleanup_validations()
    elif args.recommendations:
        cleanup_recommendations()
    elif args.workflows:
        cleanup_workflows()
    
    # Show stats after cleanup
    if any([args.all, args.validations, args.recommendations, args.workflows]):
        show_stats()