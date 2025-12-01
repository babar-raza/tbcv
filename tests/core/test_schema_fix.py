#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify OpenAPI schema fixes."""

import pytest


class TestOpenAPISchemaFixes:
    """Test that OpenAPI schema uses professional naming."""

    @pytest.fixture
    def openapi_schema(self):
        """Get OpenAPI schema from app."""
        from api.server import app
        return app.openapi()

    def test_no_ugly_auto_generated_schema_names(self, openapi_schema):
        """Verify no ugly auto-generated schema names like 'Body_dashboard'."""
        schemas = openapi_schema.get('components', {}).get('schemas', {})
        ugly_names = [name for name in schemas.keys() if name.startswith('Body_dashboard')]
        assert len(ugly_names) == 0, f"Found ugly schema names: {ugly_names}"

    def test_has_professional_schema_names(self, openapi_schema):
        """Verify professional schema names are present."""
        schemas = openapi_schema.get('components', {}).get('schemas', {})
        schema_names = list(schemas.keys())

        professional_names = ['DashboardReviewForm', 'DashboardBulkReviewForm']
        for name in professional_names:
            assert name in schema_names, f"Professional schema name '{name}' not found"

    def test_single_review_endpoint_uses_professional_schema(self, openapi_schema):
        """Verify single review endpoint references professional schema."""
        paths = openapi_schema.get('paths', {})
        ep_path = '/dashboard/recommendations/{recommendation_id}/review'

        assert ep_path in paths, f"Endpoint {ep_path} not found"

        ep = paths[ep_path].get('post', {})
        req_body = ep.get('requestBody', {})
        content = req_body.get('content', {})
        form_content = content.get('application/x-www-form-urlencoded', {})
        form_schema = form_content.get('schema', {})
        ref = form_schema.get('$ref', '')

        assert 'DashboardReviewForm' in ref, f"Expected DashboardReviewForm in schema ref, got: {ref}"
        assert 'Body_dashboard' not in ref, f"Ugly schema name found in ref: {ref}"

    def test_bulk_review_endpoint_uses_professional_schema(self, openapi_schema):
        """Verify bulk review endpoint references professional schema."""
        paths = openapi_schema.get('paths', {})
        ep_path = '/dashboard/recommendations/bulk-review'

        assert ep_path in paths, f"Endpoint {ep_path} not found"

        ep = paths[ep_path].get('post', {})
        req_body = ep.get('requestBody', {})
        content = req_body.get('content', {})
        form_content = content.get('application/x-www-form-urlencoded', {})
        form_schema = form_content.get('schema', {})
        ref = form_schema.get('$ref', '')

        assert 'DashboardBulkReviewForm' in ref, f"Expected DashboardBulkReviewForm in schema ref, got: {ref}"
        assert 'Body_dashboard' not in ref, f"Ugly schema name found in ref: {ref}"
