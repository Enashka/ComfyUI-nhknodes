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
import { $el } from "../../../scripts/ui.js";
import { api } from "../../../scripts/api.js";

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
                    padding: 0;
                    background: #2a2a2a;
                    border: none;
                    margin: 0;
                    width: 100%;
                    flex: 1;
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


        // Create selected image display
        const selectedImageDisplay = $el("div.nhk-selected-image", {
            style: { display: "none" }
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
                // Create container for image and arrows
                const imageContainer = $el("div", {
                    style: {
                        position: "relative",
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
                        isGridExpanded = true;
                        state.isGridExpanded = true;
                        if (imageGrid.children.length > 0) {
                            imageGrid.style.display = "grid";
                        }
                    }
                });

                // Left arrow (previous)
                const leftArrow = $el("div", {
                    textContent: "◀",
                    style: {
                        position: "absolute",
                        left: "2px",
                        top: "2px",
                        backgroundColor: "rgba(0,0,0,0.5)",
                        color: "#ccc",
                        padding: "2px 4px",
                        borderRadius: "2px",
                        cursor: "pointer",
                        fontSize: "10px",
                        userSelect: "none",
                        display: currentImageIndex > 0 ? "block" : "none",
                        zIndex: "10"
                    },
                    onclick: (e) => {
                        e.stopPropagation();
                        if (currentImageIndex > 0) {
                            showSelectedImage(currentImageList[currentImageIndex - 1]);
                        }
                    }
                });

                // Right arrow (next)
                const rightArrow = $el("div", {
                    textContent: "▶",
                    style: {
                        position: "absolute",
                        right: "2px",
                        top: "2px",
                        backgroundColor: "rgba(0,0,0,0.5)",
                        color: "#ccc",
                        padding: "2px 4px",
                        borderRadius: "2px",
                        cursor: "pointer",
                        fontSize: "10px",
                        userSelect: "none",
                        display: currentImageIndex < currentImageList.length - 1 ? "block" : "none",
                        zIndex: "10"
                    },
                    onclick: (e) => {
                        e.stopPropagation();
                        if (currentImageIndex < currentImageList.length - 1) {
                            showSelectedImage(currentImageList[currentImageIndex + 1]);
                        }
                    }
                });

                imageContainer.appendChild(img);
                imageContainer.appendChild(leftArrow);
                imageContainer.appendChild(rightArrow);
                selectedImageDisplay.appendChild(imageContainer);
                selectedImageDisplay.style.display = "flex";
                selectedImageDisplay.style.flex = "1";
                selectedImageDisplay.style.minHeight = "100px";
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
                flexDirection: "column"
            }
        }, [
            selectedImageDisplay,
            imageGrid
        ]);

        // Add container to node
        const widget = node.addDOMWidget("image_selector", "div", container);
        widget.computeSize = () => {
            return [400, 250];
        };

        // Monitor node size changes and reveal grid when scaled vertically
        const updateContainerHeight = () => {
            if (node.size && node.size[1] > 120) {
                const availableHeight = node.size[1] - 160;
                container.style.height = availableHeight + "px";
                // Show grid when node is scaled tall enough AND user wants grid visible
                if (availableHeight > 100 && isGridExpanded) {
                    imageGrid.style.display = "grid";
                } else if (availableHeight > 100 && !isGridExpanded && selectedImageName) {
                    // Show selected image if we have one and grid is not expanded
                    selectedImageDisplay.style.display = "flex";
                    imageGrid.style.display = "none";
                } else {
                    imageGrid.style.display = "none";
                    selectedImageDisplay.style.display = "none";
                }
            } else {
                container.style.height = "50px";
                imageGrid.style.display = "none";
                selectedImageDisplay.style.display = "none";
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
            // loadImages() will automatically get fresh path from getCurrentPath()
            loadImages().then(() => {
                // Restore selected image state if we have one
                // Only restore to selected image view if user explicitly selected something
                const widgetImageValue = imageWidget?.value || "";
                if (widgetImageValue && widgetImageValue.trim() && currentImageList.includes(widgetImageValue)) {
                    console.log('✅ User had selected:', widgetImageValue, '- restoring selected image view');
                    
                    // Show the selected image immediately
                    showSelectedImage(widgetImageValue);
                    
                    // Switch to selected image view after a brief delay
                    setTimeout(() => {
                        isGridExpanded = false;
                        imageGrid.style.display = "none";
                        selectedImageDisplay.style.display = "flex";
                        console.log('🖼️ Showing selected image view');
                    }, 100);
                } else {
                    console.log('📋 No explicit selection found - staying in grid view');
                    isGridExpanded = true;
                    // Make sure grid is visible
                    imageGrid.style.display = "grid";
                    selectedImageDisplay.style.display = "none";
                }
            });
        }, 100);

        // Monitor for size changes
        setInterval(updateContainerHeight, 100);
    }
});