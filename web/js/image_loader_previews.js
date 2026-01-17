/**
 * ImageLoaderWithPreviews - ComfyUI Node Extension
 * 
 * Provides a visual image selection interface with thumbnail grid previews.
 * Features:
 * - 4-column thumbnail grid that appears when node is scaled vertically
 * - Click thumbnails to select images and view them full-size on the node
 * - Navigation arrows (◀▶) for browsing through images in selected folder
 * - Sort options: name (asc/desc), creation date, modification date (newest/oldest first)
 * - Integrates with ComfyUI's folder_path and image dropdown widgets
 * - Auto-loads images from specified folder path with configurable sorting
 * - Click selected image to return to grid view
 * 
 * Backend API endpoints:
 * - POST /nhknodes/images: Get sorted image list from folder
 * - GET /nhknodes/view: Serve image files for preview thumbnails
 * 
 * Compatible with ComfyUI's LoadImage node pattern for seamless workflow integration.
 */

import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Local $el helper - avoids deprecated /scripts/ui.js import
function $el(tag, propsOrChildren, children) {
    const split = tag.split(".");
    const element = document.createElement(split.shift());
    if (split.length > 0) element.classList.add(...split);

    if (propsOrChildren) {
        if (Array.isArray(propsOrChildren)) {
            element.append(...propsOrChildren);
        } else {
            const { parent, ...props } = propsOrChildren;
            Object.assign(element, props);
            if (parent) parent.append(element);
        }
    }
    if (children) element.append(...children);
    return element;
}

const IMAGE_LOADER_NODE = "ImageLoaderWithPreviews";

let imagesByPath = {};

const loadImageList = async (folderPath, sortMethod = "newest_first") => {
    try {
        const response = await api.fetchApi("/nhknodes/images", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ folder_path: folderPath, sort_method: sortMethod })
        });
        const cacheKey = `${folderPath}_${sortMethod}`;
        imagesByPath[cacheKey] = await response.json();
        return imagesByPath[cacheKey];
    } catch (error) {
        console.error("Failed to load images:", error);
        return {};
    }
};

const createImageThumbnail = (filename, folderPath, onSelect) => {
    const thumbnail = $el("div.nhk-image-item", {
        onclick: () => onSelect(filename)
    }, [
        $el("img", {
            src: `/nhknodes/view?folder_path=${encodeURIComponent(folderPath)}&filename=${encodeURIComponent(filename)}`,
            loading: "lazy"
        })
    ]);
    
    return thumbnail;
};

