"""
Comprehensive E2E Test Runner for TBCV
Runs full validation → recommendations → enhancement workflow
Monitors all components: MCP, WebSocket, UI, CLI
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/e2e_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import TBCV components
from agents.base import agent_registry
from agents.orchestrator import OrchestratorAgent
from agents.content_validator import ContentValidatorAgent
from agents.recommendation_agent import RecommendationAgent
from agents.enhancement_agent import EnhancementAgent
from agents.truth_manager import TruthManagerAgent
from agents.fuzzy_detector import FuzzyDetectorAgent
from agents.llm_validator import LLMValidatorAgent
from core.database import db_manager, RecommendationStatus
from core.logging import setup_logging


class E2ETestRunner:
    """
    Runs comprehensive end-to-end tests on files/directories.
    """

    def __init__(self):
        self.results = {}
        self.errors = []
        self.test_start_time = None

    async def setup_agents(self):
        """Initialize all required agents."""
        logger.info("Setting up agents...")

        try:
            # Truth manager
            truth_manager = TruthManagerAgent("truth_manager")
            agent_registry.register_agent(truth_manager)

            # Fuzzy detector
            fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
            agent_registry.register_agent(fuzzy_detector)

            # Validators
            content_validator = ContentValidatorAgent("content_validator")
            agent_registry.register_agent(content_validator)

            llm_validator = LLMValidatorAgent("llm_validator")
            agent_registry.register_agent(llm_validator)

            # Recommendation agent
            rec_agent = RecommendationAgent("recommendation_agent")
            agent_registry.register_agent(rec_agent)

            # Enhancement agent
            enhancement_agent = EnhancementAgent("enhancement_agent")
            agent_registry.register_agent(enhancement_agent)

            # Orchestrator
            orchestrator = OrchestratorAgent("orchestrator")
            agent_registry.register_agent(orchestrator)

            logger.info(f"✓ Registered {len(agent_registry.agents)} agents")
            return True

        except Exception as e:
            logger.error(f"Failed to setup agents: {e}")
            logger.error(traceback.format_exc())
            return False

    async def run_validation(self, path: str, is_directory: bool = False, family: str = "words") -> Optional[Dict[str, Any]]:
        """
        Run validation on a file or directory.

        Args:
            path: File or directory path
            is_directory: True if path is a directory
            family: Plugin family (default: words)

        Returns:
            Validation result dictionary
        """
        logger.info(f"{'='*60}")
        logger.info(f"VALIDATION PHASE: {path}")
        logger.info(f"{'='*60}")

        try:
            orchestrator = agent_registry.get_agent("orchestrator")
            if not orchestrator:
                raise ValueError("Orchestrator agent not available")

            validation_types = [
                "yaml", "markdown", "code", "links",
                "structure", "Truth", "FuzzyLogic", "LLM"
            ]

            if is_directory:
                result = await orchestrator.process_request("validate_directory", {
                    "directory_path": path,
                    "file_pattern": "*.md",
                    "family": family,
                    "validation_types": validation_types,
                    "max_workers": 4
                })
            else:
                result = await orchestrator.process_request("validate_file", {
                    "file_path": path,
                    "family": family,
                    "validation_types": validation_types
                })

            logger.info(f"✓ Validation completed")
            logger.info(f"  Status: {result.get('status', 'unknown')}")

            if is_directory:
                logger.info(f"  Files processed: {result.get('files_total', 0)}")
                logger.info(f"  Files validated: {result.get('files_validated', 0)}")
                logger.info(f"  Files failed: {result.get('files_failed', 0)}")
            else:
                validation_data = result.get('validation_result', {})
                if validation_data:
                    content_val = validation_data.get('content_validation', {})
                    logger.info(f"  Confidence: {content_val.get('confidence', 0):.2f}")
                    logger.info(f"  Issues found: {len(content_val.get('issues', []))}")

            return result

        except Exception as e:
            logger.error(f"✗ Validation failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append({
                "phase": "validation",
                "path": path,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return None

    async def get_validation_ids(self, file_path: str = None) -> List[str]:
        """
        Get validation IDs from database.

        Args:
            file_path: Optional file path to filter by

        Returns:
            List of validation IDs
        """
        try:
            with db_manager.get_session() as session:
                from core.database import ValidationResult
                query = session.query(ValidationResult)

                if file_path:
                    query = query.filter(ValidationResult.file_path.like(f"%{Path(file_path).name}%"))

                query = query.order_by(ValidationResult.created_at.desc())
                results = query.limit(50).all()

                validation_ids = [r.id for r in results]
                logger.info(f"Found {len(validation_ids)} validation records")
                return validation_ids

        except Exception as e:
            logger.error(f"Failed to get validation IDs: {e}")
            return []

    async def generate_recommendations(self, validation_ids: List[str]) -> Dict[str, Any]:
        """
        Generate recommendations for validation results.

        Args:
            validation_ids: List of validation IDs

        Returns:
            Dictionary with recommendation generation results
        """
        logger.info(f"{'='*60}")
        logger.info(f"RECOMMENDATION PHASE")
        logger.info(f"{'='*60}")

        results = {
            "total_validations": len(validation_ids),
            "processed": 0,
            "failed": 0,
            "total_recommendations": 0
        }

        try:
            rec_agent = agent_registry.get_agent("recommendation_agent")
            if not rec_agent:
                raise ValueError("Recommendation agent not available")

            for val_id in validation_ids:
                try:
                    # Get validation result
                    val_result = db_manager.get_validation_result(val_id)
                    if not val_result:
                        logger.warning(f"Validation {val_id[:8]}... not found")
                        results["failed"] += 1
                        continue

                    # Generate recommendations
                    rec_result = await rec_agent.process_request("generate_recommendations", {
                        "validation_id": val_id,
                        "validation_result": val_result.validation_results
                    })

                    rec_count = len(rec_result.get('recommendations', []))
                    results["processed"] += 1
                    results["total_recommendations"] += rec_count

                    logger.info(f"  ✓ {val_id[:8]}... → {rec_count} recommendations")

                except Exception as e:
                    logger.error(f"  ✗ {val_id[:8]}... failed: {e}")
                    results["failed"] += 1
                    self.errors.append({
                        "phase": "recommendation",
                        "validation_id": val_id,
                        "error": str(e)
                    })

            logger.info(f"✓ Recommendation phase completed")
            logger.info(f"  Processed: {results['processed']}/{results['total_validations']}")
            logger.info(f"  Total recommendations: {results['total_recommendations']}")

            return results

        except Exception as e:
            logger.error(f"✗ Recommendation phase failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append({
                "phase": "recommendation",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return results

    async def auto_approve_recommendations(self, validation_ids: List[str], threshold: float = 0.8):
        """
        Auto-approve high-confidence recommendations.

        Args:
            validation_ids: List of validation IDs
            threshold: Confidence threshold for auto-approval
        """
        logger.info(f"{'='*60}")
        logger.info(f"AUTO-APPROVAL PHASE (threshold: {threshold})")
        logger.info(f"{'='*60}")

        approved_count = 0

        try:
            for val_id in validation_ids:
                recs = db_manager.list_recommendations(
                    validation_id=val_id,
                    status='pending',
                    limit=1000
                )

                for rec in recs:
                    if rec.confidence >= threshold:
                        db_manager.update_recommendation_status(
                            rec.id,
                            'approved',
                            reviewer='e2e_auto',
                            review_notes=f'Auto-approved (confidence: {rec.confidence:.2f})'
                        )
                        approved_count += 1
                        logger.info(f"  ✓ Approved: {rec.id[:8]}... (conf: {rec.confidence:.2f})")

            logger.info(f"✓ Auto-approved {approved_count} recommendations")

        except Exception as e:
            logger.error(f"✗ Auto-approval failed: {e}")
            self.errors.append({
                "phase": "auto_approval",
                "error": str(e)
            })

    async def apply_enhancements(self, validation_ids: List[str]) -> Dict[str, Any]:
        """
        Apply approved recommendations as enhancements.

        Args:
            validation_ids: List of validation IDs

        Returns:
            Dictionary with enhancement results
        """
        logger.info(f"{'='*60}")
        logger.info(f"ENHANCEMENT PHASE")
        logger.info(f"{'='*60}")

        results = {
            "total_validations": len(validation_ids),
            "processed": 0,
            "failed": 0,
            "total_applied": 0,
            "total_skipped": 0
        }

        try:
            enhancement_agent = agent_registry.get_agent("enhancement_agent")
            if not enhancement_agent:
                raise ValueError("Enhancement agent not available")

            for val_id in validation_ids:
                try:
                    # Get validation result
                    val_result = db_manager.get_validation_result(val_id)
                    if not val_result:
                        logger.warning(f"Validation {val_id[:8]}... not found")
                        results["failed"] += 1
                        continue

                    # Get approved recommendations
                    approved_recs = db_manager.list_recommendations(
                        validation_id=val_id,
                        status='approved',
                        limit=1000
                    )

                    if not approved_recs:
                        logger.info(f"  - {val_id[:8]}... → No approved recommendations")
                        continue

                    # Read file content
                    file_path = val_result.file_path
                    if not os.path.exists(file_path):
                        logger.warning(f"  ✗ File not found: {file_path}")
                        results["failed"] += 1
                        continue

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Apply enhancements
                    rec_ids = [r.id for r in approved_recs]
                    enhance_result = await enhancement_agent.process_request("enhance_with_recommendations", {
                        "content": content,
                        "file_path": file_path,
                        "validation_id": val_id,
                        "recommendation_ids": rec_ids
                    })

                    applied = enhance_result.get('applied_count', 0)
                    skipped = enhance_result.get('skipped_count', 0)

                    results["processed"] += 1
                    results["total_applied"] += applied
                    results["total_skipped"] += skipped

                    logger.info(f"  ✓ {val_id[:8]}... → Applied: {applied}, Skipped: {skipped}")

                    # Save enhanced content
                    if applied > 0 and 'enhanced_content' in enhance_result:
                        backup_path = f"{file_path}.e2e_backup"
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(enhance_result['enhanced_content'])

                        logger.info(f"    → Enhanced content saved (backup: {backup_path})")

                except Exception as e:
                    logger.error(f"  ✗ {val_id[:8]}... failed: {e}")
                    results["failed"] += 1
                    self.errors.append({
                        "phase": "enhancement",
                        "validation_id": val_id,
                        "error": str(e)
                    })

            logger.info(f"✓ Enhancement phase completed")
            logger.info(f"  Processed: {results['processed']}/{results['total_validations']}")
            logger.info(f"  Total applied: {results['total_applied']}")
            logger.info(f"  Total skipped: {results['total_skipped']}")

            return results

        except Exception as e:
            logger.error(f"✗ Enhancement phase failed: {e}")
            logger.error(traceback.format_exc())
            self.errors.append({
                "phase": "enhancement",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return results

    def save_results(self, test_name: str, results: Dict[str, Any]):
        """
        Save test results to file.

        Args:
            test_name: Name of the test
            results: Results dictionary
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("data/reports/e2e")
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON output
        json_file = output_dir / f"e2e_{test_name}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"✓ Results saved to {json_file}")

        # Markdown summary
        md_file = output_dir / f"e2e_{test_name}_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# E2E Test Results: {test_name}\n\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n\n")

            if self.test_start_time:
                duration = time.time() - self.test_start_time
                f.write(f"**Duration:** {duration:.2f} seconds\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Path:** `{results.get('path', 'N/A')}`\n")
            f.write(f"- **Type:** {results.get('type', 'N/A')}\n")
            f.write(f"- **Status:** {results.get('status', 'N/A')}\n")
            f.write(f"- **Errors:** {len(self.errors)}\n\n")

            if 'validation' in results:
                f.write("## Validation Phase\n\n")
                f.write(f"```json\n{json.dumps(results['validation'], indent=2, default=str)}\n```\n\n")

            if 'recommendations' in results:
                f.write("## Recommendation Phase\n\n")
                f.write(f"```json\n{json.dumps(results['recommendations'], indent=2, default=str)}\n```\n\n")

            if 'enhancements' in results:
                f.write("## Enhancement Phase\n\n")
                f.write(f"```json\n{json.dumps(results['enhancements'], indent=2, default=str)}\n```\n\n")

            if self.errors:
                f.write("## Errors\n\n")
                for i, error in enumerate(self.errors, 1):
                    f.write(f"### Error {i}\n\n")
                    f.write(f"- **Phase:** {error.get('phase', 'N/A')}\n")
                    f.write(f"- **Error:** {error.get('error', 'N/A')}\n")
                    if 'traceback' in error:
                        f.write(f"\n```\n{error['traceback']}\n```\n\n")

        logger.info(f"✓ Summary saved to {md_file}")

    async def run_test(self, path: str, test_name: str, is_directory: bool = False):
        """
        Run complete E2E test on a path.

        Args:
            path: File or directory path
            test_name: Name for this test
            is_directory: True if path is a directory
        """
        self.test_start_time = time.time()
        self.errors = []

        logger.info(f"\n{'#'*60}")
        logger.info(f"# E2E TEST: {test_name}")
        logger.info(f"# Path: {path}")
        logger.info(f"# Type: {'Directory' if is_directory else 'File'}")
        logger.info(f"{'#'*60}\n")

        results = {
            "test_name": test_name,
            "path": path,
            "type": "directory" if is_directory else "file",
            "timestamp": datetime.now().isoformat(),
            "status": "running"
        }

        try:
            # Phase 1: Validation
            validation_result = await self.run_validation(path, is_directory)
            if validation_result:
                results["validation"] = validation_result
            else:
                results["status"] = "failed_validation"
                self.save_results(test_name, results)
                return results

            # Get validation IDs
            validation_ids = await self.get_validation_ids(path if not is_directory else None)
            if not validation_ids:
                logger.warning("No validation IDs found")
                results["status"] = "no_validations"
                self.save_results(test_name, results)
                return results

            results["validation_ids"] = validation_ids[:10]  # Save first 10 for reference

            # Phase 2: Recommendations
            rec_result = await self.generate_recommendations(validation_ids)
            results["recommendations"] = rec_result

            # Phase 3: Auto-approve high-confidence recommendations
            await self.auto_approve_recommendations(validation_ids, threshold=0.8)

            # Phase 4: Apply enhancements
            enhance_result = await self.apply_enhancements(validation_ids)
            results["enhancements"] = enhance_result

            # Final status
            if self.errors:
                results["status"] = "completed_with_errors"
            else:
                results["status"] = "completed_success"

            duration = time.time() - self.test_start_time
            results["duration_seconds"] = duration
            results["errors"] = self.errors

            logger.info(f"\n{'#'*60}")
            logger.info(f"# E2E TEST COMPLETE: {test_name}")
            logger.info(f"# Status: {results['status']}")
            logger.info(f"# Duration: {duration:.2f}s")
            logger.info(f"# Errors: {len(self.errors)}")
            logger.info(f"{'#'*60}\n")

            # Save results
            self.save_results(test_name, results)

            return results

        except Exception as e:
            logger.error(f"✗ E2E test failed: {e}")
            logger.error(traceback.format_exc())
            results["status"] = "failed"
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
            self.save_results(test_name, results)
            return results


