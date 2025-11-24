import requests
import json

content = """---
title: Test
---
# Test
Test content using Aspose.Words for .NET
"""

r = requests.post(
    'http://127.0.0.1:8000/api/validate',
    json={
        'content': content,
        'file_path': 'test.md',
        'family': 'words',
        'validation_types': ['yaml', 'markdown', 'Truth', 'FuzzyLogic']
    },
    timeout=60
)

print('Status:', r.status_code)
result = r.json()

print('Has validation_id:', 'id' in result or 'validation_id' in result)
if 'id' in result:
    print('Validation ID:', result['id'])

print('Has fuzzy detection:', 'plugin_detection' in result)
print('Has LLM validation:', 'llm_validation' in result)
print('Validation mode:', result.get('validation_mode'))
print('LLM enabled:', result.get('llm_enabled'))
print('Overall confidence:', result.get('overall_confidence'))

# Check for fuzzy unavailable warning
all_issues = result.get('final_issues', []) + result.get('content_validation', {}).get('issues', [])
fuzzy_unavailable = any('fuzzy' in str(issue).lower() and 'unavailable' in str(issue).lower() for issue in all_issues)
print('Fuzzy unavailable warning:', fuzzy_unavailable)

with open('test_result.json', 'w') as f:
    json.dump(result, f, indent=2)

print('\nSaved to test_result.json')