app.registerExtension({
    name: "nhknodes.ImageLoaderWithPreviews",
    
    async beforeRegisterNodeDef(_nodeType, nodeData) {
        if (nodeData.name !== IMAGE_LOADER_NODE) {
            return;
        }

        // Add CSS styles
        $el("style", {
            textContent: `
                .nhk-image-grid {
                    display: none;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 0;
                    overflow: auto;
                    height: 100%;
                    max-height: 100%;
                    padding: 0;
                    background: #2a2a2a;
                    border: none;
                    margin: 0;
                    width: 100%;
                    flex: 1;
                    min-height: 0;
                    box-sizing: border-box;
                }
                
                .nhk-image-grid.expanded {
                    display: grid;
                }
                
                .nhk-image-item {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 0;
                    cursor: pointer;
                    transition: all 0.15s;
                    background: #333;
                    border: none;
                    aspect-ratio: 1;
                    box-sizing: border-box;
                }
                
                .nhk-image-item:hover {
                    background: #404040;
                }
                
                .nhk-image-item.selected {
                    background: #1e3a5f;
                }
                
                .nhk-image-item img {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                    background: #222;
                }
                
                .nhk-path-input {
                    width: 100%;
                    margin: 0;
                    padding: 0;
                    background: #333;
                    border: none;
                    color: #fff;
                    font-size: 12px;
                }
                
                .nhk-toggle-button {
                    margin: 0;
                    padding: 0;
                    background: #007acc;
                    border: none;
                    color: #fff;
                    cursor: pointer;
                    font-size: 11px;
                }
                
                .nhk-selected-image {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    padding: 0;
                    background: #333;
                    border: none;
                    width: 100%;
                    flex: 1;
                    box-sizing: border-box;
                    overflow: hidden;
                }
                
                .nhk-selected-image img {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }
                
                .nhk-toggle-button:hover {
                    background: #005a9e;
                }
            `,
            parent: document.head,
        });
    },

    async nodeCreated(node) {
        console.log("Node created - Class:", node.comfyClass, "Type:", node.type, "Title:", node.title);
        if (node.comfyClass !== IMAGE_LOADER_NODE && node.type !== IMAGE_LOADER_NODE) {
            return;
        }
        console.log("🖼️ Processing ImageLoaderWithPreviews node!");

        // Store state on the node itself for persistence across tab switches
        if (!node.nhkImageLoaderState) {
            node.nhkImageLoaderState = {
                isGridExpanded: true,
                selectedImageName: "",
                currentImageList: [],
                currentImageIndex: -1
            };
        }
        const state = node.nhkImageLoaderState;
        
        // Use state variables for backwards compatibility
        let isGridExpanded = state.isGridExpanded;
        let selectedImageName = state.selectedImageName;
        let currentImageList = state.currentImageList;
        let currentImageIndex = state.currentImageIndex;

        // Find the widgets
        const pathWidget = node.widgets?.find(w => w.name === "folder_path");
        const imageWidget = node.widgets?.find(w => w.name === "image");
        const sortWidget = node.widgets?.find(w => w.name === "sort_method");

        // Function to get current path from widget (always fresh)
        const getCurrentPath = () => pathWidget?.value || "/home/nhk/comfy/ComfyUI/output";
        let currentPath = getCurrentPath();
        
        // Listen for sort method changes
        if (sortWidget) {
            const originalCallback = sortWidget.callback;
            sortWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                // Reload images with new sort method
                if (isGridExpanded && imageGrid.children.length > 0) {
                    loadImages();
                }
            };
        }
        
        // Listen for image widget changes (dropdown selection)
        if (imageWidget) {
            const originalCallback = imageWidget.callback;
            imageWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                // Show selected image when chosen from dropdown
                if (value && currentImageList.includes(value)) {
                    showSelectedImage(value);
                }
            };
        }
        
        // Listen for folder path changes
        if (pathWidget) {
            const originalCallback = pathWidget.callback;
            pathWidget.callback = function(value) {
                if (originalCallback) originalCallback.call(this, value);
                // Update current path and always reload grid (even if not visible)
                currentPath = value;
                loadImages();
                // Clear selected image since we changed folders
                selectedImageName = "";
                state.selectedImageName = "";
                selectedImageDisplay.style.display = "none";
                navBar.style.display = "none";
                isGridExpanded = true;
                state.isGridExpanded = true;
                if (imageGrid.children.length > 0) {
                    imageGrid.style.display = "grid";
                }
            };
        }
        


        // Create image grid container
        const imageGrid = $el("div.nhk-image-grid");

        // Function to load and display images
        const loadImages = async () => {
            
            imageGrid.innerHTML = "Loading...";
            
            // Always get fresh path from widget
            currentPath = getCurrentPath();
            const sortMethod = sortWidget?.value || "newest_first";
            const images = await loadImageList(currentPath, sortMethod);
            const imageNames = Object.keys(images);
            
            // Update current image list and persist
            currentImageList = imageNames;
            state.currentImageList = imageNames;
            console.log('Updated image list:', imageNames.length, 'images');
            
            // Only restore widget value if it was explicitly selected before
            // DO NOT auto-select first image
            if (imageWidget) {
                const currentWidgetValue = imageWidget.value || "";
                if (currentWidgetValue && imageNames.includes(currentWidgetValue)) {
                    // Keep existing selection if it's valid
                    selectedImageName = currentWidgetValue;
                    console.log('✅ Keeping existing selection:', currentWidgetValue);
                } else if (imageNames.length === 0) {
                    // Clear widget if no images available
                    imageWidget.value = "";
                    selectedImageName = "";
                } else if (!currentWidgetValue) {
                    // Leave widget empty if nothing was selected before
                    console.log('🆆 No previous selection, leaving widget empty');
                    selectedImageName = "";
                }
            }
            
            // Clear grid
            imageGrid.innerHTML = "";
            
            if (imageNames.length === 0) {
                imageGrid.innerHTML = "No images found in this folder";
                navBar.style.display = "none";
                return;
            }

            // Create thumbnail for each image
            imageNames.forEach(filename => {
                const thumbnail = createImageThumbnail(filename, currentPath, (selectedFilename) => {
                    // Remove selection from other items
                    imageGrid.querySelectorAll('.nhk-image-item').forEach(item => {
                        item.classList.remove('selected');
                    });
                    
                    // Select this item
                    thumbnail.classList.add('selected');
                    
                    // IMMEDIATELY update the widget value for persistence
                    if (imageWidget) {
                        imageWidget.value = selectedFilename;
                        console.log('🔄 Updated widget value to:', selectedFilename);
                    }
                    
                    // Show the selected image on the node
                    showSelectedImage(selectedFilename);
                    
                    // Close the grid and persist state
                    isGridExpanded = false;
                    state.isGridExpanded = false;
                    imageGrid.style.display = "none";
                });
                
                imageGrid.appendChild(thumbnail);
            });
        };


        // Navigation bar that sits above the image display (below widgets)
        const navBar = $el("div", {
            style: {
                display: "none",
                gap: "6px",
                alignItems: "center",
                justifyContent: "center",
                padding: "4px 2px",
                background: "#262626",
                borderBottom: "1px solid #333",
                borderRadius: "3px",
                boxSizing: "border-box"
            }
        });

        const createNavButton = (label, onClick) => $el("button", {
            textContent: label,
            onclick: onClick,
            style: {
                padding: "4px 8px",
                background: "#3a3a3a",
                color: "#e5e5e5",
                border: "1px solid #444",
                borderRadius: "3px",
                cursor: "pointer",
                fontSize: "11px"
            },
            onmouseenter: (e) => e.currentTarget.style.background = "#4a4a4a",
            onmouseleave: (e) => e.currentTarget.style.background = "#3a3a3a",
        });

        const prevButton = createNavButton("◀ Previous", () => {
            if (currentImageIndex > 0) {
                showSelectedImage(currentImageList[currentImageIndex - 1]);
            }
        });

        const nextButton = createNavButton("Next ▶", () => {
            if (currentImageIndex < currentImageList.length - 1) {
                showSelectedImage(currentImageList[currentImageIndex + 1]);
            }
        });

        navBar.append(prevButton, nextButton);

        // Create selected image display (below nav bar)
        const selectedImageDisplay = $el("div.nhk-selected-image", {
            style: { display: "none", minHeight: "0", flex: "1" }
        });

        // Function to show selected image on node
        const showSelectedImage = async (filename) => {
            selectedImageName = filename;
            selectedImageName = filename;
            state.selectedImageName = filename;
            currentImageIndex = currentImageList.indexOf(filename);
            state.currentImageIndex = currentImageIndex;
            
            // Update the widget value for execution
            if (imageWidget) {
                imageWidget.value = filename;
            }
            if (pathWidget) {
                pathWidget.value = currentPath;
            }
            
            // Show the selected image with navigation
            selectedImageDisplay.innerHTML = "";
            if (filename) {
                // Create container for image
                const imageContainer = $el("div", {
                    style: {
                        width: "100%",
                        height: "100%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                    }
                });

                // Main image
                const img = $el("img", {
                    src: `/nhknodes/view?folder_path=${encodeURIComponent(currentPath)}&filename=${encodeURIComponent(filename)}`,
                    style: {
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        cursor: "pointer"
                    },
                    onclick: () => {
                // Close selected image and show grid
                selectedImageDisplay.style.display = "none";
                navBar.style.display = "none";
                isGridExpanded = true;
                state.isGridExpanded = true;
                if (imageGrid.children.length > 0) {
                    imageGrid.style.display = "grid";
                }
                    }
                });

                imageContainer.appendChild(img);
                selectedImageDisplay.appendChild(imageContainer);
                selectedImageDisplay.style.display = "flex";
                selectedImageDisplay.style.flex = "1";
                selectedImageDisplay.style.minHeight = "100px";

                // Update top nav bar visibility
                prevButton.disabled = currentImageIndex <= 0;
                nextButton.disabled = currentImageIndex >= currentImageList.length - 1;
                navBar.style.display = "flex";
            }
        };

        // Main container
        const container = $el("div", {
            style: { 
                width: "100%", 
                height: "100%",
                padding: "2px",
                background: "#1e1e1e",
                border: "1px solid #333",
                borderRadius: "4px",
                boxSizing: "border-box",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                minHeight: "0"
            }
        }, [
            navBar,
            selectedImageDisplay,
            imageGrid
        ]);

        // Add container to node
        const widget = node.addDOMWidget("image_selector", "div", container);
        // Keep the widget at a stable size; internal content manages its own layout
        widget.computeSize = (w) => {
            const width = Math.max(w || 400, 320);
            const height = 250;
            return [width, height];
        };

        // Monitor node size changes and reveal grid when scaled vertically
        const updateContainerHeight = () => {
            if (node.size && node.size[1] > 120) {
                const availableHeight = node.size[1] - 160; // leave headroom for header/widgets
                container.style.height = availableHeight + "px";

                if (availableHeight > 100 && isGridExpanded) {
                    imageGrid.style.display = "grid";
                    navBar.style.display = "none";
                } else if (availableHeight > 100 && !isGridExpanded && selectedImageName) {
                    selectedImageDisplay.style.display = "flex";
                    imageGrid.style.display = "none";
                    navBar.style.display = "flex";
                } else {
                    imageGrid.style.display = "none";
                    selectedImageDisplay.style.display = "none";
                    navBar.style.display = "none";
                }
            } else {
                container.style.height = "50px";
                imageGrid.style.display = "none";
                selectedImageDisplay.style.display = "none";
                navBar.style.display = "none";
            }
        };

        container.style.width = "100%";
        updateContainerHeight();

        // Use the image widget value as source of truth (it persists automatically)
        const currentImageValue = imageWidget?.value || "";
        console.log('🔧 Node initialization - Image widget value:', currentImageValue);
        
        // ALWAYS start with grid view - let user choose
        selectedImageName = currentImageValue;
        isGridExpanded = true;
        console.log('📋 Starting with grid view');
        
        // Load images on startup - delay to allow widget values to load from saved workflows
        setTimeout(() => {
            loadImages().then(() => {
                const widgetImageValue = imageWidget?.value || "";
                if (widgetImageValue && widgetImageValue.trim() && currentImageList.includes(widgetImageValue)) {
                    showSelectedImage(widgetImageValue);
                    setTimeout(() => {
                        isGridExpanded = false;
                        imageGrid.style.display = "none";
                        selectedImageDisplay.style.display = "flex";
                    }, 100);
                } else {
                    isGridExpanded = true;
                    imageGrid.style.display = "grid";
                    selectedImageDisplay.style.display = "none";
                }
            });
        }, 100);

        // Periodically sync height to node size in case ComfyUI doesn't emit resize events
        setInterval(updateContainerHeight, 250);
        node.onResize = updateContainerHeight;
    }
});
