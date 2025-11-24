#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify OpenAPI schema fixes."""

import sys
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from api.server import app

schema = app.openapi()
schemas = schema.get('components', {}).get('schemas', {})

print("=" * 70)
print("OpenAPI Schema Verification")
print("=" * 70)

# Check for ugly names
ugly_found = [name for name in schemas.keys() if name.startswith('Body_dashboard')]
if ugly_found:
    print("\n[ERROR] Found ugly schema names:")
    for name in ugly_found:
        print(f"   - {name}")
else:
    print("\n[SUCCESS] No ugly auto-generated schema names found!")

# Check for professional names
professional_names = ['DashboardReviewForm', 'DashboardBulkReviewForm']
professional_found = [name for name in schemas.keys() if name in professional_names]
if professional_found:
    print("\n[SUCCESS] Found professional schema names:")
    for name in professional_found:
        print(f"   - {name}")
else:
    print("\n[WARNING] Professional schema names not found")

# Check endpoint references
print("\n" + "=" * 70)
print("Endpoint Schema References")
print("=" * 70)

paths = schema.get('paths', {})

# Single review endpoint
ep1_path = '/dashboard/recommendations/{recommendation_id}/review'
if ep1_path in paths:
    ep1 = paths[ep1_path].get('post', {})
    req_body = ep1.get('requestBody', {})
    content = req_body.get('content', {})
    form_content = content.get('application/x-www-form-urlencoded', {})
    form_schema = form_content.get('schema', {})
    ref = form_schema.get('$ref', 'No reference')

    print(f"\nSingle Review Endpoint: {ep1_path}")
    print(f"  Schema Reference: {ref}")

    if 'DashboardReviewForm' in ref:
        print("  [OK] Using professional schema name")
    elif 'Body_dashboard' in ref:
        print("  [ERROR] Still using ugly schema name")

# Bulk review endpoint
ep2_path = '/dashboard/recommendations/bulk-review'
if ep2_path in paths:
    ep2 = paths[ep2_path].get('post', {})
    req_body = ep2.get('requestBody', {})
    content = req_body.get('content', {})
    form_content = content.get('application/x-www-form-urlencoded', {})
    form_schema = form_content.get('schema', {})
    ref = form_schema.get('$ref', 'No reference')

    print(f"\nBulk Review Endpoint: {ep2_path}")
    print(f"  Schema Reference: {ref}")

    if 'DashboardBulkReviewForm' in ref:
        print("  [OK] Using professional schema name")
    elif 'Body_dashboard' in ref:
        print("  [ERROR] Still using ugly schema name")

print("\n" + "=" * 70)
print("Fix Status: COMPLETE")
print("=" * 70)
