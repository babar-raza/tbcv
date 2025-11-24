#!/usr/bin/env python3
"""
Cron job script to automatically generate recommendations for validations.

This script finds validation results that don't have recommendations yet
and generates them in the background. It's designed to be run periodically
(e.g., every 5-10 minutes) via cron/systemd timer/Task Scheduler.

Usage:
    python scripts/generate_recommendations_cron.py [--min-age MINUTES] [--batch-size N] [--dry-run]

Options:
    --min-age MINUTES    Only process validations older than N minutes (default: 5)
    --batch-size N       Process at most N validations per run (default: 10)
    --dry-run           Show what would be done without actually generating
    --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager, ValidationResult
from agents.base import agent_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def generate_recommendations_for_validation(
    validation: ValidationResult,
    dry_run: bool = False
) -> bool:
    """
    Generate recommendations for a single validation.

    Args:
        validation: ValidationResult to generate recommendations for
        dry_run: If True, only log what would be done

    Returns:
        True if successful, False otherwise
    """
    try:
        if dry_run:
            logger.info(
                f"[DRY RUN] Would generate recommendations for validation {validation.id} "
                f"(file: {validation.file_path}, created: {validation.created_at})"
            )
            return True

        logger.info(f"Generating recommendations for validation {validation.id} ({validation.file_path})")

        # Get the recommendation agent
        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            logger.error("Recommendation agent not available")
            return False

        # Generate recommendations
        result = await rec_agent.process_request("generate_recommendations", {
            "validation_id": validation.id,
            "auto_approve_threshold": 0.95  # Only auto-approve very high confidence
        })

        recommendations_count = len(result.get("recommendations", []))
        logger.info(
            f"Generated {recommendations_count} recommendation(s) for validation {validation.id}"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to generate recommendations for validation {validation.id}: {e}")
        return False


async def process_validations_batch(
    min_age_minutes: int = 5,
    batch_size: int = 10,
    dry_run: bool = False
) -> dict:
    """
    Process a batch of validations without recommendations.

    Args:
        min_age_minutes: Only process validations older than this many minutes
        batch_size: Maximum number of validations to process
        dry_run: If True, only show what would be done

    Returns:
        Dictionary with processing statistics
    """
    stats = {
        "found": 0,
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "start_time": datetime.utcnow()
    }

    try:
        # Get validations without recommendations
        validations = db_manager.get_validations_without_recommendations(
            min_age_minutes=min_age_minutes,
            limit=batch_size
        )
        stats["found"] = len(validations)

        if not validations:
            logger.info("No validations found needing recommendations")
            return stats

        logger.info(
            f"Found {len(validations)} validation(s) without recommendations "
            f"(min age: {min_age_minutes} minutes, batch size: {batch_size})"
        )

        # Process each validation
        for validation in validations:
            stats["processed"] += 1

            success = await generate_recommendations_for_validation(
                validation,
                dry_run=dry_run
            )

            if success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        stats["failed"] = stats["processed"]

    finally:
        stats["end_time"] = datetime.utcnow()
        stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()

    return stats


def print_summary(stats: dict):
    """Print processing summary."""
    logger.info("=" * 60)
    logger.info("Recommendation Generation Summary")
    logger.info("=" * 60)
    logger.info(f"Validations found:       {stats['found']}")
    logger.info(f"Validations processed:   {stats['processed']}")
    logger.info(f"Successful:              {stats['successful']}")
    logger.info(f"Failed:                  {stats['failed']}")
    logger.info(f"Duration:                {stats['duration_seconds']:.2f} seconds")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate recommendations for validations in the background"
    )
    parser.add_argument(
        "--min-age",
        type=int,
        default=5,
        help="Only process validations older than N minutes (default: 5)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Process at most N validations per run (default: 10)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually generating"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("Starting recommendation generation cron job")
    if args.dry_run:
        logger.info("[DRY RUN MODE - No changes will be made]")

    # Process batch
    stats = asyncio.run(process_validations_batch(
        min_age_minutes=args.min_age,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    ))

    # Print summary
    print_summary(stats)

    # Exit with non-zero if any failures
    exit_code = 0 if stats["failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
