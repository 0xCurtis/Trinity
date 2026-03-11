import os
import ffmpeg
from pathlib import Path

from src.pipeline import MyPipeline
from src.retry import retry_with_backoff


DEFAULT_WATERMARK_PATH = "/app/watermark.png"
DEFAULT_FONT = "Arial"
DEFAULT_FONT_SIZE = 24
DEFAULT_POSITION = "bottom-right"
DEFAULT_OPACITY = 0.5
DEFAULT_MARGIN = 10
DEFAULT_MAX_WIDTH = 200
DEFAULT_MAX_HEIGHT = 50


def _get_position_overlay(
    width: int, height: int, watermark_width: int, watermark_height: int, position: str, margin: int
) -> tuple:
    """Calculate overlay position coordinates."""
    positions = {
        "top-left": (margin, margin),
        "top-right": (width - watermark_width - margin, margin),
        "bottom-left": (margin, height - watermark_height - margin),
        "bottom-right": (width - watermark_width - margin, height - watermark_height - margin),
        "center": ((width - watermark_width) // 2, (height - watermark_height) // 2),
    }
    return positions.get(position, positions["bottom-right"])


@retry_with_backoff(max_retries=2, base_delay=1.0)
def watermark(pipeline: MyPipeline = None, args: dict = None) -> dict:
    """Add watermark to images/videos."""
    config = args.get("watermark", {})

    if not config:
        return args

    media = args.get("media")
    if not media or not media[0].get("path"):
        return args

    file_path = media[0]["path"]
    if not os.path.exists(file_path):
        pipeline.log(f"Watermark skipped: file not found {file_path}")
        return args

    wm_type = config.get("type", "image")
    position = config.get("position", DEFAULT_POSITION)
    opacity = float(config.get("opacity", DEFAULT_OPACITY))
    margin = int(config.get("margin", DEFAULT_MARGIN))

    if wm_type == "text":
        return _add_text_watermark(pipeline, args, config, position, opacity, margin)
    else:
        return _add_image_watermark(pipeline, args, config, position, opacity, margin)


def _add_image_watermark(
    pipeline: MyPipeline, args: dict, config: dict, position: str, opacity: float, margin: int
):
    """Add image watermark to media."""
    wm_path = config.get("image_path", DEFAULT_WATERMARK_PATH)

    if not os.path.exists(wm_path):
        pipeline.log(f"Watermark skipped: watermark image not found {wm_path}")
        return args

    media = args["media"]
    file_path = media[0]["path"]

    output_path = _get_output_path(file_path)

    try:
        video = ffmpeg.input(file_path)
        watermark_input = ffmpeg.input(wm_path)

        probe = ffmpeg.probe(file_path)
        video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
        width = int(video_info["width"])
        height = int(video_info["height"])

        wm_probe = ffmpeg.probe(wm_path)
        wm_info = next(s for s in wm_probe["streams"] if s["codec_type"] == "video")
        wm_width = int(wm_info["width"])
        wm_height = int(wm_info["height"])

        if wm_width > DEFAULT_MAX_WIDTH or wm_height > DEFAULT_MAX_HEIGHT:
            scale_w = DEFAULT_MAX_WIDTH / wm_width
            scale_h = DEFAULT_MAX_HEIGHT / wm_height
            scale = min(scale_w, scale_h)
            wm_width = int(wm_width * scale)
            wm_height = int(wm_height * scale)

        x, y = _get_position_overlay(width, height, wm_width, wm_height, position, margin)

        watermark_input = watermark_input.filter("scale", wm_width, wm_height)
        watermark_input = watermark_input.filter("format", "rgba")
        watermark_input = watermark_input.filter("colorchannelmixer", aa=opacity)

        stream = ffmpeg.filter(video, "format", "pix_fmts=" + "yuv420p")

        (
            ffmpeg.filter([stream, watermark_input], "overlay", x, y)
            .output(
                output_path,
                **{"c:v": "libx264", "-preset": "fast", "-crf": "23", "-movflags": "+faststart"},
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        os.remove(file_path)
        os.rename(output_path, file_path)
        pipeline.log(f"Watermark added: {file_path}")

    except ffmpeg.Error as e:
        pipeline.log(f"Watermark error: {e.stderr.decode() if e.stderr else str(e)}")

    return args


def _add_text_watermark(
    pipeline: MyPipeline, args: dict, config: dict, position: str, opacity: float, margin: int
):
    """Add text watermark to media."""
    text = config.get("text", "")
    if not text:
        return args

    font = config.get("font", DEFAULT_FONT)
    font_size = int(config.get("font_size", DEFAULT_FONT_SIZE))
    color = config.get("color", "white")

    media = args["media"]
    file_path = media[0]["path"]

    output_path = _get_output_path(file_path)

    try:
        video = ffmpeg.input(file_path)

        probe = ffmpeg.probe(file_path)
        video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
        width = int(video_info["width"])
        height = int(video_info["height"])

        text_width = len(text) * font_size * 0.6
        text_height = font_size * 1.2

        x, y = _get_position_overlay(
            width, height, int(text_width), int(text_height), position, margin
        )

        color_hex = _convert_color(color, opacity)

        stream = ffmpeg.filter(video, "format", "pix_fmts=" + "yuv420p")

        (
            ffmpeg.filter(
                stream,
                "drawtext",
                fontfile=f"/usr/share/fonts/truetype/{font}/{font}.ttf",
                text=text,
                fontsize=font_size,
                fontcolor=color_hex,
                x=x,
                y=y,
                shadowcolor="black@0.5",
                shadowx=2,
                shadowy=2,
            )
            .output(
                output_path,
                **{"c:v": "libx264", "-preset": "fast", "-crf": "23", "-movflags": "+faststart"},
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        os.remove(file_path)
        os.rename(output_path, file_path)
        pipeline.log(f"Text watermark added: {file_path}")

    except ffmpeg.Error as e:
        pipeline.log(f"Text watermark error: {e.stderr.decode() if e.stderr else str(e)}")

    return args


def _get_output_path(file_path: str) -> str:
    """Generate output path for watermarked file."""
    path = Path(file_path)
    return str(path.parent / f"{path.stem}_wm{path.suffix}")


def _convert_color(color: str, opacity: float) -> str:
    """Convert color name to hex with opacity."""
    color_map = {
        "white": "ffffff",
        "black": "000000",
        "red": "ff0000",
        "green": "00ff00",
        "blue": "0000ff",
        "yellow": "ffff00",
        "cyan": "00ffff",
        "magenta": "ff00ff",
    }

    hex_color = color_map.get(color.lower(), color.lstrip("#"))
    alpha = int(opacity * 255)
    return f"#{hex_color}{alpha:02x}"
