# Per-File Summaries

> Title: Per-File Analysis
> Version: auto
> Source: Code analysis @ 2025-11-03T07:43:18.200286Z

## Overview

Analyzed 81 text files for responsibilities and key APIs.

**.npmrc**
- **Responsibility**: General text file: .npmrc
- **Size**: 74 bytes, 3 lines

**.wget-hsts**
- **Responsibility**: General text file: .wget-hsts
- **Size**: 215 bytes, 6 lines

**__init__.py**
- **Responsibility**: Package initializer for claude module
- **Classes**: _AliasFinder (__init__.py:11)
- **Functions**: _map() (__init__.py:14), find_spec() (__init__.py:18), create_module() (__init__.py:29), exec_module() (__init__.py:31), __getattr__() (__init__.py:41)
- **Size**: 1881 bytes, 46 lines

**__main__.py**
- **Responsibility**: Python module: CLI entry point for TBCV that works from any current working directory (O01). Provides package-based...
- **Functions**: ensure_package_imports() (__main__.py:18), main() (__main__.py:25)
- **CLI Elements**: 1 found
- **Size**: 1199 bytes, 40 lines

**agents/__init__.py**
- **Responsibility**: Python module: Package initializer for the TBCV agents.  Why this file exists: - Makes `tbcv.agents` a proper Pytho...
- **Size**: 1900 bytes, 51 lines

**agents/base.py**
- **Responsibility**: Defines classes: AgentStatus (base.py:26), MessageType (base.py:35), MCPMessage (base.py:43)
- **Classes**: AgentStatus (base.py:26), MessageType (base.py:35), MCPMessage (base.py:43)
- **Functions**: __post_init__() (base.py:62), to_dict() (base.py:69), from_dict() (base.py:76), __post_init__() (base.py:94), __post_init__() (base.py:116)
- **Size**: 17467 bytes, 456 lines

**agents/code_analyzer.py**
- **Responsibility**: Python module: scripts/tbcv/agents/code_analyzer.py ------------------------------------  Agent: CodeAnalyzerAgent ...
- **Classes**: CodeIssue (code_analyzer.py:37), CodeFix (code_analyzer.py:76), CodeAnalyzerAgent (code_analyzer.py:107)
- **Functions**: to_dict() (code_analyzer.py:61), to_dict() (code_analyzer.py:93), __init__() (code_analyzer.py:120), get_contract() (code_analyzer.py:133), _register_message_handlers() (code_analyzer.py:247)
- **CLI Elements**: 1 found
- **Size**: 45877 bytes, 1020 lines

**agents/content_enhancer.py**
- **Responsibility**: Python module: ContentEnhancerAgent (rebased on your file)  Enhances content and NOW consumes stored validation res...
- **Classes**: Enhancement (content_enhancer.py:28), EnhancementResult (content_enhancer.py:48), ContentEnhancerAgent (content_enhancer.py:61)
- **Functions**: to_dict() (content_enhancer.py:36), to_dict() (content_enhancer.py:53), __init__() (content_enhancer.py:62), get_contract() (content_enhancer.py:66), _register_message_handlers() (content_enhancer.py:106)
- **CLI Elements**: 1 found
- **Size**: 18704 bytes, 439 lines

**agents/content_validator.py**
- **Responsibility**: Python module: ContentValidatorAgent - Generic quality and structure validation for content. Rebased fixes: - Imple...
- **Classes**: ValidationIssue (content_validator.py:42), ValidationResult (content_validator.py:63), ContentValidatorAgent (content_validator.py:77)
- **Functions**: to_dict() (content_validator.py:51), to_dict() (content_validator.py:69), __init__() (content_validator.py:78), get_contract() (content_validator.py:85), _register_message_handlers() (content_validator.py:115)
- **Size**: 23254 bytes, 496 lines

**agents/fuzzy_detector.py**
- **Responsibility**: Python module: FuzzyDetectorAgent - Generic plugin detection with configurable patterns.  Rebased changes: - Import...
- **Classes**: PluginDetection (fuzzy_detector.py:34), FuzzyDetectorAgent (fuzzy_detector.py:59)
- **Functions**: to_dict() (fuzzy_detector.py:45), __init__() (fuzzy_detector.py:62), _register_message_handlers() (fuzzy_detector.py:67), _validate_configuration() (fuzzy_detector.py:76), get_contract() (fuzzy_detector.py:81)
- **Size**: 7658 bytes, 196 lines

