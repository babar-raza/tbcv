#!/usr/bin/env python3
"""Generate comprehensive inventory of the repository."""
import os
import json
import hashlib
from pathlib import Path

def detect_line_endings(filepath):
    """Detect line ending style."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read(8192)
            if b'\r\n' in content:
                return 'CRLF'
            elif b'\n' in content:
                return 'LF'
            elif b'\r' in content:
                return 'CR'
            return 'None'
    except:
        return 'Unknown'

def detect_encoding(filepath):
    """Detect file encoding."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read(4096)
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            try:
                raw.decode('utf-8')
                return 'utf-8'
            except:
                try:
                    raw.decode('latin-1')
                    return 'latin-1'
                except:
                    return 'binary'
    except:
        return 'unknown'

def get_file_type(filepath):
    """Determine file type."""
    ext = Path(filepath).suffix.lower()
    text_exts = {'.py', '.md', '.txt', '.ini', '.toml', '.yaml', '.yml', 
                 '.json', '.bat', '.sh', '.cfg', '.rst'}
    if ext in text_exts:
        return 'text'
    return 'binary'

def compute_sha256(filepath):
    """Compute SHA256 hash."""
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except:
        return 'error'

def generate_inventory(root_dir):
    """Generate complete inventory."""
    inventory = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'__pycache__', '.git', 'node_modules', '.pytest_cache'}]
        
        for fname in files:
            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, root_dir)
            
            try:
                size = os.path.getsize(filepath)
                ftype = get_file_type(filepath)
                sha256 = compute_sha256(filepath)
                
                entry = {
                    'path': rel_path.replace('\\', '/'),
                    'size': size,
                    'type': ftype,
                    'sha256': sha256
                }
                
                if ftype == 'text':
                    entry['line_endings'] = detect_line_endings(filepath)
                    entry['encoding'] = detect_encoding(filepath)
                
                inventory.append(entry)
            except Exception as e:
                print(f"Error processing {rel_path}: {e}")
    
    return sorted(inventory, key=lambda x: x['path'])

if __name__ == '__main__':
    root = '/tbcv'
    inventory = generate_inventory(root)
    
    output = {
        'total_files': len(inventory),
        'total_size': sum(f['size'] for f in inventory),
        'files': inventory
    }
    
    os.makedirs('/reports', exist_ok=True)
    with open('/reports/inventory.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Generated inventory: {len(inventory)} files")