async def main():
    """Main entry point."""

    # Test paths from user
    TEST_CASES = [
        {
            "name": "document_converter_index",
            "path": r"D:\OneDrive\Documents\GitHub\aspose.net\content\docs.aspose.net\words\en\developer-guide\document-converter\_index.md",
            "is_directory": False
        },
        {
            "name": "blog_words_directory",
            "path": r"D:\OneDrive\Documents\GitHub\aspose.net\content\blog.aspose.net\words",
            "is_directory": True
        }
    ]

    # Setup
    setup_logging()

    runner = E2ETestRunner()

    # Initialize agents
    if not await runner.setup_agents():
        logger.error("Failed to setup agents. Exiting.")
        return 1

    # Run tests
    all_results = []

    for test_case in TEST_CASES:
        # Check if path exists
        if not os.path.exists(test_case["path"]):
            logger.error(f"Path not found: {test_case['path']}")
            logger.error("Please verify the path and try again.")
            continue

        result = await runner.run_test(
            path=test_case["path"],
            test_name=test_case["name"],
            is_directory=test_case["is_directory"]
        )
        all_results.append(result)

        # Brief pause between tests
        await asyncio.sleep(2)

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("ALL E2E TESTS COMPLETE")
    logger.info("="*60)

    for i, result in enumerate(all_results, 1):
        logger.info(f"{i}. {result.get('test_name', 'Unknown')}: {result.get('status', 'Unknown')}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
