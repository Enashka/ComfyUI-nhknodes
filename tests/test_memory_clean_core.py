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


class _FakeLibc:
    def __init__(self, retval):
        self.retval = retval
        self.calls = []

    def malloc_trim(self, arg):
        self.calls.append(arg)
        return self.retval


def test_trim_malloc_true_when_memory_released():
    libc = _FakeLibc(1)
    assert core.trim_malloc(lambda: libc) is True
    assert libc.calls == [0]


def test_trim_malloc_false_when_nothing_released():
    assert core.trim_malloc(lambda: _FakeLibc(0)) is False


def test_trim_malloc_none_when_not_glibc():
    def loader():
        raise OSError("no libc here")

    assert core.trim_malloc(loader) is None


def test_run_steps_runs_in_order():
    calls = []
    core.run_steps([
        ("a", lambda: calls.append("a")),
        ("b", lambda: calls.append("b")),
    ])
    assert calls == ["a", "b"]


def test_run_steps_records_result():
    assert core.run_steps([("a", lambda: 42)]) == [
        {"step": "a", "ok": True, "result": 42}
    ]


def test_run_steps_continues_after_failure():
    calls = []

    def boom():
        raise ValueError("nope")

    results = core.run_steps([("a", boom), ("b", lambda: calls.append("b"))])

    assert results[0]["ok"] is False
    assert "ValueError: nope" in results[0]["error"]
    assert results[1]["ok"] is True
    assert calls == ["b"]
