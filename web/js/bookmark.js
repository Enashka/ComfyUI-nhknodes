import { app } from "../../../scripts/app.js";

/**
 * Bookmark node for nhknodes
 * Place anywhere on canvas to navigate via keyboard shortcut
 * Configurable anchor position (lower-left or lower-right)
 */

class BookmarkNode {
	constructor() {
		this.shortcuts = new Map();
		this.handleKeydown = this.handleKeydown.bind(this);
		document.addEventListener("keydown", this.handleKeydown);
	}

	registerShortcut(node, shortcut) {
		if (shortcut && shortcut.trim()) {
			this.shortcuts.set(shortcut.toLowerCase(), node);
		}
	}

	unregisterShortcut(shortcut) {
		if (shortcut) {
			this.shortcuts.delete(shortcut.toLowerCase());
		}
	}

	handleKeydown(e) {
		// Ignore if typing in input/textarea
		const target = e.target;
		if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
			return;
		}

		// Build the key combination string
		const keys = [];
		if (e.ctrlKey) keys.push("ctrl");
		if (e.altKey) keys.push("alt");
		if (e.shiftKey) keys.push("shift");
		keys.push(e.key.toLowerCase());
		const combo = keys.join("+");

		// Check if this matches any bookmark
		const node = this.shortcuts.get(combo);
		if (node && node.graph === app.graph) {
			this.navigateToBookmark(node);
			e.preventDefault();
			e.stopPropagation();
		}
	}

	navigateToBookmark(node) {
		const canvas = app.canvas;
		if (!canvas || !canvas.ds) return;

		const zoom = node.widgets?.find(w => w.name === "zoom")?.value || 1;
		const anchor = node.widgets?.find(w => w.name === "anchor")?.value || "upper-left";

		// Calculate offset based on anchor position
		// Offset is in canvas coordinate space
		// The transform is: screen_pos = (canvas_pos + offset) * scale
		let offsetX, offsetY;

		if (anchor === "upper-right") {
			// Position node at upper-right of viewport
			// viewport_width_in_canvas_units = canvas.canvas.width / canvas.ds.scale
			// We want: (node.pos[0] + offset) * zoom = viewport_width - node_width - 16
			// So: offset = viewport_width/zoom - node.pos[0] - node.size[0]/zoom - 16/zoom
			const currentScale = canvas.ds.scale;
			const viewportWidthInCanvasUnits = canvas.canvas.width / currentScale;
			offsetX = -node.pos[0] + viewportWidthInCanvasUnits - node.size[0] - 16;
			offsetY = -node.pos[1] + 40;
		} else {
			// Position node at upper-left of viewport (original rgthree behavior)
			offsetX = -node.pos[0] + 16;
			offsetY = -node.pos[1] + 40;
		}

		canvas.ds.offset[0] = offsetX;
		canvas.ds.offset[1] = offsetY;
		canvas.ds.scale = zoom;
		canvas.setDirty(true, true);
	}
}

const bookmarkService = new BookmarkNode();

app.registerExtension({
	name: "nhknodes.Bookmark",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "Bookmark") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				onNodeCreated?.apply(this, arguments);

				// Store old shortcut for cleanup
				this._oldShortcut = "";

				// Register shortcut when it changes
				const shortcutWidget = this.widgets?.find(w => w.name === "shortcut_key");
				if (shortcutWidget) {
					const originalCallback = shortcutWidget.callback;
					shortcutWidget.callback = (value) => {
						if (this._oldShortcut) {
							bookmarkService.unregisterShortcut(this._oldShortcut);
						}
						this._oldShortcut = value;
						bookmarkService.registerShortcut(this, value);
						originalCallback?.call(shortcutWidget, value);
					};

					// Register initial shortcut
					if (shortcutWidget.value) {
						this._oldShortcut = shortcutWidget.value;
						bookmarkService.registerShortcut(this, shortcutWidget.value);
					}
				}

				// Set node title
				this.title = "🔖";

				// Make it smaller
				this.size = [200, 80];
			};

			const onRemoved = nodeType.prototype.onRemoved;
			nodeType.prototype.onRemoved = function () {
				if (this._oldShortcut) {
					bookmarkService.unregisterShortcut(this._oldShortcut);
				}
				onRemoved?.apply(this, arguments);
			};

			// Handle double-click to navigate
			const onDblClick = nodeType.prototype.onDblClick;
			nodeType.prototype.onDblClick = function (e) {
				bookmarkService.navigateToBookmark(this);
				return true;
			};
		}
	},
});
