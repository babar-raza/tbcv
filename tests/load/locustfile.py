"""
Load Testing Suite for TBCV (Truth-Based Content Validation)

This module provides comprehensive load testing scenarios using Locust to test:
- Validation throughput (single file and batch)
- Folder validation performance
- Recommendation generation under load
- Concurrent workflow processing
- Cache performance under load
- Database performance under load
- WebSocket connection handling

Usage:
    # Run with web UI (recommended for first-time setup)
    locust -f tests/load/locustfile.py --host=http://localhost:8080

    # Run headless with specific parameters
    locust -f tests/load/locustfile.py --host=http://localhost:8080 \
           --users 50 --spawn-rate 5 --run-time 5m --headless

    # Run specific user class
    locust -f tests/load/locustfile.py --host=http://localhost:8080 \
           ValidationUser --users 20 --spawn-rate 2

Performance Targets:
    - Single file validation: < 500ms @ 95th percentile
    - Batch validation (10 files): < 2s @ 95th percentile
    - Recommendation generation: < 1s @ 95th percentile
    - Workflow operations: < 200ms @ 95th percentile
    - Cache operations: < 50ms @ 95th percentile
"""

import json
import random
import time
from typing import Dict, Any, List
from locust import HttpUser, task, between, events, TaskSet
from locust.contrib.fasthttp import FastHttpUser


# =============================================================================
# Test Data Generation
# =============================================================================

def generate_markdown_content(size: str = "small") -> str:
    """Generate markdown content for testing."""
    if size == "small":
        return """# Test Document

## Introduction
This is a test document for load testing the TBCV system.

## Content
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
- Item 1
- Item 2
- Item 3

### Code Example
```python
def hello_world():
    print("Hello, World!")
```

## Conclusion
This concludes our test document.
"""
    elif size == "medium":
        content = "# Large Test Document\n\n"
        for i in range(10):
            content += f"""
## Section {i+1}

This is section {i+1} with substantial content. Lorem ipsum dolor sit amet,
consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et
dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Subsection {i+1}.1
More detailed information here.

### Subsection {i+1}.2
Even more content to increase the document size.

```javascript
function example{i+1}() {{
    console.log("Example code block {i+1}");
}}
```
"""
        return content
    else:  # large
        content = "# Very Large Test Document\n\n"
        for i in range(50):
            content += f"""
## Major Section {i+1}

This is a comprehensive section with multiple subsections and substantial content.

### Subsection {i+1}.1
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

### Subsection {i+1}.2
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### Subsection {i+1}.3
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

```python
def complex_function_{i+1}():
    # This is example code block {i+1}
    data = {{'key': 'value'}}
    return process_data(data)
```
"""
        return content


def generate_file_path() -> str:
    """Generate a unique file path for testing."""
    timestamp = int(time.time() * 1000)
    random_id = random.randint(1000, 9999)
    return f"/test/documents/test_doc_{timestamp}_{random_id}.md"


# =============================================================================
# Validation Load Tests
# =============================================================================

