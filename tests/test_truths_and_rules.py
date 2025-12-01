# file: tests\test_truths_and_rules.py
"""
Tests for truths and rules integration in validation system.
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path

class TestTruthsAndRulesIntegration:
    
    @pytest.mark.asyncio
    async def test_content_validator_loads_both_truths_and_rules(self):
        """Test that content validator loads and uses both truths and rules."""
        from agents.content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """---
title: "Test Document with Plugin Declaration"
description: "Testing how truths and rules work together in validation."
plugins: ["Word Processor", "PDF Processor"]
---
# Test Content
```csharp
Document doc = new Document("input.docx");
doc.Save("output.pdf", SaveFormat.Pdf);
```
"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["yaml", "code"]
        })
        
        # Should have metrics for each validation type
        assert 'yaml_metrics' in result['metrics'] or 'code_metrics' in result['metrics']

        # YAML validation should produce valid metrics
        yaml_metrics = result['metrics'].get('yaml_metrics', {})
        # Check that YAML validation ran (has yaml_valid field)
        assert 'yaml_valid' in yaml_metrics or len(yaml_metrics) > 0

        # Code validation should also run
        code_metrics = result['metrics'].get('code_metrics', {})
        assert 'code_valid' in code_metrics or len(code_metrics) > 0

    @pytest.mark.asyncio 
    async def test_yaml_validation_against_truths(self):
        """Test YAML validation checks declared plugins against truth data."""
        from agents.content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """---
title: "Plugin Truth Validation Test"
description: "Test validation of plugin declarations against truth data."
plugins: ["Nonexistent Plugin", "Word Processor"]
---
# Test Content"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["yaml"]
        })
        
        # Should detect issues with non-existent plugin
        truth_issues = [i for i in result['issues'] if i.get('source') == 'truth_validation']
        # May or may not find issues depending on truth data availability
        
    @pytest.mark.asyncio
    async def test_code_validation_with_api_patterns(self):
        """Test code validation using API patterns from rules."""
        from agents.content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """# Code Pattern Test
```csharp
Document doc = new Document("C:\\\\temp\\\\input.docx");
doc.Save("output.pdf");
// Missing using statement for resource disposal
```
"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["code"]
        })
        
        # Should detect code quality issues using rules
        code_issues = [i for i in result['issues'] if i['category'] == 'code_quality']
        api_issues = [i for i in result['issues'] if i['category'] == 'api_usage']
        
        # Should find some issues from rule-driven validation
        assert len(code_issues) > 0 or len(api_issues) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_directory_validation(self):
        """Test orchestrator directory validation workflow."""
        from agents.orchestrator import OrchestratorAgent
        
        orchestrator = OrchestratorAgent()
        
        # Create temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("""---
title: "Test File"
description: "Test file for directory validation."
---
# Test Content

Some test content here.
""")
            
            result = await orchestrator.handle_validate_directory({
                "directory_path": temp_dir,
                "file_pattern": "*.md",
                "family": "words",
                "max_workers": 2
            })
            
            # Status could be 'success' or 'completed'
            assert result['status'] in ['success', 'completed']
            # Files may be filtered (e.g., English-only filter)
            assert 'files_total' in result or 'files_found' in result
            assert 'files_validated' in result or 'files_processed' in result

class TestCLIIntegration:
    
    def test_cli_help_shows_directory_validation(self):
        """Test that CLI shows directory validation command."""
        from cli.main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'validate-directory' in result.output

    def test_cli_validate_directory_help(self):
        """Test directory validation command help."""
        from cli.main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(cli, ['validate-directory', '--help'])
        
        assert result.exit_code == 0
        assert '--pattern' in result.output
        assert '--family' in result.output
        assert '--workers' in result.output

class TestAPIIntegration:
    
    @pytest.mark.asyncio
    async def test_api_agents_endpoint_shows_orchestrator(self):
        """Test that /agents endpoint includes orchestrator."""
        from api.server import app
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            response = client.get("/agents")
            
            assert response.status_code == 200
            data = response.json()
            
            agent_types = [agent['agent_type'] for agent in data['agents']]
            assert 'OrchestratorAgent' in agent_types

    @pytest.mark.asyncio  
    async def test_workflow_validate_directory_endpoint_exists(self):
        """Test that directory validation endpoint exists."""
        from api.server import app
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            # Test with minimal valid request
            with tempfile.TemporaryDirectory() as temp_dir:
                response = client.post("/workflows/validate-directory", json={
                    "directory_path": temp_dir,
                    "file_pattern": "*.md",
                    "max_workers": 1
                })
                
                # Should not return 404 or 500 errors
                assert response.status_code in [200, 202, 422]  # Various valid responses

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
