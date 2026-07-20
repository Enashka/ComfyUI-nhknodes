import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const TIERS = [
    { id: "vram", label: "VRAM", title: "Unload models, empty CUDA cache. RAM cache stays warm." },
    { id: "ram", label: "RAM", title: "Drop node outputs, evict pinned pages, trim arenas. Models stay on GPU." },
    { id: "all", label: "ALL", title: "Full clean: models, node cache, pins, arenas." },
];

const POS_KEY = "nhk.memoryClean.pos";
const COLLAPSED_KEY = "nhk.memoryClean.collapsed";

// Default sits clear of ComfyUI's bottom-right control cluster.
const DEFAULT_POS = { left: null, top: 90, right: 12 };

const fmt = (bytes) => {
    if (bytes === null || bytes === undefined) return "n/a";
    const gb = bytes / (1024 ** 3);
    return `${gb >= 0 ? "+" : ""}${gb.toFixed(2)} GB`;
};

const readJSON = (key, fallback) => {
    try {
        const raw = localStorage.getItem(key);
        return raw === null ? fallback : JSON.parse(raw);
    } catch {
        return fallback;
    }
};

const writeJSON = (key, value) => {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch {
        /* private mode / quota - position just won't persist */
    }
};

app.registerExtension({
    name: "nhk.MemoryClean",
    setup() {
        let collapsed = readJSON(COLLAPSED_KEY, true);

        const panel = document.createElement("div");
        panel.style.cssText = [
            "position:fixed", "z-index:1000",
            "display:flex", "gap:6px", "align-items:center",
            "padding:4px 6px", "border-radius:6px",
            "background:rgba(20,20,20,0.9)", "border:1px solid #444",
            "font-family:sans-serif", "font-size:11px", "color:#ddd",
            "box-shadow:0 2px 8px rgba(0,0,0,0.4)",
            "user-select:none",
        ].join(";");

        // --- position, clamped so the panel can never be dragged off-screen ---
        const applyPos = (pos) => {
            if (pos.left !== null && pos.left !== undefined) {
                const maxLeft = Math.max(0, window.innerWidth - panel.offsetWidth - 4);
                panel.style.left = `${Math.min(Math.max(0, pos.left), maxLeft)}px`;
                panel.style.right = "auto";
            } else {
                panel.style.left = "auto";
                panel.style.right = `${pos.right ?? 12}px`;
            }
            const maxTop = Math.max(0, window.innerHeight - panel.offsetHeight - 4);
            panel.style.top = `${Math.min(Math.max(0, pos.top ?? 90), maxTop)}px`;
        };

        let pos = readJSON(POS_KEY, DEFAULT_POS);

        // --- drag handle doubles as the collapse toggle ---
        const handle = document.createElement("span");
        handle.textContent = "clean";
        handle.title = "Drag to move · click to expand/collapse";
        handle.style.cssText = "cursor:grab;opacity:0.65;padding:2px 2px";

        const body = document.createElement("span");
        body.style.cssText = "display:flex;gap:6px;align-items:center";

        const status = document.createElement("span");
        status.style.cssText = "min-width:150px;opacity:0.8";

        const render = () => {
            body.style.display = collapsed ? "none" : "flex";
            handle.style.opacity = collapsed ? "0.5" : "0.65";
            applyPos(pos);
        };

        // A click and a drag both start with pointerdown, so distinguish them by
        // distance travelled - pointer jitter must not swallow the collapse toggle.
        const DRAG_THRESHOLD_PX = 4;

        let dragging = false;
        let moved = false;
        let startX = 0;
        let startY = 0;
        let offsetX = 0;
        let offsetY = 0;

        handle.addEventListener("pointerdown", (e) => {
            dragging = true;
            moved = false;
            startX = e.clientX;
            startY = e.clientY;
            const rect = panel.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            handle.setPointerCapture(e.pointerId);
        });

        handle.addEventListener("pointermove", (e) => {
            if (!dragging) return;
            if (!moved) {
                const dist = Math.hypot(e.clientX - startX, e.clientY - startY);
                if (dist < DRAG_THRESHOLD_PX) return;
                moved = true;
                handle.style.cursor = "grabbing";
            }
            pos = { left: e.clientX - offsetX, top: e.clientY - offsetY, right: null };
            applyPos(pos);
        });

        handle.addEventListener("pointerup", (e) => {
            if (!dragging) return;
            dragging = false;
            handle.releasePointerCapture(e.pointerId);
            handle.style.cursor = "grab";
            if (moved) {
                writeJSON(POS_KEY, pos);
            } else {
                // A click without movement toggles collapse.
                collapsed = !collapsed;
                writeJSON(COLLAPSED_KEY, collapsed);
                status.textContent = "";
                render();
            }
        });

        for (const tier of TIERS) {
            const btn = document.createElement("button");
            btn.textContent = tier.label;
            btn.title = tier.title;
            btn.style.cssText = [
                "cursor:pointer", "padding:3px 8px", "border-radius:4px",
                "border:1px solid #555", "background:#2a2a2a", "color:#ddd",
                "font-size:11px",
            ].join(";");

            btn.addEventListener("click", async () => {
                const original = btn.textContent;
                btn.disabled = true;
                btn.textContent = "...";
                status.textContent = "";
                try {
                    const res = await api.fetchApi(`/nhknodes/clean/${tier.id}`, {
                        method: "POST",
                    });
                    if (!res.ok) {
                        const errBody = await res.json().catch(() => ({}));
                        status.textContent = errBody.error || `error ${res.status}`;
                        return;
                    }
                    const data = await res.json();
                    const failed = (data.steps || []).filter((s) => !s.ok);
                    const paths = (data.steps || [])
                        .map((s) => s.result && s.result.path)
                        .filter(Boolean);
                    // rss_freed is what ComfyUI actually gave back; ram_freed is
                    // system-wide and drifts with other processes.
                    status.textContent =
                        `RSS ${fmt(data.rss_freed)} · VRAM ${fmt(data.vram_freed)}` +
                        (paths.length ? ` · ${paths.join(",")}` : "") +
                        (failed.length ? ` · ${failed.length} step(s) failed` : "");
                    status.title =
                        `process RSS freed: ${fmt(data.rss_freed)}\n` +
                        `system RAM available delta: ${fmt(data.ram_freed)}\n` +
                        `VRAM freed: ${fmt(data.vram_freed)}`;
                    if (failed.length) {
                        console.warn("[nhk] memory clean step failures", failed);
                    }
                } catch (err) {
                    status.textContent = "request failed";
                    console.error("[nhk] memory clean", err);
                } finally {
                    btn.disabled = false;
                    btn.textContent = original;
                }
            });

            body.appendChild(btn);
        }

        body.appendChild(status);
        panel.appendChild(handle);
        panel.appendChild(body);
        document.body.appendChild(panel);

        render();
        window.addEventListener("resize", () => applyPos(pos));
    },
});
