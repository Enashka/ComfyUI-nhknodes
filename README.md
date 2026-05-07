# NHK Nodes for ComfyUI

A comprehensive collection of utility nodes for ComfyUI workflows. Organized into logical categories for better workflow management.

## 🌟 Featured Node

### 🖼️ Image Loader With Previews
The standout feature of this collection - an advanced image loader that hopefully simplifies how you browse and select images in ComfyUI.

<p align="center">
  <img src="./images/loader_1.png" width="45%" />
  <img src="./images/loader_2.png" width="45%" />
</p>

- **Browse from any folder** on your system
- **Live image previews** - see images before selecting
- **Multiple sorting options**: name, date modified, created


## 📦 Installation

### Via ComfyUI Manager (Recommended)
1. Open ComfyUI Manager
2. Search for "NHK Nodes"
3. Click Install
4. Restart ComfyUI

### Manual Installation
1. Clone or download this repository to `ComfyUI/custom_nodes/nhknodes`
2. Restart ComfyUI
3. Nodes will appear in organized categories under `nhk`

## 🗂️ Node catalog

### 🔤 Text Processing (`nhk/text`)
- **📝 Simple Text Input** (nhk) – Minimal text entry node that just forwards its value.
- **📄 Text Display** (nhk) – Shows any incoming string inside the UI while keeping the data flowing.
- **📂 Load Text Files** (nhk) – Load text files with auto-incrementing index, repeat count, and wrap-around. Scans folders for numbered files (e.g., `saved_text_001.txt`).
- **🧩 Text Combiner** (nhk) – Unlimited text inputs with automatic sockets and configurable separator.
- **🧷 Text Template** (nhk) – Lightweight templating (`The [a] walks in the [b]`) with 4 placeholders [a]-[d].
- **🧷 Text Template Extended** (nhk) – Same as Text Template but with 8 placeholders [a]-[h].

### 🖼️ Image Processing (`nhk/image`)
- **🖼️ Image Loader With Previews** (nhk) – The featured browser with searchable folders, previews, and sorting.
- **📸 Load Image Series** (nhk) – Sequence loader with two modes (single_image/random). Use control_after_generate=increment for auto-advancing.
- **📁 Image Series With Prompts** (nhk) – Loads a folder sequence and attaches per-file prompts from a markdown lookup, with optional default fallback.
- **📦 Image Grid Batch** (nhk) – Stacks arbitrary images into a batch tensor for downstream samplers.
- **🎯 Image Grid Composite** (nhk) – Creates presentation grids with gutters, padding, and background control.
- **📏 Visual Resizer** (nhk) – Drops any image onto a custom canvas size with precise offsets.
- **🧑 Add Headroom** (nhk) – Shrinks the subject within the original canvas to create breathing room up top.
- **🎨 Edit with Krita** (nhk) – Sends a frame to Krita, waits for edits, and re-imports it into the workflow.
- **⏹️ Extract Grid Panel** (nhk) – Extracts a single panel from a grid image using spreadsheet notation (a1, b2, c3). Supports variable grid sizes and separator widths.
- **⏹️ Load 2x2 Grid Series** (nhk) – Loads images from a directory, treating each as a 2x2 grid. Extracts cells in reading order.
- **⏹️ Load 3x3 Grid Series** (nhk) – Loads images from a directory, treating each as a 3x3 grid. Extracts cells in reading order.
- **🎨 RGBA Flatten** (nhk) – Composites RGBA over solid background color, eliminating alpha artifacts and color bleed.
- **🎯 Crop To Mask** (nhk) – Crops image and mask to the mask bbox with a single padding value. Outputs bbox for stitch-back.

### ⚙️ Workflow Utilities (`nhk/utility`)
- **📋 List Selector** (nhk) – Select from a list by index, use a default input, or batch the entire list. Index 0 = default, 1+ = list item. Batch mode outputs all items as an output list.
- **🔄 Cycling Switch** (nhk) – Rotates through unlimited inputs, staying on each for a configurable number of runs.
- **🚪 Interval Gate** (nhk) – Turns a branch on/off every N executions (perfect for “every 5th image” flows).
- **🔀 Double Switch (In/Out)** (nhk) – Paired A/B switches that route image/text tuples together.
- **⏱️ Execution Counter** (nhk) – Counts queue runs, stops when a limit is reached, and shows progress.
- **📐 Size Picker** (nhk) – Flux/SDXL/Qwen/ZIT-optimized resolution presets with handy metadata.
- **🔊 Play Sound** (nhk) – Small notification node that plays an audio file when a queue finishes.
- **🔖 Bookmark** (nhk) – Frontend-only canvas bookmark with keyboard shortcut and zoom positioning.

### 🎛️ Conditioning (`nhk/conditioning`)
- **⚡ Text Encode Flux2 Image Edit** (nhk) – Simplified encoding for Flux2 Klein image editing. Combines prompt + up to 3 reference images into positive/negative conditioning with reference latents attached.

### 🤖 AI & Media (`nhk/ai`)
- **🦙 Ollama API** (nhk) – Local chat/vision models with hidden thinking output and optional image prompts.
- **🤖 OpenAI API** (nhk) – GPT‑4/GPT‑5 chat with optional vision input (requires `OPENAI_API_KEY`).
- **🍌 Gemini API** (nhk) – Gemini 3 Pro multimodal: up to 4 input images, text/image output, configurable aspect ratio and resolution (requires `GOOGLE_API_KEY`).

## 🚀 Key Features

- **Dynamic Inputs** - Many nodes support unlimited inputs that auto-expand as you connect
- **Conditional Branching** - Interval Gate enables periodic workflow paths (upscale every 5th image, etc.)
- **Configurable Cycling** - Cycling Switch with stay duration control for precise input testing
- **Smart UI** - Hover tooltips and emoji icons for easy identification
- **Clean Organization** - Logical categories make nodes easy to find
- **Professional Quality** - Consistent design and error handling throughout

## 📋 Requirements

### For OpenAI API Node
- OpenAI API key in `.env` file:
  ```
  OPENAI_API_KEY=your_api_key_here
  ```
- GPT nodes support gpt-4o, gpt-4o-mini, chatgpt-4o-latest, plus gpt-5 / gpt-5-mini / gpt-5-nano.

### For Gemini API Node
- Google API key in `.env` file:
  ```
  GOOGLE_API_KEY=your_api_key_here
  ```
- Install: `pip install google-genai`

### For Ollama API Node
- Ollama server running locally (`ollama serve`)
- Pull at least one supported model (`ollama pull qwen3-vl:8b`, etc.)
- Optional vision input works automatically when the selected model supports it

### For Edit with Krita Node
- Krita available either as AppImage, system install, or Flatpak
- Writable directory for round-tripping frames (default `/home/nhk/workspace/editing`)

## 📄 License

MIT License - Feel free to use, modify, and distribute.

## 🤝 Contributing

Contributions welcome! Please follow the existing code style and add appropriate documentation.

---

**Created by NHK** | [GitHub](https://github.com/Enashka/ComfyUI-nhknodes) | [ComfyUI Registry](https://registry.comfy.org/)

## 🧪 Experimental (WIP)
- **Image Evaluator**, **Conditional Router/Dual/Splitter/Stop**, **Save Image +**, **Preview Image +** — part of the in-progress Image Evaluation workflow (see `IMAGE_EVALUATION.md`). They load under `nhk/wip`; behavior may change while we resolve reverse-dependency (pull-based) execution quirks in ComfyUI.
