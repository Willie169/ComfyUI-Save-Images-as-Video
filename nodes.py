# nodes.py
import subprocess
import os
import shlex
import tempfile
import numpy as np
from PIL import Image
import folder_paths
import torch
import torchaudio
import json
import base64
from comfy.cli_args import args
from .ffmpeg_path_resolver import get_ffmpeg_path
from .node_logger import (
    log_node_info,
    log_node_success,
    log_node_error,
    log_node_warning,
    log_node_debug,
)


# A base class containing common logic for working with FFmpeg.
class FFmpegConverterBase:
    FPS = (
        "FLOAT",
        {
            "default": 24.0,
            "min": 1.0,
            "max": 340282346638528859811704183484516925440.0,
            "step": 1.0,
        },
    )

    VIDEO_CODEC = (
        [
            "skip",
            "a64multi",
            "a64multi5",
            "alias_pix",
            "amv",
            "apng",
            "asv1",
            "asv2",
            "libsvtav1",
            "avrp",
            "avui",
            "bitpacked",
            "bmp",
            "cfhd",
            "cinepak",
            "cljr",
            "vc2",
            "dnxhd",
            "dpx",
            "dvvideo",
            "dxv",
            "exr",
            "ffv1",
            "ffvhuff",
            "fits",
            "flashsv",
            "flashsv2",
            "flv",
            "gif",
            "h261",
            "h263",
            "h263_v4l2m2m",
            "h263p",
            "libx264",
            "libx264rgb",
            "h264_v4l2m2m",
            "hdr",
            "libx265",
            "hevc_v4l2m2m",
            "huffyuv",
            "jpeg2000",
            "jpegls",
            "ljpeg",
            "magicyuv",
            "mjpeg",
            "mpeg1video",
            "mpeg2video",
            "mpeg4",
            "mpeg4_v4l2m2m",
            "msmpeg4v2",
            "msmpeg4",
            "msrle",
            "msvideo1",
            "pam",
            "pbm",
            "pcx",
            "pdv",
            "pfm",
            "pgm",
            "pgmyuv",
            "phm",
            "png",
            "ppm",
            "prores",
            "prores_aw",
            "prores_ks",
            "qoi",
            "qtrle",
            "r10k",
            "r210",
            "rawvideo",
            "roqvideo",
            "rpza",
            "rv10",
            "rv20",
            "sgi",
            "smc",
            "snow",
            "speedhq",
            "sunrast",
            "svq1",
            "targa",
            "tiff",
            "utvideo",
            "v210",
            "vbn",
            "vnull",
            "libvpx",
            "vp8_v4l2m2m",
            "libvpx-vp9",
            "wbmp",
            "wmv1",
            "wmv2",
            "wrapped_avframe",
            "xbm",
            "xface",
            "xwd",
            "y41p",
            "yuv4",
            "zlib",
            "zmbv",
        ],
        {
            "default": "libx264",
            "tooltip": "If set to skip, -c:a option will be skipped; otherwise, -c:a <value> will be used.",
        },
    )

    PIXEL_FORMAT = (
        [
            "copy",
            "skip",
            "yuv420p",
            "yuyv422",
            "rgb24",
            "bgr24",
            "yuv422p",
            "yuv444p",
            "yuv410p",
            "yuv411p",
            "gray",
            "monow",
            "monob",
            "yuvj420p",
            "yuvj422p",
            "yuvj444p",
            "uyvy422",
            "bgr8",
            "bgr4",
            "bgr4_byte",
            "rgb8",
            "rgb4",
            "rgb4_byte",
            "nv12",
            "nv21",
            "argb",
            "rgba",
            "abgr",
            "bgra",
            "gray16be",
            "gray16le",
            "yuv440p",
            "yuvj440p",
            "yuva420p",
            "rgb48be",
            "rgb48le",
            "rgb565be",
            "rgb565le",
            "rgb555be",
            "rgb555le",
            "bgr565be",
            "bgr565le",
            "bgr555be",
            "bgr555le",
            "yuv420p16le",
            "yuv420p16be",
            "yuv422p16le",
            "yuv422p16be",
            "yuv444p16le",
            "yuv444p16be",
            "rgb444le",
            "rgb444be",
            "bgr444le",
            "bgr444be",
            "ya8",
            "bgr48be",
            "bgr48le",
            "yuv420p9be",
            "yuv420p9le",
            "yuv420p10be",
            "yuv420p10le",
            "yuv422p10be",
            "yuv422p10le",
            "yuv444p9be",
            "yuv444p9le",
            "yuv444p10be",
            "yuv444p10le",
            "yuv422p9be",
            "yuv422p9le",
            "gbrp",
            "gbrp9be",
            "gbrp9le",
            "gbrp10be",
            "gbrp10le",
            "gbrp16be",
            "gbrp16le",
            "yuva422p",
            "yuva444p",
            "yuva420p9be",
            "yuva420p9le",
            "yuva422p9be",
            "yuva422p9le",
            "yuva444p9be",
            "yuva444p9le",
            "yuva420p10be",
            "yuva420p10le",
            "yuva422p10be",
            "yuva422p10le",
            "yuva444p10be",
            "yuva444p10le",
            "yuva420p16be",
            "yuva420p16le",
            "yuva422p16be",
            "yuva422p16le",
            "yuva444p16be",
            "yuva444p16le",
            "xyz12le",
            "xyz12be",
            "nv16",
            "nv20le",
            "nv20be",
            "rgba64be",
            "rgba64le",
            "bgra64be",
            "bgra64le",
            "yvyu422",
            "ya16be",
            "ya16le",
            "gbrap",
            "gbrap16be",
            "gbrap16le",
            "0rgb",
            "rgb0",
            "0bgr",
            "bgr0",
            "yuv420p12be",
            "yuv420p12le",
            "yuv420p14be",
            "yuv420p14le",
            "yuv422p12be",
            "yuv422p12le",
            "yuv422p14be",
            "yuv422p14le",
            "yuv444p12be",
            "yuv444p12le",
            "yuv444p14be",
            "yuv444p14le",
            "gbrp12be",
            "gbrp12le",
            "gbrp14be",
            "gbrp14le",
            "yuvj411p",
            "yuv440p10le",
            "yuv440p10be",
            "yuv440p12le",
            "yuv440p12be",
            "ayuv64le",
            "ayuv64be",
            "p010le",
            "p010be",
            "gbrap12be",
            "gbrap12le",
            "gbrap10be",
            "gbrap10le",
            "gray12be",
            "gray12le",
            "gray10be",
            "gray10le",
            "p016le",
            "p016be",
            "gray9be",
            "gray9le",
            "gbrpf32be",
            "gbrpf32le",
            "gbrapf32be",
            "gbrapf32le",
            "gray14be",
            "gray14le",
            "grayf32be",
            "grayf32le",
            "yuva422p12be",
            "yuva422p12le",
            "yuva444p12be",
            "yuva444p12le",
            "nv24",
            "nv42",
            "y210le",
            "x2rgb10le",
            "x2bgr10le",
            "p210be",
            "p210le",
            "p410be",
            "p410le",
            "p216be",
            "p216le",
            "p416be",
            "p416le",
            "vuya",
            "vuyx",
            "p012le",
            "p012be",
            "y212le",
            "xv30le",
            "xv36be",
            "xv36le",
            "p212be",
            "p212le",
            "p412be",
            "p412le",
            "gbrap14be",
            "gbrap14le",
            "ayuv",
            "uyva",
            "vyu444",
            "v30xle",
            "y216le",
            "xv48be",
            "xv48le",
            "yuv444p10msbbe",
            "yuv444p10msble",
            "yuv444p12msbbe",
            "yuv444p12msble",
            "gbrp10msbbe",
            "gbrp10msble",
            "gbrp12msbbe",
            "gbrp12msble",
        ],
        {
            "default": "yuv420p",
            "tooltip": "If set to skip, -pix_fmt option will be skipped; otherwise, -pix_fmt <value> will be used.",
        },
    )

    CRF = (
        "INT",
        {
            "default": 23,
            "min": -1,
            "max": 2147483647,
            "step": 1,
            "tooltip": "If set to -1, -crf option will be skipped; otherwise, -crf <value> will be used.",
        },
    )

    AUDIO_CODEC = (
        [
            "copy",
            "skip",
            "aac",
            "ac3",
            "ac3_fixed",
            "adpcm_adx",
            "adpcm_argo",
            "g722",
            "g726",
            "g726le",
            "adpcm_ima_alp",
            "adpcm_ima_amv",
            "adpcm_ima_apm",
            "adpcm_ima_qt",
            "adpcm_ima_ssi",
            "adpcm_ima_wav",
            "adpcm_ima_ws",
            "adpcm_ms",
            "adpcm_swf",
            "adpcm_yamaha",
            "alac",
            "anull",
            "aptx",
            "aptx_hd",
            "comfortnoise",
            "dfpwm",
            "dca",
            "eac3",
            "flac",
            "g723_1",
            "mlp",
            "mp2",
            "mp2fixed",
            "libmp3lame",
            "nellymoser",
            "opus",
            "libopus",
            "pcm_alaw",
            "pcm_bluray",
            "pcm_dvd",
            "pcm_f32be",
            "pcm_f32le",
            "pcm_f64be",
            "pcm_f64le",
            "pcm_mulaw",
            "pcm_s16be",
            "pcm_s16be_planar",
            "pcm_s16le",
            "pcm_s16le_planar",
            "pcm_s24be",
            "pcm_s24daud",
            "pcm_s24le",
            "pcm_s24le_planar",
            "pcm_s32be",
            "pcm_s32le",
            "pcm_s32le_planar",
            "pcm_s64be",
            "pcm_s64le",
            "pcm_s8",
            "pcm_s8_planar",
            "pcm_u16be",
            "pcm_u16le",
            "pcm_u24be",
            "pcm_u24le",
            "pcm_u32be",
            "pcm_u32le",
            "pcm_u8",
            "pcm_vidc",
            "real_144",
            "roq_dpcm",
            "s302m",
            "sbc",
            "truehd",
            "tta",
            "vorbis",
            "wavpack",
            "wmav1",
            "wmav2",
        ],
        {
            "default": "flac",
            "tooltip": "If set to skip, -c:a option will be skipped; otherwise, -c:a <value> will be used.",
        },
    )

    BITRATE = (
        "INT",
        {
            "default": 0,
            "min": 0,
            "max": 2147483647,
            "step": 1,
            "tooltip": "If set to 0, -b:a option will be skipped; otherwise, -b:a <value>k will be used.",
        },
    )

    VIDEO_FORMAT = (
        "STRING",
        {
            "multiline": False,
            "default": "mkv",
        },
    )

    AUDIO_FORMAT = (
        "STRING",
        {
            "multiline": False,
            "default": "opus",
        },
    )

    AUDIO_HANDLING = (
        ["copy original", "replace with new", "remove audio", "skip"],
        {
            "default": "copy original",
            "tooltip": "If set to skip, audio options will be skipped; if set to replace with new, you have to supply an audio input, and the first track will be used if the input contains multiple tracks.",
        },
    )

    TIMEOUT = (
        "INT",
        {"default": 300, "min": 1, "max": 2147483647, "step": 1},
    )

    METADATA = (
        [
            "original",
            "original, non-Windows only",
            "base64",
            "base64, non-Windows only",
            "none",
        ],
        {"default": "original, non-Windows only"},
    )

    OUTPUT_FILE_OPT = (
        "STRING",
        {
            "multiline": True,
            "default": "",
            "tooltip": "Custom FFmpeg output options. One option per line or space‑separated. For example, -preset slow",
        },
    )

    HIDDEN = {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}

    @staticmethod
    def _add_copy(tpl):
        return (["copy"] + tpl[0], tpl[1])

    def _add_metadata(self, metadata_dict, base_params, metadata_strategy):
        """
        Add metadata to FFmpeg parameters with various encoding strategies

        Args:
            metadata_dict: Dictionary containing metadata to embed
            base_params: Dictionary of FFmpeg parameters to extend
            metadata_strategy: One of:
                - "original": Embed as raw JSON string
                - "original, non-Windows only": Embed as raw JSON string and only on non-Windows systems
                - "base64": Embed as base64 encoded JSON
                - "base64, non-Windows only": Embed as base64 encoded JSON and only on non-Windows systems
                - "none": Don't embed metadata

        Returns:
            Updated base_params dictionary
        """
        if not metadata_dict:
            return base_params

        # Parse the strategy
        strategy_parts = metadata_strategy.split(",")
        strategy = strategy_parts[0]
        is_non_windows_only = len(strategy_parts) > 1

        if os.name == "nt" and is_non_windows_only:
            log_node_debug(
                self.NODE_LOG_PREFIX,
                f"Skipping metadata on Windows system (strategy: {metadata_strategy})",
            )
            return base_params

        if strategy == "none":
            log_node_debug(
                self.NODE_LOG_PREFIX, "Metadata embedding disabled by strategy"
            )
            return base_params

        try:
            metadata_json = json.dumps(metadata_dict)
            if strategy == "base64":
                metadata_encoded = base64.b64encode(
                    metadata_json.encode("utf-8")
                ).decode("utf-8")
                base_params["-metadata"] = f"comment=b64:{metadata_encoded}"
                log_node_debug(
                    self.NODE_LOG_PREFIX,
                    f"Added base64-encoded metadata (strategy: {metadata_strategy})",
                )
            else:
                base_params["-metadata"] = f"comment={metadata_json}"
                log_node_debug(
                    self.NODE_LOG_PREFIX,
                    f"Added original metadata (strategy: {metadata_strategy})",
                )

        except Exception as e:
            log_node_error(
                self.NODE_LOG_PREFIX,
                f"Failed to add metadata: {e}. Metadata will be skipped.",
            )

        return base_params

    def _build_ffmpeg_params(self, base_params, override_str, log_prefix):
        """
        Merge GUI/base FFmpeg parameters with user-supplied output options.
        User-supplied parameters take precedence.
        """
        try:
            override_args = shlex.split(override_str)
        except ValueError as e:
            log_node_error(
                log_prefix,
                f"Error parsing override parameters: {e}. Ignoring overrides.",
            )
            override_args = []

        final_params = base_params.copy()
        i = 0
        while i < len(override_args):
            flag = override_args[i]
            if not flag.startswith("-"):
                log_node_warning(
                    log_prefix,
                    f"Token not starting with '-' '{flag}' in override parameters.",
                )

            # Support both options with values and valueless flags such as -an.
            if i + 1 < len(override_args) and not override_args[i + 1].startswith("-"):
                value = override_args[i + 1]
                if flag in final_params:
                    log_node_warning(
                        log_prefix,
                        f"Overriding GUI parameter '{flag}' with value '{value}' "
                        f"(was '{final_params[flag]}').",
                    )
                final_params[flag] = value
                i += 2
            else:
                final_params[flag] = None
                i += 1

        result_list = []
        for key, val in final_params.items():
            result_list.append(key)
            if val is not None:
                result_list.append(str(val))

        return result_list

    def _execute_ffmpeg_command(self, ffmpeg_cmd, log_prefix, timeout):
        log_node_info(log_prefix, f"Executing ffmpeg: {' '.join(ffmpeg_cmd)}")
        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            stdout, stderr = process.communicate(timeout)
            if process.returncode != 0:
                err_msg = f"ffmpeg error (code {process.returncode}):\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                log_node_error(log_prefix, err_msg)
                return {
                    "ui": {
                        "text": [
                            f"ffmpeg error (code {process.returncode}): Check console for details."
                        ]
                    }
                }
            else:
                log_node_success(log_prefix, "FFmpeg command executed successfully.")
                if stderr.strip():
                    log_node_warning(
                        log_prefix,
                        f"ffmpeg stderr (warnings):\n{stderr}",
                        msg_color_override="GREY",
                    )
                return None  # Успіх
        except Exception as e:
            log_node_error(log_prefix, f"Python error during ffmpeg execution: {e}")
            return {"ui": {"text": [f"Python error: {e}"]}}