**agents/orchestrator.py**
- **Responsibility**: Python module: OrchestratorAgent - Workflow coordination and batch processing. Manages complex workflows involving ...
- **Classes**: WorkflowResult (orchestrator.py:28), OrchestratorAgent (orchestrator.py:46)
- **Functions**: __post_init__() (orchestrator.py:39), __init__() (orchestrator.py:49), _register_message_handlers() (orchestrator.py:53), get_contract() (orchestrator.py:64), _validate_configuration() (orchestrator.py:109)
- **CLI Elements**: 1 found
- **Size**: 14491 bytes, 356 lines

**agents/truth_manager.py**
- **Responsibility**: Python module: scripts/tbcv/agents/truth_manager.py ------------------------------------  Agent: TruthManagerAgent ...
- **Classes**: PluginInfo (truth_manager.py:41), CombinationRule (truth_manager.py:80), TruthDataIndex (truth_manager.py:99)
- **Functions**: __post_init__() (truth_manager.py:56), to_dict() (truth_manager.py:62), to_dict() (truth_manager.py:88), __init__() (truth_manager.py:117), adapt_plugin_data() (truth_manager.py:121)
- **CLI Elements**: 1 found
- **Size**: 27436 bytes, 686 lines

**api/dashboard.py**
- **Responsibility**: Python module: Dashboard interface for TBCV system. Provides browser-accessible UI for viewing and managing validat...
- **Size**: 12612 bytes, 362 lines

**api/export_endpoints.py**
- **Responsibility**: Python module: Export functionality for reports and audit history (D05, I08, I26). Provides JSON, Markdown, and CSV...
- **Functions**: generate() (export_endpoints.py:50), generate() (export_endpoints.py:77), generate() (export_endpoints.py:142), generate() (export_endpoints.py:179), generate() (export_endpoints.py:201)
- **Size**: 13983 bytes, 368 lines

**api/server.py**
- **Responsibility**: Python module: Complete FastAPI server with all endpoints for TBCV system.  New Features: - Complete health endpoin...
- **Classes**: ContentValidationRequest (server.py:64), DirectoryValidationRequest (server.py:70), BatchValidationRequest (server.py:77)
- **CLI Elements**: 1 found
- **Size**: 34742 bytes, 1012 lines

**api/server_extensions.py**
- **Responsibility**: Python module: Server extensions for WebSocket and export functionality. This module extends the main server with m...
- **Functions**: get_extension_routers() (server_extensions.py:171), setup_websocket_handlers() (server_extensions.py:186)
- **Size**: 6753 bytes, 192 lines

**api/websocket_endpoints.py**
- **Responsibility**: Python module: WebSocket endpoints for real-time progress updates (O05, I05, I20). This module provides WebSocket s...
- **Classes**: ConnectionManager (websocket_endpoints.py:17)
- **Functions**: __init__() (websocket_endpoints.py:20), disconnect() (websocket_endpoints.py:36)
- **Size**: 7802 bytes, 200 lines

**artifacts/import_map.json**
- **Responsibility**: General json file: import_map.json
- **Size**: 227 bytes, 1 lines

**cli/main.py**
- **Responsibility**: Python module: Command-line interface for TBCV system. Provides commands for validation, enhancement, and batch pro...
- **Functions**: cli() (main.py:91), validate_file() (main.py:121), validate_directory() (main.py:188), check_agents() (main.py:288), validate() (main.py:338)
- **CLI Elements**: 72 found
- **Size**: 29110 bytes, 788 lines

**config/main.yaml**
- **Responsibility**: General yaml file: main.yaml
- **Size**: 3869 bytes, 178 lines

**core/__init__.py**
- **Responsibility**: Package initializer for core module
- **Size**: 618 bytes, 17 lines

**core/__main__.py**
- **Responsibility**: CLI entry point and main execution logic
- **CLI Elements**: 1 found
- **Size**: 155 bytes, 7 lines

