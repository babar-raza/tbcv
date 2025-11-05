import sys
import importlib

# Expose this package as 'core' for backward compatibility
sys.modules.setdefault('core', sys.modules[__name__])

# List of submodules to alias
for sub in ['cache', 'config', 'logging', 'database', 'validation_store', 'rule_manager', 'ollama', 'prompt_loader']:
    try:
        module = importlib.import_module(f'{__name__}.{sub}')
        # Assign module to this package's namespace
        setattr(sys.modules[__name__], sub, module)
        # Assign to 'core.<sub>' so "from core.logging import ..." works
        sys.modules[f'core.{sub}'] = module
    except Exception:
        pass
