"""nhk Memory Clean - core logic.

Pure helpers with no ComfyUI or torch imports, so they can be unit-tested with a
plain Python interpreter. nhk_memory_clean.py supplies the live ComfyUI callables.
"""

import weakref


def snapshot(ram_available_fn, vram_free_fn):
    """Capture free RAM and VRAM in bytes.

    Both arguments are zero-arg callables. vram_free_fn may return None when CUDA
    is unavailable.
    """
    return {
        "ram_available": ram_available_fn(),
        "vram_free": vram_free_fn(),
    }


def trim_malloc(loader=None):
    """Ask glibc to return free arena pages to the OS.

    Returns True if pages were released, False if there was nothing to release,
    and None when malloc_trim is unavailable (non-glibc platform). The None case
    is distinct on purpose: it means the step was skipped, not that it did nothing.
    """
    if loader is None:
        def loader():
            import ctypes

            return ctypes.CDLL("libc.so.6")

    try:
        libc = loader()
        return bool(libc.malloc_trim(0))
    except (OSError, AttributeError):
        return None


def run_steps(steps):
    """Run (name, callable) pairs in order, guarding each one.

    A step that raises is recorded and the remaining steps still run.
    """
    results = []
    for name, fn in steps:
        try:
            results.append({"step": name, "ok": True, "result": fn()})
        except Exception as exc:
            results.append({
                "step": name,
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            })
    return results


def wait_for_flags_consumed(get_flags, keys, timeout_s=5.0, poll_s=0.02,
                            sleep_fn=None, now_fn=None):
    """Block until none of `keys` remain pending, or the timeout expires.

    get_flags is called as get_flags(reset=False) and must return a dict copy.
    Returns True if the flags were consumed, False on timeout.
    """
    import time

    sleep_fn = sleep_fn or time.sleep
    now_fn = now_fn or time.monotonic
    deadline = now_fn() + timeout_s

    while True:
        pending = get_flags(reset=False)
        if not any(key in pending for key in keys):
            return True
        if now_fn() >= deadline:
            return False
        sleep_fn(poll_s)


class CacheCapture:
    """Capture the live node-output cache by wrapping set_ram_cache_release_state.

    ComfyUI hands the release callback a bound method of the RAMPressureCache, then
    unregisters it in a finally block once the prompt ends. Wrapping the setter is
    the only way to keep a handle on that cache while idle.

    The handle is a weakref on purpose: a strong reference would keep a stale
    CacheSet alive after /free rebuilds it.
    """

    def __init__(self):
        self._ref = None
        self.installed_over = None

    def install(self, memory_management_module):
        """Wrap the module's setter. Safe to call repeatedly."""
        original = memory_management_module.set_ram_cache_release_state
        if getattr(original, "_nhk_capture", None) is self:
            return

        def wrapped(callback, headroom):
            if callback is not None:
                owner = getattr(callback, "__self__", None)
                if owner is not None:
                    self._ref = weakref.ref(owner)
            return original(callback, headroom)

        wrapped._nhk_capture = self
        self.installed_over = original
        memory_management_module.set_ram_cache_release_state = wrapped

    def get(self):
        """Return the captured cache, or None if unavailable or collected."""
        if self._ref is None:
            return None
        return self._ref()
