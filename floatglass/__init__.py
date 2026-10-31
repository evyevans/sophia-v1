"""Compatibility imports for the former Floatglass package name."""
import importlib
import sys
from sophia import __version__

for _name in ('contracts', 'core', 'demo', 'lenses', 'live', 'report'):
    _module = importlib.import_module(f'sophia.{_name}')
    sys.modules[f'{__name__}.{_name}'] = _module
    globals()[_name] = _module