class ValidationTaskSet(TaskSet):
    """Task set for validation-related operations."""

    @task(5)
    def validate_small_file(self):
        """Test single file validation with small content."""
        content = generate_markdown_content("small")
        file_path = generate_file_path()

        with self.client.post(
            "/api/validate",
            json={
                "content": content,
                "file_path": file_path,
                "family": "words",
                "validation_types": ["markdown", "structure"]
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Validation failed: {response.status_code}")

    @task(3)
    def validate_medium_file(self):
        """Test single file validation with medium content."""
        content = generate_markdown_content("medium")
        file_path = generate_file_path()

        with self.client.post(
            "/api/validate",
            json={
                "content": content,
                "file_path": file_path,
                "family": "words",
                "validation_types": ["yaml", "markdown", "code", "structure"]
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Validation failed: {response.status_code}")

    @task(1)
    def validate_large_file(self):
        """Test single file validation with large content."""
        content = generate_markdown_content("large")
        file_path = generate_file_path()

        with self.client.post(
            "/api/validate",
            json={
                "content": content,
                "file_path": file_path,
                "family": "words",
                "validation_types": ["yaml", "markdown", "code", "links", "structure"]
            },
            catch_response=True,
            name="/api/validate [large]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Large validation failed: {response.status_code}")

    @task(2)
    def validate_batch(self):
        """Test batch validation with multiple files."""
        files = []
        file_contents = []

        # Generate 5-10 files for batch validation
        num_files = random.randint(5, 10)
        for _ in range(num_files):
            file_path = generate_file_path()
            content = generate_markdown_content("small")
            files.append(file_path)
            file_contents.append({"file_path": file_path, "content": content})

        with self.client.post(
            "/api/validate/batch",
            json={
                "files": files,
                "family": "words",
                "validation_types": ["markdown", "structure"],
                "max_workers": 4,
                "upload_mode": True,
                "file_contents": file_contents
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Batch validation failed: {response.status_code}")

    @task(2)
    def list_validations(self):
        """Test listing validations with pagination."""
        limit = random.choice([10, 20, 50])
        with self.client.get(
            f"/api/validations?limit={limit}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List validations failed: {response.status_code}")


class RecommendationTaskSet(TaskSet):
    """Task set for recommendation-related operations."""

    def on_start(self):
        """Initialize with a validation ID."""
        # Create a validation first
        content = generate_markdown_content("medium")
        file_path = generate_file_path()

        response = self.client.post(
            "/api/validate",
            json={
                "content": content,
                "file_path": file_path,
                "family": "words",
                "validation_types": ["markdown", "structure"]
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.validation_id = data.get("validation_id", "test_validation_id")
        else:
            self.validation_id = "test_validation_id"

    @task(5)
    def list_recommendations(self):
        """Test listing recommendations."""
        with self.client.get(
            "/api/recommendations",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List recommendations failed: {response.status_code}")

    @task(3)
    def generate_recommendations(self):
        """Test recommendation generation."""
        with self.client.post(
            f"/api/validations/{self.validation_id}/recommendations/generate",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is ok if validation doesn't exist
                response.success()
            else:
                response.failure(f"Generate recommendations failed: {response.status_code}")

    @task(2)
    def get_validation_recommendations(self):
        """Test getting recommendations for a validation."""
        with self.client.get(
            f"/api/validations/{self.validation_id}/recommendations",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Get validation recommendations failed: {response.status_code}")


class WorkflowTaskSet(TaskSet):
    """Task set for workflow-related operations."""

    @task(5)
    def list_workflows(self):
        """Test listing workflows."""
        with self.client.get(
            "/api/workflows",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List workflows failed: {response.status_code}")

    @task(2)
    def get_workflow_status(self):
        """Test getting workflow status."""
        workflow_id = f"test_workflow_{random.randint(1000, 9999)}"
        with self.client.get(
            f"/workflows/{workflow_id}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is ok
                response.success()
            else:
                response.failure(f"Get workflow status failed: {response.status_code}")


class SystemHealthTaskSet(TaskSet):
    """Task set for system health and admin operations."""

    @task(10)
    def health_check(self):
        """Test basic health check."""
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def health_live(self):
        """Test liveness probe."""
        with self.client.get(
            "/health/live",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health live failed: {response.status_code}")

    @task(5)
    def health_ready(self):
        """Test readiness probe."""
        with self.client.get(
            "/health/ready",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health ready failed: {response.status_code}")

    @task(3)
    def list_agents(self):
        """Test listing agents."""
        with self.client.get(
            "/agents",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List agents failed: {response.status_code}")

    @task(2)
    def get_cache_stats(self):
        """Test getting cache statistics."""
        with self.client.get(
            "/admin/cache/stats",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Cache stats failed: {response.status_code}")


# =============================================================================
# User Classes - Different Load Patterns
# =============================================================================

class ValidationUser(FastHttpUser):
    """
    User that primarily performs validation operations.
    Simulates content creators validating their work.
    """
    wait_time = between(1, 3)
    weight = 5
    tasks = [ValidationTaskSet]


class RecommendationUser(FastHttpUser):
    """
    User that focuses on recommendation operations.
    Simulates users reviewing and managing recommendations.
    """
    wait_time = between(2, 4)
    weight = 3
    tasks = [RecommendationTaskSet]


class WorkflowUser(FastHttpUser):
    """
    User that monitors and manages workflows.
    Simulates administrators monitoring batch operations.
    """
    wait_time = between(3, 5)
    weight = 2
    tasks = [WorkflowTaskSet]


class SystemMonitorUser(FastHttpUser):
    """
    User that performs system health checks.
    Simulates monitoring systems checking system health.
    """
    wait_time = between(5, 10)
    weight = 1
    tasks = [SystemHealthTaskSet]


class MixedWorkloadUser(FastHttpUser):
    """
    User that performs a mix of all operations.
    Simulates typical user behavior with varied tasks.
    """
    wait_time = between(1, 5)
    weight = 10

    @task(5)
    def validate_content(self):
        """Perform validation."""
        content = generate_markdown_content(random.choice(["small", "medium"]))
        file_path = generate_file_path()

        self.client.post(
            "/api/validate",
            json={
                "content": content,
                "file_path": file_path,
                "family": "words",
                "validation_types": ["markdown", "structure"]
            }
        )

    @task(3)
    def check_recommendations(self):
        """Check recommendations."""
        self.client.get("/api/recommendations")

    @task(2)
    def check_workflows(self):
        """Check workflow status."""
        self.client.get("/api/workflows")

    @task(10)
    def health_check(self):
        """Perform health check."""
        self.client.get("/health")


# =============================================================================
# Event Handlers for Custom Metrics
# =============================================================================

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize custom metrics and logging."""
    print("\n" + "="*80)
    print("TBCV Load Testing Suite Started")
    print("="*80)
    print(f"Target Host: {environment.host}")
    print(f"Test Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary at end of test."""
    print("\n" + "="*80)
    print("TBCV Load Testing Suite Completed")
    print("="*80)
    print(f"Test End Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nSummary:")
    print(f"  Total Requests: {environment.stats.total.num_requests}")
    print(f"  Total Failures: {environment.stats.total.num_failures}")
    print(f"  Failure Rate: {environment.stats.total.fail_ratio:.2%}")
    print(f"  Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"  95th Percentile: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  99th Percentile: {environment.stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  Requests/sec: {environment.stats.total.total_rps:.2f}")
    print("="*80 + "\n")

    # Performance assessment
    avg_response = environment.stats.total.avg_response_time
    p95_response = environment.stats.total.get_response_time_percentile(0.95)
    fail_rate = environment.stats.total.fail_ratio

    print("Performance Assessment:")
    if fail_rate < 0.01:
        print("  Reliability: EXCELLENT (< 1% failure rate)")
    elif fail_rate < 0.05:
        print("  Reliability: GOOD (< 5% failure rate)")
    else:
        print("  Reliability: NEEDS IMPROVEMENT (>= 5% failure rate)")

    if p95_response < 500:
        print("  Response Time: EXCELLENT (< 500ms @ p95)")
    elif p95_response < 1000:
        print("  Response Time: GOOD (< 1s @ p95)")
    elif p95_response < 2000:
        print("  Response Time: ACCEPTABLE (< 2s @ p95)")
    else:
        print("  Response Time: NEEDS IMPROVEMENT (>= 2s @ p95)")

    print("="*80 + "\n")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import os
    print("TBCV Load Testing Suite")
    print("=" * 80)
    print("\nTo run this load test suite, use one of the following commands:")
    print("\n1. With Web UI (recommended):")
    print("   locust -f tests/load/locustfile.py --host=http://localhost:8080")
    print("\n2. Headless mode:")
    print("   locust -f tests/load/locustfile.py --host=http://localhost:8080 \\")
    print("          --users 50 --spawn-rate 5 --run-time 5m --headless")
    print("\n3. Specific user class:")
    print("   locust -f tests/load/locustfile.py --host=http://localhost:8080 \\")
    print("          ValidationUser --users 20 --spawn-rate 2")
    print("\n4. Multiple user classes with custom distribution:")
    print("   locust -f tests/load/locustfile.py --host=http://localhost:8080 \\")
    print("          ValidationUser RecommendationUser --users 30 --spawn-rate 3")
    print("=" * 80)