**core/cache.py**
- **Responsibility**: Python module: Two-level caching system for TBCV. L1: In-memory LRU cache for fast access L2: Persistent SQLite cac...
- **Classes**: LRUCache (cache.py:52), CacheManager (cache.py:135)
- **Functions**: _gx() (cache.py:33), _ensure_bool() (cache.py:46), __init__() (cache.py:54), get() (cache.py:63), put() (cache.py:84)
- **Size**: 17017 bytes, 430 lines

**core/config.py**
- **Responsibility**: Python module: Configuration management for TBCV system (Pydantic v2 compatible).  WHAT CHANGED (important): - When...
- **Classes**: BaseSettings (config.py:27), Config (config.py:28), SettingsConfigDict (config.py:32)
- **Functions**: load_config_from_yaml() (config.py:180), _deep_apply_dict_to_model() (config.py:188), merge_configs() (config.py:209), get_settings() (config.py:224), get_config_value() (config.py:253)
- **CLI Elements**: 1 found
- **Size**: 10854 bytes, 301 lines

**core/database.py**
- **Responsibility**: Python module: Enhanced Database configuration and models for the TBCV system.  Features: - Recommendation table fo...
- **Classes**: _Dummy (database.py:43), TEXT (database.py:53), TypeDecorator (database.py:54)
- **Functions**: __init__() (database.py:44), __call__() (database.py:45), declarative_base() (database.py:55), sessionmaker() (database.py:56), process_bind_param() (database.py:95)
- **Size**: 30126 bytes, 810 lines

**core/logging.py**
- **Responsibility**: Python module: Structured logging configuration for the TBCV system.  Goals: - Provide JSON-structured logs by defa...
- **Classes**: _FallbackJsonFormatter (logging.py:41), TBCVProcessor (logging.py:110), ContextFilter (logging.py:140)
- **Functions**: format() (logging.py:61), _build_formatter() (logging.py:83), __call__() (logging.py:120), __init__() (logging.py:148), filter() (logging.py:152)
- **CLI Elements**: 1 found
- **Size**: 15218 bytes, 432 lines

**core/ollama.py**
- **Responsibility**: Python module: Unified Ollama LLM integration for all agents. Uses only Python standard library (urllib.request) fo...
- **Classes**: OllamaError (ollama.py:22), OllamaConnectionError (ollama.py:27), OllamaAPIError (ollama.py:32)
- **Functions**: __init__() (ollama.py:54), _make_request() (ollama.py:74), generate() (ollama.py:121), chat() (ollama.py:146), embed() (ollama.py:172)
- **Size**: 15974 bytes, 440 lines

**core/ollama_validator.py**
- **Responsibility**: Python module: Ollama LLM integration for content validation. Provides contradiction detection and omission checkin...
- **Classes**: OllamaValidator (ollama_validator.py:20)
- **Functions**: __init__() (ollama_validator.py:23), _build_contradiction_prompt() (ollama_validator.py:61), _build_omission_prompt() (ollama_validator.py:92), _parse_contradiction_response() (ollama_validator.py:155), _parse_omission_response() (ollama_validator.py:181)
- **Size**: 7980 bytes, 208 lines

**core/prompt_loader.py**
- **Responsibility**: Python module: Centralized prompt loader for TBCV system. Loads prompts from JSON files in the prompts/ directory u...
- **Classes**: PromptLoader (prompt_loader.py:16)
- **Functions**: __init__() (prompt_loader.py:24), _load_file() (prompt_loader.py:43), get_prompt() (prompt_loader.py:81), get_prompt_with_description() (prompt_loader.py:108), format_prompt() (prompt_loader.py:138)
- **Size**: 9059 bytes, 275 lines

**core/rule_manager.py**
- **Responsibility**: Python module: Generic rule management system for family-specific validation rules. Loads and manages API patterns,...
- **Classes**: FamilyRules (rule_manager.py:16), RuleManager (rule_manager.py:27)
- **Functions**: __init__() (rule_manager.py:30), get_family_rules() (rule_manager.py:37), _load_family_rules() (rule_manager.py:43), _parse_rules_data() (rule_manager.py:60), _get_default_rules() (rule_manager.py:73)
- **Size**: 5715 bytes, 140 lines

