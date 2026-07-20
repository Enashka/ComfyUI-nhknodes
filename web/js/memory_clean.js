import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const TIERS = [
    { id: "vram", label: "VRAM", title: "Unload models, empty CUDA cache. RAM cache stays warm." },
    { id: "ram", label: "RAM", title: "Drop node outputs, evict pinned pages, trim arenas. Models stay on GPU." },
    { id: "all", label: "ALL", title: "Full clean: models, node cache, pins, arenas." },
];

const fmt = (bytes) => {
    if (bytes === null || bytes === undefined) return "n/a";
    const gb = bytes / (1024 ** 3);
    return `${gb >= 0 ? "+" : ""}${gb.toFixed(2)} GB`;
};

app.registerExtension({
    name: "nhk.MemoryClean",
    setup() {
        const panel = document.createElement("div");
        panel.style.cssText = [
            "position:fixed", "bottom:12px", "right:12px", "z-index:1000",
            "display:flex", "gap:6px", "align-items:center",
            "padding:6px 8px", "border-radius:6px",
            "background:rgba(20,20,20,0.85)", "border:1px solid #444",
            "font-family:sans-serif", "font-size:11px", "color:#ddd",
        ].join(";");

        const label = document.createElement("span");
        label.textContent = "clean";
        label.style.opacity = "0.6";
        panel.appendChild(label);

        const status = document.createElement("span");
        status.style.cssText = "min-width:150px;opacity:0.8";
        status.textContent = "";

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
                        const body = await res.json().catch(() => ({}));
                        status.textContent = body.error || `error ${res.status}`;
                        return;
                    }
                    const data = await res.json();
                    const failed = (data.steps || []).filter((s) => !s.ok);
                    const paths = (data.steps || [])
                        .map((s) => s.result && s.result.path)
                        .filter(Boolean);
                    status.textContent =
                        `RAM ${fmt(data.ram_freed)} · VRAM ${fmt(data.vram_freed)}` +
                        (paths.length ? ` · ${paths.join(",")}` : "") +
                        (failed.length ? ` · ${failed.length} step(s) failed` : "");
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

            panel.appendChild(btn);
        }

        panel.appendChild(status);
        document.body.appendChild(panel);
    },
});
