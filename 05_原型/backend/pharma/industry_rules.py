"""Explicit trusted code registry; uploaded packs cannot choose executable paths."""
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from .config import APP


@lru_cache(maxsize=1)
def pharmaceutical_rules():
    # This fixed entry is reviewed source. New code strategies require a code
    # change/review and controlled process restart, never eval or network install.
    path = APP / 'industry_packs/pharmaceutical/narrative_rules.py'
    spec = spec_from_file_location('pharma._trusted_pharmaceutical_rules',path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.append_findings
