"""nhk Memory Clean - core logic.

Pure helpers with no ComfyUI or torch imports, so they can be unit-tested with a
plain Python interpreter. nhk_memory_clean.py supplies the live ComfyUI callables.
"""


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
