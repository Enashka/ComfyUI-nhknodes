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
