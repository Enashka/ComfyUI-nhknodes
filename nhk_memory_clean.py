"""nhk Memory Clean - three routes that actually free memory.

ComfyUI's own unload path moves weights VRAM -> RAM without freeing them, never
evicts pinned host pages while idle, and never calls malloc_trim. These routes
close those gaps. See docs/superpowers/specs/2026-07-20-nhk-memory-clean-design.md
in /home/nhk/comfy for the full rationale.
"""

import asyncio
import gc
import importlib.util
import os

import psutil
import torch
from aiohttp import web
from server import PromptServer

import comfy.model_management
import comfy.memory_management

_HERE = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location(
    "nhk_memory_clean_core", os.path.join(_HERE, "nhk_memory_clean_core.py")
)
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

# Larger than any real RAM figure, so ram_release's early-return never triggers
# and free_pins never runs out of budget.
SENTINEL = 1 << 60

_capture = core.CacheCapture()
_capture.install(comfy.memory_management)

_lock = asyncio.Lock()


def _ram_available():
    return psutil.virtual_memory().available


def _vram_free():
    if not torch.cuda.is_available():
        return None
    return torch.cuda.mem_get_info()[0]


def _snapshot():
    return core.snapshot(_ram_available, _vram_free)


def _is_executing():
    return bool(PromptServer.instance.prompt_queue.currently_running)


def _relay(unload_models, free_memory):
    """Set ComfyUI's /free flags and wait for the worker thread to consume them.

    set_flag notifies the queue condition variable, so the worker wakes at once
    rather than waiting out its 1000s timeout.
    """
    queue = PromptServer.instance.prompt_queue
    queue.set_flag("unload_models", unload_models)
    queue.set_flag("free_memory", free_memory)
    consumed = core.wait_for_flags_consumed(
        queue.get_flags, ["unload_models", "free_memory"], timeout_s=10.0
    )
    return {"consumed": consumed}


def _free_pins():
    return comfy.model_management.free_pins(SENTINEL, evict_active=True)


def _release_node_outputs():
    """Drop cached node outputs without unloading models.

    Falls back to the /free relay when the capture is unavailable - a different
    cache type (--cache-lru, --cache-none), no prompt run yet this session, or an
    upstream change to the callback contract. Never silently under-cleans.
    """
    cache = _capture.get()
    if cache is not None and hasattr(cache, "ram_release"):
        freed = cache.ram_release(SENTINEL, free_active=True)
        return {"path": "direct", "freed": freed}
    # unload_models=False is honoured: main.py reads
    # flags.get("unload_models", free_memory), so an explicit False wins.
    return {"path": "fallback", **_relay(False, True)}


def _reset_peak_stats():
    if not torch.cuda.is_available():
        return None
    torch.cuda.reset_peak_memory_stats()
    return True


TIERS = {
    "vram": lambda: [
        ("unload_all_models", comfy.model_management.unload_all_models),
        ("soft_empty_cache", comfy.model_management.soft_empty_cache),
        ("reset_peak_stats", _reset_peak_stats),
    ],
    "ram": lambda: [
        ("release_node_outputs", _release_node_outputs),
        ("free_pins", _free_pins),
        ("gc_collect", gc.collect),
        ("malloc_trim", core.trim_malloc),
    ],
    "all": lambda: [
        ("free_relay", lambda: _relay(True, True)),
        ("free_pins", _free_pins),
        ("gc_collect", gc.collect),
        ("soft_empty_cache", comfy.model_management.soft_empty_cache),
        ("malloc_trim", core.trim_malloc),
    ],
}


async def _clean(tier):
    if _is_executing():
        return web.json_response(
            {"error": "cannot clean during execution"}, status=409
        )

    async with _lock:
        before = _snapshot()
        steps = await asyncio.get_running_loop().run_in_executor(
            None, core.run_steps, TIERS[tier]()
        )
        after = _snapshot()

    return web.json_response({
        "tier": tier,
        "before": before,
        "after": after,
        "ram_freed": after["ram_available"] - before["ram_available"],
        "vram_freed": (
            None if after["vram_free"] is None
            else after["vram_free"] - before["vram_free"]
        ),
        "steps": steps,
    })


@PromptServer.instance.routes.post("/nhknodes/clean/vram")
async def clean_vram(request):
    return await _clean("vram")


@PromptServer.instance.routes.post("/nhknodes/clean/ram")
async def clean_ram(request):
    return await _clean("ram")


@PromptServer.instance.routes.post("/nhknodes/clean/all")
async def clean_all(request):
    return await _clean("all")


print("nhk Memory Clean: routes registered (/nhknodes/clean/{vram,ram,all})")
