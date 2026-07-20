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