**core/utilities.py**
- **Responsibility**: Python module: Utility functions for TBCV focus issues."""...
- **Classes**: ConfigWithDefaults (utilities.py:9)
- **Functions**: __init__() (utilities.py:12), __getitem__() (utilities.py:15), __iter__() (utilities.py:18), __len__() (utilities.py:21), get() (utilities.py:24)
- **Size**: 2406 bytes, 74 lines

**core/validation_store.py**
- **Responsibility**: Python module: Validation results persistence for TBCV (canonical).  Why this file: - Keep validation persistence i...
- **Classes**: ValidationRecord (validation_store.py:24)
- **Functions**: to_dict() (validation_store.py:54), _sha256() (validation_store.py:71), create_validation_record() (validation_store.py:75), list_validation_records() (validation_store.py:106), latest_validation_record() (validation_store.py:127)
- **Size**: 5554 bytes, 173 lines

**data/logs/tbcv.log**
- **Responsibility**: General log file: tbcv.log
- **Size**: 538811 bytes, 1511 lines

**data/reports/endpoint_probe_20251028_151325.json**
- **Responsibility**: General json file: endpoint_probe_20251028_151325.json
- **Size**: 20364 bytes, 610 lines

**data/reports/endpoint_probe_20251028_151325.md**
- **Responsibility**: Documentation: TBCV Endpoint Probe Report
- **Size**: 9055 bytes, 212 lines

**data/reports/endpoint_probe_20251028_151436.json**
- **Responsibility**: General json file: endpoint_probe_20251028_151436.json
- **Size**: 18861 bytes, 610 lines

**data/reports/endpoint_probe_20251028_151436.md**
- **Responsibility**: Documentation: TBCV Endpoint Probe Report
- **Size**: 7143 bytes, 196 lines

**init.py**
- **Responsibility**: Python module: TBCV - Truth-Based Content Validation System A comprehensive system for validating and enhancing tec...
- **Size**: 1572 bytes, 46 lines

**main.py**
- **Responsibility**: Python module: from __future__ import annotations  import argparse import sys import os import shutil...
- **Functions**: _ensure_project_on_path() (main.py:24), _print_env_header() (main.py:37), _purge_bytecode() (main.py:43), _validate_schemas() (main.py:72), _import_uvicorn_or_die() (main.py:111)
- **CLI Elements**: 4 found
- **Size**: 8282 bytes, 221 lines

**prompts/code_analysis.json**
- **Responsibility**: General json file: code_analysis.json
- **Size**: 1249 bytes, 15 lines

**prompts/enhancer.json**
- **Responsibility**: General json file: enhancer.json
- **Size**: 356 bytes, 11 lines

**prompts/validator.json**
- **Responsibility**: General json file: validator.json
- **Size**: 1427 bytes, 11 lines

**pyproject.toml**
- **Responsibility**: Python project metadata, dependencies, and build configuration
- **Config Sections**: [build-system] (pyproject.toml:2), [project] (pyproject.toml:6), [project.optional-dependencies] (pyproject.toml:25)
- **Size**: 2559 bytes, 119 lines

**pytest.ini**
- **Responsibility**: Pytest test runner configuration and options
- **Config Sections**: [pytest] (pytest.ini:1)
- **Size**: 306 bytes, 12 lines

**reports/endpoint_mismatches.json**
- **Responsibility**: General json file: endpoint_mismatches.json
- **Size**: 310 bytes, 10 lines

**reports/endpoints_offline.json**
- **Responsibility**: General json file: endpoints_offline.json
- **Size**: 6107 bytes, 336 lines

**reports/health_fix_report.json**
- **Responsibility**: General json file: health_fix_report.json
- **Size**: 654 bytes, 26 lines

**reports/inventory.json**
- **Responsibility**: General json file: inventory.json
- **Size**: 8151 bytes, 382 lines

**reports/patch_apply.json**
- **Responsibility**: General json file: patch_apply.json
- **Size**: 437 bytes, 21 lines

**reports/status_update.json**
- **Responsibility**: General json file: status_update.json
- **Size**: 440 bytes, 17 lines

**reports/validation_run.json**
- **Responsibility**: General json file: validation_run.json
- **Size**: 443 bytes, 14 lines

**requirements.md**
- **Responsibility**: Requirements specification and feature documentation
- **Size**: 11112 bytes, 270 lines

**requirements.txt**
- **Responsibility**: Text file: requirements.txt (77 lines)
- **Size**: 1511 bytes, 77 lines

**requirements_mapping.md**
- **Responsibility**: Requirements specification and feature documentation
- **Size**: 14737 bytes, 138 lines

**rules/__init__.py**
- **Responsibility**: Package initializer for rules module
- **Size**: 111 bytes, 4 lines

**rules/words.json**
- **Responsibility**: General json file: words.json
- **Size**: 4026 bytes, 131 lines

**stage1_inventory.py**
- **Responsibility**: Python module: Stage 1 inventory script - enumerate all files with metadata...
- **Functions**: get_file_kind() (stage1_inventory.py:12), get_sha256() (stage1_inventory.py:54), infer_purpose() (stage1_inventory.py:64), main() (stage1_inventory.py:130)
- **CLI Elements**: 1 found
- **Size**: 7579 bytes, 213 lines

**system.md**
- **Responsibility**: System architecture documentation and technical overview
- **Size**: 27491 bytes, 819 lines

**tbcv.egg-info/PKG-INFO**
- **Responsibility**: General text file: PKG-INFO
- **Size**: 939 bytes, 27 lines

**tbcv.egg-info/SOURCES.txt**
- **Responsibility**: Text file: sources.txt (16 lines)
- **Size**: 479 bytes, 16 lines

**tbcv.egg-info/dependency_links.txt**
- **Responsibility**: Text file: dependency_links.txt (2 lines)
- **Size**: 1 bytes, 2 lines

**tbcv.egg-info/entry_points.txt**
- **Responsibility**: Text file: entry_points.txt (3 lines)
- **Size**: 44 bytes, 3 lines

**tbcv.egg-info/requires.txt**
- **Responsibility**: Text file: requires.txt (24 lines)
- **Size**: 353 bytes, 24 lines

**tbcv.egg-info/top_level.txt**
- **Responsibility**: Text file: top_level.txt (2 lines)
- **Size**: 1 bytes, 2 lines

**tests/conftest.py**
- **Responsibility**: Test module with unit tests and fixtures
- **Functions**: event_loop() (conftest.py:35)
- **Size**: 2025 bytes, 62 lines

**tests/fixtures/multi_plugin_content.md**
- **Responsibility**: Documentation: Advanced Document Processing
- **Size**: 1705 bytes, 50 lines

**tests/fixtures/truths_and_rules_test.md**
- **Responsibility**: Markdown documentation: truths_and_rules_test
- **Size**: 2266 bytes, 70 lines

**tests/fixtures/yaml_only_content.md**
- **Responsibility**: Markdown documentation: yaml_only_content
- **Size**: 360 bytes, 14 lines

**tests/startup/test_rule_manager_imports.py**
- **Responsibility**: Python module: Test that rule_manager imports work correctly....
- **Functions**: test_import_rule_manager_top_level() (test_rule_manager_imports.py:6), test_import_rule_manager_from_top_level() (test_rule_manager_imports.py:13), test_import_rule_manager_from_core() (test_rule_manager_imports.py:20), test_smoke_api_import() (test_rule_manager_imports.py:28)
- **CLI Elements**: 1 found
- **Size**: 1460 bytes, 43 lines

**tests/test_endpoints_live.py**
- **Responsibility**: Python module: Tests for endpoint discovery and probing in live mode.  These tests execute HTTP requests against a ...
- **Functions**: test_live_endpoint_probing() (test_endpoints_live.py:41)
- **Size**: 3991 bytes, 108 lines

**tests/test_endpoints_offline.py**
- **Responsibility**: Python module: Tests for endpoint discovery and probing in offline mode.  This test suite performs the following ch...
- **Functions**: test_offline_endpoint_probing() (test_endpoints_offline.py:39)
- **Size**: 4411 bytes, 111 lines

**tests/test_enhancer_consumes_validation.py**
- **Responsibility**: API server and endpoint definitions
- **Functions**: _app() (test_enhancer_consumes_validation.py:4), test_enhancer_reads_validation_and_applies_style_fix() (test_enhancer_consumes_validation.py:8)
- **Size**: 763 bytes, 19 lines

**tests/test_framework.py**
- **Responsibility**: Python module: Quick test script to verify TBCV system functionality (folder name agnostic)....
- **CLI Elements**: 1 found
- **Size**: 5983 bytes, 173 lines

**tests/test_generic_validator.py**
- **Responsibility**: Python module: Tests for generic validator system with family-specific rules....
- **Classes**: TestRuleManager (test_generic_validator.py:11), TestGenericContentValidator (test_generic_validator.py:47), TestGenericFuzzyDetector (test_generic_validator.py:160)
- **Functions**: test_load_family_rules_words() (test_generic_validator.py:13), test_api_patterns_loaded() (test_generic_validator.py:25), test_non_editable_fields_include_global() (test_generic_validator.py:36)
- **CLI Elements**: 1 found
- **Size**: 7060 bytes, 216 lines

**tests/test_idempotence_and_schemas.py**
- **Responsibility**: Python module: Tests for idempotence (A04, A23) and schema validation (A03). Ensures deterministic execution and pr...
- **Functions**: sample_content() (test_idempotence_and_schemas.py:18), detected_plugins() (test_idempotence_and_schemas.py:38), test_schema_validation_success_a03() (test_idempotence_and_schemas.py:134), test_schema_validation_failure_a03() (test_idempotence_and_schemas.py:184), test_schema_validation_json_error_a03() (test_idempotence_and_schemas.py:218)
- **CLI Elements**: 2 found
- **Size**: 11798 bytes, 312 lines

**tests/test_performance.py**
- **Responsibility**: Python module: Performance tests for TBCV system (P01-P07).  Tests performance targets: - P01: First run: 5-8 s / f...
- **Classes**: PerformanceMetrics (test_performance.py:29)
- **Functions**: __init__() (test_performance.py:32), reset() (test_performance.py:35), add_validation_time() (test_performance.py:43), add_enhancement_time() (test_performance.py:46), add_cache_hit() (test_performance.py:49)
- **CLI Elements**: 2 found
- **Size**: 14425 bytes, 460 lines

**tests/test_smoke_agents.py**
- **Responsibility**: API server and endpoint definitions
- **Functions**: _import_app() (test_smoke_agents.py:15), _normalize_agents() (test_smoke_agents.py:19), _to_flat_agent() (test_smoke_agents.py:43), _validate_flat_agent() (test_smoke_agents.py:85), test_agents_endpoint_registers_and_lists_agents() (test_smoke_agents.py:114)
- **Size**: 6623 bytes, 154 lines

**tests/test_truths_and_rules.py**
- **Responsibility**: Python module: Tests for truths and rules integration in validation system....
- **Classes**: TestTruthsAndRulesIntegration (test_truths_and_rules.py:11), TestCLIIntegration (test_truths_and_rules.py:128), TestAPIIntegration (test_truths_and_rules.py:154)
- **Functions**: test_cli_help_shows_directory_validation() (test_truths_and_rules.py:130), test_cli_validate_directory_help() (test_truths_and_rules.py:141)
- **CLI Elements**: 3 found
- **Size**: 6716 bytes, 190 lines

**tests/test_validation_persistence.py**
- **Responsibility**: API server and endpoint definitions
- **Functions**: test_validation_persist_and_consume() (test_validation_persistence.py:16)
- **Size**: 1422 bytes, 45 lines

**tools/endpoint_check.py**
- **Responsibility**: API server and endpoint definitions
- **Functions**: _parse_app_import() (endpoint_check.py:6), _load_app() (endpoint_check.py:12), _traverse_routes_offline() (endpoint_check.py:19), _static_scan_paths() (endpoint_check.py:32), _http_get() (endpoint_check.py:50)
- **CLI Elements**: 3 found
- **Size**: 5435 bytes, 126 lines

**truth/words.json**
- **Responsibility**: General json file: words.json
- **Size**: 9419 bytes, 324 lines

