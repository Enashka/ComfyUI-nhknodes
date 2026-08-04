# Image Evaluation & Conditional Routing

> ComfyUI executes **backward** from terminals (`OUTPUT_NODE=True`). Only chains that lead into a terminal are pulled into the graph. The WIP nodes here rely on that lazy, pull-based planning, so:
> - Always end your evaluation branches in a real terminal (e.g., standard Save/Preview or any node with `OUTPUT_NODE=True`). The passthrough Save/Preview here are not terminals by themselves.
> - Conditional Router uses `check_lazy_status` to pull only the active input branch. Conditional Splitter/Stop use `ExecutionBlocker` to silently block the chains that shouldn’t run — no error dialog, so batches keep going.
> - If nothing seems to run, you likely don’t have a terminal reachable from the evaluator branch.

AI-powered image quality control using Qwen3VL for workflow automation.

---

## Nodes

### 🔍 Image Evaluator
**nhk/ai**

Analyzes images with Qwen3VL, outputs pass/fail + confidence + reasoning.

**Inputs:**
- `image` - Image to evaluate
- `evaluation_criteria` - What makes a good image
- `confidence_threshold` - Min score to pass (0.0-1.0, default: 0.7)
- `model` - qwen3-vl:8b or llama3.2-vision:11b
- `temperature` - Lower = more consistent (default: 0.3)

**Outputs:**
- `image` - Passthrough
- `passed` - Boolean (meets criteria AND confidence ≥ threshold)
- `confidence` - Score 0.0-1.0
- `reasoning` - AI explanation
- `info` - Summary

---

### 🔀 Conditional Router
**nhk/utility**

Selects between two input chains based on boolean. Only selected chain executes.

**Inputs:**
- `condition` - Boolean
- `pass_input` - Chain when True (lazy)
- `fail_input` - Chain when False (lazy)

**Outputs:**
- `output` - Selected input
- `info` - Path taken

---

### 🔀 Conditional Router Dual
**nhk/utility**

Selects between two input pairs based on boolean. Only selected pair executes.

**Inputs:**
- `condition` - Boolean
- `pass_input1/2` - Pair when True (lazy)
- `fail_input1/2` - Pair when False (lazy)

**Outputs:**
- `output1/2` - Selected inputs
- `info` - Path taken

---

### 🛑 Conditional Stop
**nhk/utility**

Silently halts the downstream chain if condition is False. No error dialog, so batches keep running.

**Inputs:**
- `input` - Any data
- `condition` - True = continue, False = stop

---

## Example Workflows

### Basic Quality Check
```
Load Image → Image Evaluator → Preview
```

### Route by Quality
```
Image → Upscale → pass_input ──┐
                                ├─► Conditional Router → output → Save
Image → Enhance → fail_input ──┘
        ▲
Evaluator → passed → condition
```

### Hard Quality Gate
```
Image → Evaluator ─┬─► passed → Conditional Stop → Continue
                   └─► image ──────────┘
```

---

## Criteria Examples

**Portrait:** "Clear facial features, eyes in focus, natural skin tones"

**Product:** "Product visible, centered, clean background, proper lighting"

**Technical:** "No motion blur, chromatic aberration, or noise"

**Landscape:** "Sharp, well-composed, good dynamic range, no overexposed areas"

---

## Settings

### Confidence Threshold
- **0.85+** - Very strict
- **0.7** - Standard
- **0.5** - Lenient

### Temperature
- **0.2** - Consistent (recommended for QC)
- **0.5** - Balanced
- **0.7** - Varied

---

## Troubleshooting

**Cannot connect to Ollama:** `ollama serve`

**All images passing/failing:** Check criteria, adjust threshold, review reasoning output

**Inconsistent results:** Lower temperature, use objective criteria

---

## Technical

**Confidence Extraction:** Parses "confidence: 0.85", "8/10", "85%", or quality keywords

**Lazy Evaluation:** Only processes selected branch

**Re-execution:** Evaluator always re-runs for fresh judgments
