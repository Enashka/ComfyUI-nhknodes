import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(os.path.dirname(_HERE), "nhk_memory_clean_core.py")

_spec = importlib.util.spec_from_file_location("nhk_memory_clean_core", _CORE)
core = importlib.util.module_from_spec(_spec)
sys.modules["nhk_memory_clean_core"] = core
_spec.loader.exec_module(core)


def test_snapshot_reads_both_sources():
    snap = core.snapshot(lambda: 100, lambda: 200)
    assert snap == {"ram_available": 100, "vram_free": 200}


def test_snapshot_allows_missing_vram():
    snap = core.snapshot(lambda: 100, lambda: None)
    assert snap["vram_free"] is None
    assert snap["ram_available"] == 100
