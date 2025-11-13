from __future__ import annotations

import os
import folder_paths
from typing import Optional
from comfy_api.input import VideoInput
from comfy_api.util import VideoCodec, VideoContainer
from comfy_api.latest import io, ui
from comfy.cli_args import args


class SaveVideoShort(io.ComfyNode):
    """
    Save Video node with 3-digit counter (000-999) instead of 5-digit.
    Useful for smaller batches where short filenames are preferred.
    """

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="SaveVideoShort",
            display_name="Save Video (Short)",
            category="nhk/video",
            description="Saves video with 3-digit counter (000-999) instead of 5-digit.",
            inputs=[
                io.Video.Input("video", tooltip="The video to save."),
                io.String.Input("filename_prefix", default="video/ComfyUI", tooltip="The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes."),
                io.Combo.Input("format", options=VideoContainer.as_input(), default="auto", tooltip="The format to save the video as."),
                io.Combo.Input("codec", options=VideoCodec.as_input(), default="auto", tooltip="The codec to use for the video."),
            ],
            outputs=[],
            hidden=[io.Hidden.prompt, io.Hidden.extra_pnginfo],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, video: VideoInput, filename_prefix, format, codec) -> io.NodeOutput:
        width, height = video.get_dimensions()
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix,
            folder_paths.get_output_directory(),
            width,
            height
        )
        saved_metadata = None
        if not args.disable_metadata:
            metadata = {}
            if cls.hidden.extra_pnginfo is not None:
                metadata.update(cls.hidden.extra_pnginfo)
            if cls.hidden.prompt is not None:
                metadata["prompt"] = cls.hidden.prompt
            if len(metadata) > 0:
                saved_metadata = metadata

        # Use :03 for 3-digit counter (000-999) instead of :05 (00000-99999)
        file = f"{filename}_{counter:03}_.{VideoContainer.get_extension(format)}"

        video.save_to(
            os.path.join(full_output_folder, file),
            format=format,
            codec=codec,
            metadata=saved_metadata
        )

        return io.NodeOutput(ui=ui.PreviewVideo([ui.SavedResult(file, subfolder, io.FolderType.output)]))


# Node registration
NODE_CLASS_MAPPINGS = {
    "SaveVideoShort": SaveVideoShort,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveVideoShort": "Save Video (Short)",
}