class SaveFramesToVideoFFmpeg(FFmpegConverterBase):
    NODE_LOG_PREFIX = "SaveVideoFFMPEG"

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.ffmpeg_executable_path = get_ffmpeg_path()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "VID"}),
                "fps": cls.FPS,
                "codec": cls.VIDEO_CODEC,
                "pixel_format": cls.PIXEL_FORMAT,
                "crf": cls.CRF,
                "output_format": cls.VIDEO_FORMAT,
            },
            "optional": {
                "audio": ("AUDIO",),
                "audio_codec": cls.AUDIO_CODEC,
                "audio_bitrate": cls.BITRATE,
                "output_file_opt": cls.OUTPUT_FILE_OPT,
                "timeout": cls.TIMEOUT,
                "metadata": cls.METADATA,
            },
            "hidden": cls.HIDDEN,
        }

    RETURN_TYPES = ()
    FUNCTION = "save_video"
    OUTPUT_NODE = True
    CATEGORY = "San4itos"

    def save_video(
        self,
        images,
        filename_prefix,
        fps,
        codec,
        pixel_format,
        crf,
        output_format,
        audio=None,
        audio_codec="aac",
        audio_bitrate=192,
        output_file_opt="",
        timeout=300,
        metadata="original, non-Windows only",
        prompt=None,
        extra_pnginfo=None,
    ):

        h, w = images[0].shape[0], images[0].shape[1]
        (
            full_output_folder,
            filename_part,
            counter,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path(filename_prefix, self.output_dir, w, h)
        video_filename = f"{filename_part}_{counter:05}_.{output_format}"
        video_full_path = os.path.join(full_output_folder, video_filename)

        with tempfile.TemporaryDirectory() as temp_dir:
            for i, image_tensor in enumerate(images):
                img_pil = Image.fromarray(
                    (image_tensor.cpu().numpy() * 255).astype(np.uint8)
                )
                img_pil.save(os.path.join(temp_dir, f"frame_{i:06d}.png"), "PNG")

            ffmpeg_cmd = [
                self.ffmpeg_executable_path,
                "-y",
                "-framerate",
                str(fps),
                "-i",
                os.path.join(temp_dir, "frame_%06d.png"),
            ]
            has_audio = audio and "waveform" in audio and audio["waveform"].numel() > 0

            if has_audio:
                temp_audio_file = os.path.join(temp_dir, "temp_audio.wav")
                waveform_tensor = audio["waveform"]
                if waveform_tensor.shape[0] > 1:
                    log_node_warning(
                        self.NODE_LOG_PREFIX,
                        f"Audio batch size is {waveform_tensor.shape[0]}. Using the first audio track.",
                    )
                torchaudio.save(
                    temp_audio_file, waveform_tensor[0].cpu(), audio["sample_rate"]
                )
                ffmpeg_cmd.extend(["-i", temp_audio_file])

            # Prepare metadata
            metadata_dict = {}
            if not args.disable_metadata:
                if prompt is not None:
                    metadata_dict["prompt"] = prompt
                if extra_pnginfo is not None:
                    metadata_dict.update(extra_pnginfo)

            base_params = {}
            if codec != "skip":
                base_params["-c:v"] = codec
            if pixel_format != "skip":
                base_params["-pix_fmt"] = pixel_format
            if crf != -1:
                base_params["-crf"] = crf

            # Add metadata using the helper method
            base_params = self._add_metadata(metadata_dict, base_params, metadata)

            if has_audio:
                if audio_codec != "skip":
                    base_params["-c:a"] = audio_codec
                if audio_bitrate != 0:
                    base_params["-b:a"] = str(audio_bitrate) + "k"
                base_params["-shortest"] = None
            else:
                base_params["-an"] = None

            final_params = self._build_ffmpeg_params(
                base_params, output_file_opt, self.NODE_LOG_PREFIX
            )
            ffmpeg_cmd.extend(final_params)

            ffmpeg_cmd.append(video_full_path)

            error = self._execute_ffmpeg_command(
                ffmpeg_cmd, self.NODE_LOG_PREFIX, timeout
            )
            if error:
                return error

            preview = [
                {"filename": video_filename, "subfolder": subfolder, "type": self.type}
            ]
            return {"ui": {"videos": preview}}


class ConvertVideoFFmpeg(FFmpegConverterBase):
    NODE_LOG_PREFIX = "ConvertVideoFFMPEG"

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.ffmpeg_executable_path = get_ffmpeg_path()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
                "filename_prefix": ("STRING", {"default": "VID_conv"}),
                "codec": cls._add_copy(cls.VIDEO_CODEC),
                "pixel_format": cls.PIXEL_FORMAT,
                "crf": cls.CRF,
                "output_format": cls.VIDEO_FORMAT,
                "audio_handling": cls.AUDIO_HANDLING,
            },
            "optional": {
                "audio": ("AUDIO",),
                "audio_codec": cls.AUDIO_CODEC,
                "audio_bitrate": cls.BITRATE,
                "output_file_opt": cls.OUTPUT_FILE_OPT,
                "timeout": cls.TIMEOUT,
                "metadata": cls.METADATA,
            },
            "hidden": cls.HIDDEN,
        }

    RETURN_TYPES = ()
    FUNCTION = "convert_video"
    OUTPUT_NODE = True
    CATEGORY = "San4itos"

    def convert_video(
        self,
        video,
        filename_prefix,
        codec,
        pixel_format,
        crf,
        output_format,
        audio_handling,
        audio=None,
        audio_codec="aac",
        audio_bitrate=192,
        output_file_opt="",
        timeout=300,
        metadata="original, non-Windows only",
        prompt=None,
        extra_pnginfo=None,
    ):

        (
            full_output_folder,
            filename_part,
            counter,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path(filename_prefix, self.output_dir, 0, 0)
        video_filename = f"{filename_part}_{counter:05}_.{output_format}"
        video_full_path = os.path.join(full_output_folder, video_filename)

        # Prepare metadata
        metadata_dict = {}
        if not args.disable_metadata:
            if prompt is not None:
                metadata_dict["prompt"] = prompt
            if extra_pnginfo is not None:
                metadata_dict.update(extra_pnginfo)

        is_direct_path = hasattr(video, "_is_direct_path")

        error = None
        if is_direct_path:
            log_node_info(
                self.NODE_LOG_PREFIX, "Direct path detected. Using fast conversion."
            )
            ffmpeg_cmd = [self.ffmpeg_executable_path, "-y", "-i", video.filepath]

            base_params = {}
            if codec != "skip":
                base_params["-c:v"] = codec
            if pixel_format != "skip":
                base_params["-pix_fmt"] = pixel_format
            if crf != -1:
                base_params["-crf"] = crf

            # Add metadata using the helper method
            base_params = self._add_metadata(metadata_dict, base_params, metadata)

            if audio_handling == "copy original":
                base_params["-c:a"] = "copy"
            elif audio_handling == "remove audio":
                base_params["-an"] = None
            elif audio_handling == "replace with new":
                log_node_warning(
                    self.NODE_LOG_PREFIX,
                    "Audio replacement is not supported in direct path mode. Audio will be copied.",
                )
                base_params["-c:a"] = "copy"

            final_params = self._build_ffmpeg_params(
                base_params, output_file_opt, self.NODE_LOG_PREFIX
            )
            ffmpeg_cmd.extend(final_params)

            ffmpeg_cmd.append(video_full_path)
            error = self._execute_ffmpeg_command(
                ffmpeg_cmd, self.NODE_LOG_PREFIX, timeout
            )
        else:
            log_node_info(
                self.NODE_LOG_PREFIX,
                "Standard video object detected. Using compatibility mode.",
            )
            components = video.get_components()
            images, source_audio, source_fps = (
                components.images,
                components.audio,
                float(components.frame_rate),
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                for i, image_tensor in enumerate(images):
                    Image.fromarray(
                        (image_tensor.cpu().numpy() * 255).astype(np.uint8)
                    ).save(os.path.join(temp_dir, f"frame_{i:06d}.png"))

                ffmpeg_cmd = [
                    self.ffmpeg_executable_path,
                    "-y",
                    "-framerate",
                    str(source_fps),
                    "-i",
                    os.path.join(temp_dir, "frame_%06d.png"),
                ]

                final_audio = (
                    source_audio
                    if audio_handling == "copy original"
                    else audio if audio_handling == "replace with new" else None
                )
                has_audio = (
                    final_audio
                    and "waveform" in final_audio
                    and final_audio["waveform"].numel() > 0
                )

                if has_audio:
                    temp_audio_file = os.path.join(temp_dir, "temp_audio.wav")
                    torchaudio.save(
                        temp_audio_file,
                        final_audio["waveform"][0].cpu(),
                        final_audio["sample_rate"],
                    )
                    ffmpeg_cmd.extend(["-i", temp_audio_file])

                base_params = {}
                if codec != "skip":
                    base_params["-c:v"] = codec
                if pixel_format != "skip":
                    base_params["-pix_fmt"] = pixel_format
                if crf != -1:
                    base_params["-crf"] = crf

                # Add metadata using the helper method
                base_params = self._add_metadata(metadata_dict, base_params, metadata)

                if has_audio:
                    if audio_codec != "skip":
                        base_params["-c:a"] = (audio_codec,)
                    if audio_bitrate != 0:
                        base_params["-b:a"] = str(audio_bitrate) + "k"
                    base_params["-shortest"] = None
                else:
                    base_params["-an"] = None

                final_params = self._build_ffmpeg_params(
                    base_params, output_file_opt, self.NODE_LOG_PREFIX
                )
                ffmpeg_cmd.extend(final_params)

                ffmpeg_cmd.append(video_full_path)
                error = self._execute_ffmpeg_command(
                    ffmpeg_cmd, self.NODE_LOG_PREFIX, timeout
                )

        if error:
            return error

        preview = [
            {"filename": video_filename, "subfolder": subfolder, "type": self.type}
        ]
        return {"ui": {"videos": preview}}


class ConvertAudioFFmpeg(FFmpegConverterBase):
    NODE_LOG_PREFIX = "ConvertAudioFFMPEG"

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.ffmpeg_executable_path = get_ffmpeg_path()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename_prefix": ("STRING", {"default": "AUD"}),
                "codec": cls.AUDIO_CODEC,
                "bitrate": cls.BITRATE,
                "output_format": cls.AUDIO_FORMAT,
            },
            "optional": {
                "output_file_opt": cls.OUTPUT_FILE_OPT,
                "timeout": cls.TIMEOUT,
                "metadata": cls.METADATA,
            },
            "hidden": cls.HIDDEN,
        }

    RETURN_TYPES = ()
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    CATEGORY = "San4itos"

    def save_audio(
        self,
        audio,
        filename_prefix,
        bitrate,
        output_format,
        output_file_opt="",
        timeout=300,
        metadata="original, non-Windows only",
        prompt=None,
        extra_pnginfo=None,
    ):
        (
            full_output_folder,
            filename_part,
            counter,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path(filename_prefix, self.output_dir, 0, 0)
        audio_filename = f"{filename_part}_{counter:05}_.{output_format}"
        audio_full_path = os.path.join(
            os.path.join(full_output_folder, "audio"), audio_filename
        )

        waveform = audio["waveform"]
        if waveform.shape[0] > 1:
            log_node_warning(
                self.NODE_LOG_PREFIX,
                f"Audio batch size is {waveform.shape[0]}. Using the first audio track.",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio_file = os.path.join(temp_dir, "input.wav")
            torchaudio.save(temp_audio_file, waveform[0].cpu(), audio["sample_rate"])

            ffmpeg_cmd = [self.ffmpeg_executable_path, "-y", "-i", temp_audio_file]
            base_params = {}
            if bitrate != 0:
                base_params["-b:a"] = str(bitrate) + "k"

            metadata_dict = {}
            if not args.disable_metadata:
                if prompt is not None:
                    metadata_dict["prompt"] = prompt
                if extra_pnginfo is not None:
                    metadata_dict.update(extra_pnginfo)

            # Add metadata using the helper method
            base_params = self._add_metadata(metadata_dict, base_params, metadata)

            ffmpeg_cmd.extend(
                self._build_ffmpeg_params(
                    base_params, output_file_opt, self.NODE_LOG_PREFIX
                )
            )
            ffmpeg_cmd.append(audio_full_path)

            error = self._execute_ffmpeg_command(
                ffmpeg_cmd, self.NODE_LOG_PREFIX, timeout
            )
            if error:
                return error

        return {
            "ui": {
                "audio": [
                    {
                        "filename": audio_filename,
                        "subfolder": subfolder,
                        "type": self.type,
                    }
                ]
            }
        }


class VideoPathWrapper:
    def __init__(self, filepath):
        self.filepath = filepath
        self._is_direct_path = True

    def get_components(self):
        from comfy.comfy_types import InputImpl

        return InputImpl.VideoFromFile(self.filepath).get_components()


class LoadVideoByPath_san4itos:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = folder_paths.filter_files_content_types(
            [
                f
                for f in os.listdir(input_dir)
                if os.path.isfile(os.path.join(input_dir, f))
            ],
            ["video"],
        )
        return {"required": {"video_file": (sorted(files), {"video_upload": True})}}

    CATEGORY = "San4itos"
    RETURN_TYPES = ("VIDEO",)
    FUNCTION = "load_video"

    def load_video(self, video_file):
        video_path = folder_paths.get_annotated_filepath(video_file)
        return (VideoPathWrapper(video_path),)


NODE_CLASS_MAPPINGS = {
    "SaveFramesToVideoFFmpeg_san4itos": SaveFramesToVideoFFmpeg,
    "ConvertVideoFFmpeg_san4itos": ConvertVideoFFmpeg,
    "ConvertAudioFFmpeg_san4itos": ConvertAudioFFmpeg,
    "LoadVideoByPath_san4itos": LoadVideoByPath_san4itos,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveFramesToVideoFFmpeg_san4itos": "Save Images to Video (FFmpeg)",
    "ConvertVideoFFmpeg_san4itos": "Convert Video (FFmpeg)",
    "ConvertAudioFFmpeg_san4itos": "Convert Audio (FFmpeg)",
    "LoadVideoByPath_san4itos": "Load Video by Path",
}
