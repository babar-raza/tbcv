# tbcv package bootstrap (single-level)
# Ensures imports like `from api.server import app` work without PYTHONPATH hacks.
import sys, importlib, importlib.util, importlib.abc
from pathlib import Path

# Ensure this package directory itself is on sys.path so subpackages (api, agents, core, ...) resolve.
_pkg_dir = Path(__file__).resolve().parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

class _AliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    _legacy = {'rule_manager': 'core.rule_manager', 'ollama_validator': 'core.ollama',
               'tbcv.rule_manager': 'core.rule_manager', 'tbcv.ollama_validator': 'core.ollama'}
    def _map(self, fullname: str):
        if fullname.startswith('tbcv.'):
            return fullname.split('.', 1)[1]
        return self._legacy.get(fullname)
    def find_spec(self, fullname, path=None, target=None):
        real = self._map(fullname)
        if not real:
            return None
        spec_real = importlib.util.find_spec(real)
        if spec_real is None:
            return None
        is_pkg = spec_real.submodule_search_locations is not None
        spec = importlib.util.spec_from_loader(fullname, self, is_package=is_pkg)
        spec._alias_to = real
        return spec
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        real = module.__spec__._alias_to
        real_mod = importlib.import_module(real)
        sys.modules[module.__spec__.name] = real_mod

# Install alias finder once
if not any(getattr(x, '__class__', None).__name__ == '_AliasFinder' for x in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())

# Convenience: allow `from tbcv import api` fallback
def __getattr__(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        raise AttributeError(name) from e
