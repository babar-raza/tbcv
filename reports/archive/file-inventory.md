# File Inventory Report

> Title: File Inventory
> Version: auto
> Source: file-inventory.json @ 2025-11-03T07:42:05.495257Z

## Summary

- **Total Files**: 92
- **Total Directories**: 22
- **Root Path**: /home/claude

## Root Structure (1-2 levels)

| Path | Kind | Size (bytes) | Purpose |
|------|------|--------------|----------|
| agents | directory | - | Agent implementation modules |
| api | directory | - | API-related modules |
| artifacts | directory | - | File: artifacts |
| cli | directory | - | Command-line interface modules |
| config | directory | - | Configuration files |
| core | directory | - | Core application logic |
| data | directory | - | Data storage and files |
| data/cache | directory | - | File: cache |
| data/logs | directory | - | File: logs |
| data/reports | directory | - | Generated reports and output |
| data/temp | directory | - | File: temp |
| patches | directory | - | File: patches |
| prompts | directory | - | Prompt templates and configurations |
| reports | directory | - | Generated reports and output |
| rules | directory | - | File: rules |
| tbcv.egg-info | directory | - | File: tbcv.egg-info |
| templates | directory | - | Template files |
| tests | directory | - | Test files and fixtures |
| tests/fixtures | directory | - | File: fixtures |
| tests/startup | directory | - | File: startup |
| tools | directory | - | Utility and helper tools |
| truth | directory | - | File: truth |
| .npmrc | data | 74 | Data file: .npmrc |
| .wget-hsts | data | 215 | Data file: .wget-hsts |
| __init__.py | code | 1926 | Python package initializer for claude |
| __main__.py | code | 1238 | Python module entry point |
| agents/__init__.py | code | 1950 | Python package initializer for agents |
| agents/base.py | code | 17922 | Python module: base |
| agents/code_analyzer.py | code | 46918 | Python module: code_analyzer |
| agents/content_enhancer.py | code | 19124 | Python module: content_enhancer |
| agents/content_validator.py | code | 23749 | Python module: content_validator |
| agents/fuzzy_detector.py | code | 7853 | Python module: fuzzy_detector |
| agents/orchestrator.py | code | 14846 | Python module: orchestrator |
| agents/truth_manager.py | code | 28133 | Python module: truth_manager |
| api/dashboard.py | code | 12973 | Python module: dashboard |
| api/export_endpoints.py | code | 14350 | Python module: export_endpoints |
| api/server.py | code | 35753 | Python module: server |
| api/server_extensions.py | code | 6944 | Python module: server_extensions |
| api/websocket_endpoints.py | code | 8001 | Python module: websocket_endpoints |
| artifacts/import_map.json | config | 227 | Configuration: import_map.json |
| cli/main.py | code | 29931 | Main application entry point |
| config/main.yaml | config | 4046 | Configuration: main.yaml |
| core/__init__.py | code | 634 | Python package initializer for core |
| core/__main__.py | code | 161 | Python module entry point |
| core/cache.py | code | 17462 | Python module: cache |
| core/config.py | code | 11162 | Python module: config |
| core/database.py | code | 30935 | Python module: database |
| core/logging.py | code | 15649 | Python module: logging |
| core/ollama.py | code | 15974 | Python module: ollama |
| core/ollama_validator.py | code | 8187 | Python module: ollama_validator |
| core/prompt_loader.py | code | 9059 | Python module: prompt_loader |
| core/rule_manager.py | code | 5854 | Python module: rule_manager |
| core/utilities.py | code | 2479 | Python module: utilities |
| core/validation_store.py | code | 5728 | Python module: validation_store |
| data/tbcv.db | data | 266240 | Database file |
| init.py | code | 1617 | Python module: init |
| main.py | code | 8512 | Main application entry point |
| prompts/code_analysis.json | config | 1249 | Configuration: code_analysis.json |
| prompts/enhancer.json | config | 356 | Configuration: enhancer.json |
| prompts/validator.json | config | 1427 | Configuration: validator.json |
| pyproject.toml | config | 2677 | Python project configuration |
| pytest.ini | config | 317 | Pytest configuration |
| reports/endpoint_mismatches.json | config | 310 | Configuration: endpoint_mismatches.json |
| reports/endpoints_offline.json | config | 6107 | Configuration: endpoints_offline.json |
| reports/health_fix_report.json | config | 654 | Configuration: health_fix_report.json |
| reports/inventory.json | config | 8151 | Configuration: inventory.json |
| reports/patch_apply.json | config | 457 | Configuration: patch_apply.json |
| reports/status_update.json | config | 440 | Configuration: status_update.json |
| reports/validation_run.json | config | 443 | Configuration: validation_run.json |
| requirements.md | docs | 11479 | Documentation: requirements |
| requirements.txt | docs | 1587 | Python dependencies specification |
| requirements_mapping.md | docs | 14785 | Documentation: requirements_mapping |
| rules/__init__.py | code | 114 | Python package initializer for rules |
| rules/words.json | config | 4156 | Configuration: words.json |
| stage1_inventory.py | code | 7579 | Python module: stage1_inventory |
| system.md | docs | 30223 | System architecture documentation |
| tbcv.db | data | 266240 | Database file |
| tbcv.egg-info/PKG-INFO | data | 965 | Data file: pkg-info |
| tbcv.egg-info/SOURCES.txt | docs | 479 | Documentation: sources.txt |
| tbcv.egg-info/dependency_links.txt | docs | 1 | Documentation: dependency_links.txt |
| tbcv.egg-info/entry_points.txt | docs | 44 | Documentation: entry_points.txt |
| tbcv.egg-info/requires.txt | docs | 353 | Documentation: requires.txt |
| tbcv.egg-info/top_level.txt | docs | 1 | Documentation: top_level.txt |
| templates/audit_logs.html | assets | 874 | File: audit_logs.html |
| templates/base.html | assets | 8826 | File: base.html |
| templates/dashboard_home.html | assets | 5230 | File: dashboard_home.html |
| templates/recommendation_detail.html | assets | 6234 | File: recommendation_detail.html |
| templates/recommendations_list.html | assets | 3556 | File: recommendations_list.html |
| templates/validation_detail.html | assets | 3030 | File: validation_detail.html |
| templates/validations_list.html | assets | 3355 | File: validations_list.html |
| templates/workflow_detail.html | assets | 1321 | File: workflow_detail.html |
| templates/workflows_list.html | assets | 1052 | File: workflows_list.html |
| tests/conftest.py | code | 2086 | Python module: conftest |
| tests/test_endpoints_live.py | code | 4098 | Python module: test_endpoints_live |
| tests/test_endpoints_offline.py | code | 4521 | Python module: test_endpoints_offline |
| tests/test_enhancer_consumes_validation.py | code | 785 | Python module: test_enhancer_consumes_validation |
| tests/test_framework.py | code | 6164 | Python module: test_framework |
| tests/test_generic_validator.py | code | 7275 | Python module: test_generic_validator |
| tests/test_idempotence_and_schemas.py | code | 12109 | Python module: test_idempotence_and_schemas |
| tests/test_performance.py | code | 14936 | Python module: test_performance |
| tests/test_smoke_agents.py | code | 6778 | Python module: test_smoke_agents |
| tests/test_truths_and_rules.py | code | 6905 | Python module: test_truths_and_rules |
| tests/test_validation_persistence.py | code | 1466 | Python module: test_validation_persistence |
| tools/endpoint_check.py | code | 5435 | Python module: endpoint_check |
| truth/words.json | config | 9760 | Configuration: words.json |

