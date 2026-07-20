import gc as _gc
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(os.path.dirname(_HERE), "nhk_memory_clean_core.py")

_spec = importlib.util.spec_from_file_location("nhk_memory_clean_core", _CORE)
core = importlib.util.module_from_spec(_spec)
sys.modules["nhk_memory_clean_core"] = core
_spec.loader.exec_module(core)


def test_snapshot_reads_all_sources():
    snap = core.snapshot(lambda: 100, lambda: 200, lambda: 300)
    assert snap == {"ram_available": 100, "vram_free": 200, "rss": 300}


def test_snapshot_allows_missing_vram():
    snap = core.snapshot(lambda: 100, lambda: None, lambda: 300)
    assert snap["vram_free"] is None
    assert snap["ram_available"] == 100
    assert snap["rss"] == 300


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


class _FakeClock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


def test_wait_returns_true_when_already_consumed():
    clock = _FakeClock()
    ok = core.wait_for_flags_consumed(
        lambda reset: {}, ["free_memory"],
        timeout_s=1.0, poll_s=0.01, sleep_fn=clock.sleep, now_fn=clock.now,
    )
    assert ok is True


def test_wait_polls_until_flag_clears():
    clock = _FakeClock()
    state = {"polls": 0}

    def get_flags(reset):
        state["polls"] += 1
        return {"free_memory": True} if state["polls"] < 3 else {}

    ok = core.wait_for_flags_consumed(
        lambda reset=False: get_flags(reset), ["free_memory"],
        timeout_s=1.0, poll_s=0.01, sleep_fn=clock.sleep, now_fn=clock.now,
    )
    assert ok is True
    assert state["polls"] == 3


def test_wait_returns_false_on_timeout():
    clock = _FakeClock()
    ok = core.wait_for_flags_consumed(
        lambda reset: {"free_memory": True}, ["free_memory"],
        timeout_s=0.05, poll_s=0.01, sleep_fn=clock.sleep, now_fn=clock.now,
    )
    assert ok is False


class _FakeModule:
    def __init__(self):
        self.received = []

        def set_ram_cache_release_state(callback, headroom):
            self.received.append((callback, headroom))

        self.set_ram_cache_release_state = set_ram_cache_release_state


class _FakeCache:
    def ram_release(self, target, free_active=False):
        return 0


def test_capture_stores_callback_owner():
    module = _FakeModule()
    capture = core.CacheCapture()
    capture.install(module)

    cache = _FakeCache()
    module.set_ram_cache_release_state(cache.ram_release, 123)

    assert capture.get() is cache


def test_capture_delegates_to_original():
    module = _FakeModule()
    original = module.set_ram_cache_release_state
    capture = core.CacheCapture()
    capture.install(module)

    cache = _FakeCache()
    module.set_ram_cache_release_state(cache.ram_release, 123)

    assert module.set_ram_cache_release_state is not original
    assert capture.installed_over is original
    assert module.received == [(cache.ram_release, 123)]


def test_capture_ignores_none_callback():
    module = _FakeModule()
    capture = core.CacheCapture()
    capture.install(module)

    cache = _FakeCache()
    module.set_ram_cache_release_state(cache.ram_release, 123)
    module.set_ram_cache_release_state(None, 0)

    assert capture.get() is cache


def test_capture_holds_only_a_weak_reference():
    module = _FakeModule()
    capture = core.CacheCapture()
    capture.install(module)

    cache = _FakeCache()
    module.set_ram_cache_release_state(cache.ram_release, 123)
    module.received.clear()
    del cache
    _gc.collect()

    assert capture.get() is None


def test_capture_install_is_idempotent():
    module = _FakeModule()
    capture = core.CacheCapture()
    capture.install(module)
    wrapped_once = module.set_ram_cache_release_state
    capture.install(module)

    assert module.set_ram_cache_release_state is wrapped_once
