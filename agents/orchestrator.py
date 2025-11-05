# file: tbcv\agents\orchestrator.py
"""
OrchestratorAgent - Workflow coordination and batch processing.
Manages complex workflows involving multiple agents and file processing.

Rebased fixes:
- Provide checkpoints=[] in AgentContract to satisfy base contract signature.
- Register "get_contract" to the existing method (self.get_contract) instead of a non-existent handler.
- Use structured project logger (get_logger) and avoid passing arbitrary keyword args to logging methods.
"""

from __future__ import annotations

import asyncio
import glob
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents.base import BaseAgent, AgentContract, AgentCapability, agent_registry
from core.logging import PerformanceLogger, get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    job_id: str
    workflow_type: str
    status: str
    files_total: int = 0
    files_validated: int = 0
    files_failed: int = 0
    errors: List[str] = None
    results: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.results is None:
            self.results = []


class OrchestratorAgent(BaseAgent):
    """Agent that coordinates workflows across multiple agents."""

    def __init__(self, agent_id: Optional[str] = None):
        self.active_workflows: Dict[str, WorkflowResult] = {}
        super().__init__(agent_id)

    def _register_message_handlers(self):
        """Register workflow handlers."""
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        # FIX: register to the existing method rather than a non-existent handler
        self.register_handler("get_contract", self.get_contract)
        self.register_handler("validate_file", self.handle_validate_file)
        self.register_handler("validate_directory", self.handle_validate_directory)
        self.register_handler("get_workflow_status", self.handle_get_workflow_status)
        self.register_handler("list_workflows", self.handle_list_workflows)

    def get_contract(self) -> AgentContract:
        """Return agent contract."""
        return AgentContract(
            agent_id=self.agent_id,
            name="OrchestratorAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="validate_file",
                    description="Validate a single file using multiple agents",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "family": {"type": "string", "default": "words"}
                        },
                        "required": ["file_path"]
                    },
                    output_schema={"type": "object"},
                    side_effects=["read", "db_write"]
                ),
                AgentCapability(
                    name="validate_directory",
                    description="Validate all files in a directory using multiple agents",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"},
                            "file_pattern": {"type": "string", "default": "*.md"},
                            "max_workers": {"type": "integer", "default": 4},
                            "family": {"type": "string", "default": "words"}
                        },
                        "required": ["directory_path"]
                    },
                    output_schema={"type": "object"},
                    side_effects=["read", "db_write"]
                )
            ],
            max_runtime_s=600,  # 10 minutes for batch operations
            confidence_threshold=0.7,
            side_effects=["read", "db_write"],
            dependencies=["content_validator", "fuzzy_detector", "llm_validator", "truth_manager"],
            checkpoints=[]  # REQUIRED by AgentContract in your base.py
        )

    def _validate_configuration(self):
        """Validate orchestrator configuration."""
        # No specific configuration needed
        pass

    async def handle_validate_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single file using the validation pipeline."""
        file_path = params.get("file_path")
        family = params.get("family", "words")

        if not file_path:
            raise ValueError("file_path is required")

        try:
            # Read file content
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()

            # Run validation pipeline
            validation_result = await self._run_validation_pipeline(content, str(path_obj), family)

            return {
                "file_path": str(path_obj),
                "family": family,
                "validation_result": validation_result,
                "status": "completed"
            }

        except Exception as e:
            logger.exception("File validation failed")
            return {
                "file_path": file_path,
                "family": family,
                "status": "failed",
                "error": str(e)
            }

    async def handle_validate_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all files in a directory."""
        directory_path = params.get("directory_path")
        file_pattern = params.get("file_pattern", "*.md")
        max_workers = int(params.get("max_workers", 4))
        family = params.get("family", "words")

        if not directory_path:
            raise ValueError("directory_path is required")

        with PerformanceLogger(self.logger, "validate_directory"):
            try:
                # Find matching files
                dir_path = Path(directory_path)
                if not dir_path.exists():
                    raise FileNotFoundError(f"Directory not found: {directory_path}")

                # Use glob to find files matching pattern
                pattern_path = dir_path / file_pattern
                matching_files = list(glob.glob(str(pattern_path), recursive=True))

                # Also check subdirectories if pattern not already recursive
                if "**" not in file_pattern:
                    recursive_pattern = dir_path / "**" / file_pattern
                    matching_files.extend(glob.glob(str(recursive_pattern), recursive=True))

                # Remove duplicates and ensure they're files
                unique_files: List[str] = []
                seen = set()
                for fp in matching_files:
                    abs_path = os.path.abspath(fp)
                    if abs_path not in seen and Path(abs_path).is_file():
                        unique_files.append(abs_path)
                        seen.add(abs_path)

                logger.info(
                    "Starting directory validation",
                    extra={
                        "directory": directory_path,
                        "pattern": file_pattern,
                        "files_found": len(unique_files),
                        "family": family,
                    },
                )

                # Process files concurrently
                results = await self._process_files_concurrently(unique_files, family, max_workers)

                # Compile summary
                files_validated = len([r for r in results if r.get("status") == "completed"])
                files_failed = len([r for r in results if r.get("status") == "failed"])
                errors = [r.get("error", "") for r in results if r.get("error")]

                return {
                    "directory_path": directory_path,
                    "file_pattern": file_pattern,
                    "family": family,
                    "files_total": len(unique_files),
                    "files_validated": files_validated,
                    "files_failed": files_failed,
                    "errors": errors[:10],  # Limit error list
                    "results": results,
                    "status": "completed"
                }

            except Exception as e:
                logger.exception("Directory validation failed")
                return {
                    "directory_path": directory_path,
                    "file_pattern": file_pattern,
                    "family": family,
                    "files_total": 0,
                    "files_validated": 0,
                    "files_failed": 0,
                    "errors": [str(e)],
                    "status": "failed"
                }

    async def _process_files_concurrently(self, file_paths: List[str], family: str, max_workers: int) -> List[Dict[str, Any]]:
        """Process multiple files concurrently."""
        semaphore = asyncio.Semaphore(max_workers)

        async def process_single_file(fp: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.handle_validate_file({
                    "file_path": fp,
                    "family": family
                })

        tasks = [process_single_file(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results: List[Dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "file_path": file_paths[i],
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _run_validation_pipeline(self, content: str, file_path: str, family: str) -> Dict[str, Any]:
        """Run the complete validation pipeline for a file."""
        pipeline_result: Dict[str, Any] = {
            "truth_loading": None,
            "plugin_detection": None,
            "llm_validation": None,
            "content_validation": None,
            "overall_confidence": 0.0
        }

        try:
            # Step 1: Load truth data
            truth_manager = agent_registry.get_agent("truth_manager")
            if truth_manager:
                truth_result = await truth_manager.process_request("load_truth_data", {"family": family})
                pipeline_result["truth_loading"] = truth_result
                logger.debug("Truth data loaded", extra={"family": family, "success": truth_result.get("success", False)})

            # Step 2: Detect plugins with fuzzy matching
            fuzzy_detector = agent_registry.get_agent("fuzzy_detector")
            fuzzy_detections = []
            if fuzzy_detector:
                detection_result = await fuzzy_detector.process_request("detect_plugins", {
                    "text": content,
                    "family": family,
                    "confidence_threshold": 0.6
                })
                fuzzy_detections = detection_result.get("detections", [])
                pipeline_result["plugin_detection"] = detection_result
                logger.debug(
                    "Plugin detection completed",
                    extra={"file_path": file_path, "detections": detection_result.get("detection_count", 0)},
                )

            # Step 3: LLM validation (PRIORITY - verifies and finds missing plugins)
            llm_validator = agent_registry.get_agent("llm_validator")
            if llm_validator:
                llm_result = await llm_validator.process_request("validate_plugins", {
                    "content": content,
                    "fuzzy_detections": fuzzy_detections,
                    "family": family
                })
                pipeline_result["llm_validation"] = llm_result
                logger.debug(
                    "LLM validation completed",
                    extra={
                        "file_path": file_path,
                        "requirements": len(llm_result.get("requirements", [])),
                        "issues": len(llm_result.get("issues", [])),
                    },
                )

            # Step 4: Validate content (uses both truths and rules)
            content_validator = agent_registry.get_agent("content_validator")
            if content_validator:
                validation_result = await content_validator.process_request("validate_content", {
                    "content": content,
                    "file_path": file_path,
                    "family": family,
                    "validation_types": ["yaml", "markdown", "code", "links", "structure"]
                })
                pipeline_result["content_validation"] = validation_result
                logger.debug(
                    "Content validation completed",
                    extra={
                        "file_path": file_path,
                        "confidence": validation_result.get("confidence", 0.0),
                        "issues": len(validation_result.get("issues", [])),
                    },
                )

            # Calculate overall confidence (give LLM higher weight)
            confidences: List[float] = []
            if pipeline_result["llm_validation"]:
                # LLM gets double weight
                llm_conf = float(pipeline_result["llm_validation"].get("confidence", 0.0))
                confidences.extend([llm_conf, llm_conf])
            if pipeline_result["plugin_detection"]:
                confidences.append(float(pipeline_result["plugin_detection"].get("confidence", 0.0)))
            if pipeline_result["content_validation"]:
                confidences.append(float(pipeline_result["content_validation"].get("confidence", 0.0)))

            pipeline_result["overall_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0

            return pipeline_result

        except Exception as e:
            logger.exception("Validation pipeline failed")
            pipeline_result["error"] = str(e)
            return pipeline_result

    async def handle_get_workflow_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific workflow."""
        job_id = params.get("job_id")
        if not job_id or job_id not in self.active_workflows:
            return {"found": False, "job_id": job_id}

        return {"found": True, "workflow": self.active_workflows[job_id]}

    async def handle_list_workflows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all active workflows."""
        return {
            "workflows": list(self.active_workflows.values()),
            "total_count": len(self.active_workflows)
        }


# Self-test
if __name__ == "__main__":
    async def _demo():
        orchestrator = OrchestratorAgent("test_orchestrator")

        # Test file validation (optional, only if a test file exists)
        test_file = Path("test_content.md")
        if test_file.exists():
            result = await orchestrator.handle_validate_file({
                "file_path": str(test_file),
                "family": "words"
            })
            print("File validation result:", result.get("status"))
        else:
            print("Test file not found, skipping file validation test")

        print("Orchestrator agent ready")

    asyncio.run(_demo())