## Complete File Listing

| Path | Kind | Size (bytes) | Purpose |
|------|------|--------------|----------|
| .npmrc | data | 74 | Data file: .npmrc |
| .wget-hsts | data | 215 | Data file: .wget-hsts |
| __init__.py | code | 1926 | Python package initializer for claude |
| __main__.py | code | 1238 | Python module entry point |
| agents | directory | - | Agent implementation modules |
| agents/__init__.py | code | 1950 | Python package initializer for agents |
| agents/base.py | code | 17922 | Python module: base |
| agents/code_analyzer.py | code | 46918 | Python module: code_analyzer |
| agents/content_enhancer.py | code | 19124 | Python module: content_enhancer |
| agents/content_validator.py | code | 23749 | Python module: content_validator |
| agents/fuzzy_detector.py | code | 7853 | Python module: fuzzy_detector |
| agents/orchestrator.py | code | 14846 | Python module: orchestrator |
| agents/truth_manager.py | code | 28133 | Python module: truth_manager |
| api | directory | - | API-related modules |
| api/dashboard.py | code | 12973 | Python module: dashboard |
| api/export_endpoints.py | code | 14350 | Python module: export_endpoints |
| api/server.py | code | 35753 | Python module: server |
| api/server_extensions.py | code | 6944 | Python module: server_extensions |
| api/websocket_endpoints.py | code | 8001 | Python module: websocket_endpoints |
| artifacts | directory | - | File: artifacts |
| artifacts/import_map.json | config | 227 | Configuration: import_map.json |
| cli | directory | - | Command-line interface modules |
| cli/main.py | code | 29931 | Main application entry point |
| config | directory | - | Configuration files |
| config/main.yaml | config | 4046 | Configuration: main.yaml |
| core | directory | - | Core application logic |
| core/__init__.py | code | 634 | Python package initializer for core |
| core/__main__.py | code | 161 | Python module entry point |
| core/cache.py | code | 17462 | Python module: cache |
| core/config.py | code | 11162 | Python module: config |
| core/database.py | code | 30935 | Python module: database |
| core/logging.py | code | 15649 | Python module: logging |
| core/ollama.py | code | 15974 | Python module: ollama |
| core/ollama_validator.py | code | 8187 | Python module: ollama_validator |
| core/prompt_loader.py | code | 9059 | Python module: prompt_loader |
| core/rule_manager.py | code | 5854 | Python module: rule_manager |
| core/utilities.py | code | 2479 | Python module: utilities |
| core/validation_store.py | code | 5728 | Python module: validation_store |
| data | directory | - | Data storage and files |
| data/cache | directory | - | File: cache |
| data/logs | directory | - | File: logs |
| data/logs/tbcv.log | data | 540315 | Data file: tbcv.log |
| data/reports | directory | - | Generated reports and output |
| data/reports/endpoint_probe_20251028_151325.json | config | 20973 | Configuration: endpoint_probe_20251028_151325.json |
| data/reports/endpoint_probe_20251028_151325.md | docs | 9322 | Documentation: endpoint_probe_20251028_151325 |
| data/reports/endpoint_probe_20251028_151436.json | config | 19470 | Configuration: endpoint_probe_20251028_151436.json |
| data/reports/endpoint_probe_20251028_151436.md | docs | 7394 | Documentation: endpoint_probe_20251028_151436 |
| data/tbcv.db | data | 266240 | Database file |
| data/temp | directory | - | File: temp |
| init.py | code | 1617 | Python module: init |
| main.py | code | 8512 | Main application entry point |
| patches | directory | - | File: patches |
| prompts | directory | - | Prompt templates and configurations |
| prompts/code_analysis.json | config | 1249 | Configuration: code_analysis.json |
| prompts/enhancer.json | config | 356 | Configuration: enhancer.json |
| prompts/validator.json | config | 1427 | Configuration: validator.json |
| pyproject.toml | config | 2677 | Python project configuration |
| pytest.ini | config | 317 | Pytest configuration |
| reports | directory | - | Generated reports and output |
| reports/endpoint_mismatches.json | config | 310 | Configuration: endpoint_mismatches.json |
| reports/endpoints_offline.json | config | 6107 | Configuration: endpoints_offline.json |
| reports/health_fix_report.json | config | 654 | Configuration: health_fix_report.json |
| reports/inventory.json | config | 8151 | Configuration: inventory.json |
| reports/patch_apply.json | config | 457 | Configuration: patch_apply.json |
| reports/status_update.json | config | 440 | Configuration: status_update.json |
| reports/validation_run.json | config | 443 | Configuration: validation_run.json |
| requirements.md | docs | 11479 | Documentation: requirements |
| requirements.txt | docs | 1587 | Python dependencies specification |
| requirements_mapping.md | docs | 14785 | Documentation: requirements_mapping |
| rules | directory | - | File: rules |
| rules/__init__.py | code | 114 | Python package initializer for rules |
| rules/words.json | config | 4156 | Configuration: words.json |
| stage1_inventory.py | code | 7579 | Python module: stage1_inventory |
| system.md | docs | 30223 | System architecture documentation |
| tbcv.db | data | 266240 | Database file |
| tbcv.egg-info | directory | - | File: tbcv.egg-info |
| tbcv.egg-info/PKG-INFO | data | 965 | Data file: pkg-info |
| tbcv.egg-info/SOURCES.txt | docs | 479 | Documentation: sources.txt |
| tbcv.egg-info/dependency_links.txt | docs | 1 | Documentation: dependency_links.txt |
| tbcv.egg-info/entry_points.txt | docs | 44 | Documentation: entry_points.txt |
| tbcv.egg-info/requires.txt | docs | 353 | Documentation: requires.txt |
| tbcv.egg-info/top_level.txt | docs | 1 | Documentation: top_level.txt |
| templates | directory | - | Template files |
| templates/audit_logs.html | assets | 874 | File: audit_logs.html |
| templates/base.html | assets | 8826 | File: base.html |
| templates/dashboard_home.html | assets | 5230 | File: dashboard_home.html |
| templates/recommendation_detail.html | assets | 6234 | File: recommendation_detail.html |
| templates/recommendations_list.html | assets | 3556 | File: recommendations_list.html |
| templates/validation_detail.html | assets | 3030 | File: validation_detail.html |
| templates/validations_list.html | assets | 3355 | File: validations_list.html |
| templates/workflow_detail.html | assets | 1321 | File: workflow_detail.html |
| templates/workflows_list.html | assets | 1052 | File: workflows_list.html |
| tests | directory | - | Test files and fixtures |
| tests/conftest.py | code | 2086 | Python module: conftest |
| tests/fixtures | directory | - | File: fixtures |
| tests/fixtures/multi_plugin_content.md | docs | 1754 | Documentation: multi_plugin_content |
| tests/fixtures/truths_and_rules_test.md | docs | 2335 | Documentation: truths_and_rules_test |
| tests/fixtures/yaml_only_content.md | docs | 373 | Documentation: yaml_only_content |
| tests/startup | directory | - | File: startup |
| tests/startup/test_rule_manager_imports.py | code | 1502 | Python module: test_rule_manager_imports |
| tests/test_endpoints_live.py | code | 4098 | Python module: test_endpoints_live |
| tests/test_endpoints_offline.py | code | 4521 | Python module: test_endpoints_offline |
| tests/test_enhancer_consumes_validation.py | code | 785 | Python module: test_enhancer_consumes_validation |
| tests/test_framework.py | code | 6164 | Python module: test_framework |
| tests/test_generic_validator.py | code | 7275 | Python module: test_generic_validator |
| tests/test_idempotence_and_schemas.py | code | 12109 | Python module: test_idempotence_and_schemas |
| tests/test_performance.py | code | 14936 | Python module: test_performance |
| tests/test_smoke_agents.py | code | 6778 | Python module: test_smoke_agents |
| tests/test_truths_and_rules.py | code | 6905 | Python module: test_truths_and_rules |
| tests/test_validation_persistence.py | code | 1466 | Python module: test_validation_persistence |
| tools | directory | - | Utility and helper tools |
| tools/endpoint_check.py | code | 5435 | Python module: endpoint_check |
| truth | directory | - | File: truth |
| truth/words.json | config | 9760 | Configuration: words.json |
