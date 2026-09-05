# Save Images to Video (FFmpeg) for ComfyUI

A powerful custom node suite for ComfyUI that lets you save image sequences as videos, convert existing videos, audio muxing, and convert audio using FFmpeg.  

It offers extensive codec support, fine‑grained audio control, high performance, flexible metadata embedding, and full customisation via user‑supplied FFmpeg options.

![Save Images to Video](./screenshots/save-images.png)
![Convert Video](./screenshots/convert.png)
![Workflow Example](./screenshots/workflow.png)

## Features

- **Save image frames** to a video file with adjustable frame rate, codec, pixel format, CRF, and custom options.
- **Convert videos** between formats, re‑encode with different settings, or simply remux.
- **Convert audios** between formats or re-encode with different settings.
- **Audio handling**:
  - Attach audio to videos saved from image frames.
  - Copy, replace, or remove audio tracks when converting videos.
  - Direct‑path mode for fast re‑encoding when using the **Load Video by Path** node.
- **Metadata embedding** with multiple strategies (raw JSON, base64, platform‑aware).
- **Custom options** can be appended via the `output_file_opt` field.
- **Skip** options for experienced users who want to override settings entirely via custom options.
- **Timeout control** to prevent hanging processes.

## Installation

1. **Clone the repository:**
   ```bash
   cd ComfyUI/custom_nodes/
   git clone https://github.com/San4itos/ComfyUI-Save-Images-as-Video.git 
   cd ComfyUI-Save-Images-as-Video
   pip install -r requirements.txt
   ```

2. **Get FFmpeg:**
   The node will automatically find FFmpeg in the following order:
   1. **Custom Path:** Edit `ffmpeg_config.ini` in the node's folder to point to your FFmpeg installation directory.
   2. **Portable:** Place the `ffmpeg` executable inside the `ComfyUI-Save-Images-as-Video/ffmpeg_bin/` folder.
   3. **System PATH:** If FFmpeg is installed and accessible in your system's PATH, it will be used.

After installation, the nodes appear in the **San4itos** category in ComfyUI's node menu.

## Nodes Overview

| Node | Description | Required Inputs | Optional Inputs |
|------|-------------|-----------------|-----------------|
| **Save Images to Video (FFmpeg)** | Creates a video from image frames. | `images`, `filename_prefix`, `fps`, `codec`, `pixel_format`, `crf`, `output_format` | `audio`, `audio_codec`, `audio_bitrate`, `output_file_opt`, `timeout`, `metadata` |
| **Convert Video (FFmpeg)** | Re‑encodes or remuxes an existing video. | `video`, `filename_prefix`, `codec`, `pixel_format`, `crf`, `output_format`, `audio_handling` | `audio`, `audio_codec`, `audio_bitrate`, `output_file_opt`, `timeout`, `metadata` |
| **Convert Audio (FFmpeg)** | Re-encodes an audio. | `audio`, `filename_prefix`, `bitrate`, `output_format` | `output_file_opt`, `timeout`, `metadata` |
| **Load Video by Path** | Loads a video file **without** converting it to images first. The output is a direct path wrapper that is only compatible with the **Convert Video** node for much faster re‑encoding. | `video_file` (file picker) | – |

### `skip` and `copy` Values

- **`skip`** – When selected, the corresponding FFmpeg flag is **omitted** from the command. This is useful when you want to define those options yourself via `output_file_opt`. For `crf`, `-1` means `skip`. For `audio_bitrate` and `bitrate`, `0` means `skip`.
- **`copy`** – This tells FFmpeg to **copy** the stream without re‑encoding (`-c:v copy` for video and `-c:a copy` for audio), which is fast and lossless. The **Save Images to Video (FFmpeg)** node does not offer `copy` because it always encodes new video.

### Audio Muxing

- **Save Images to Video:**  An optional audio input can be attached, which will be added to the produced video with the `-shortest` flag used to trim the longer between video and audio to fit the shorter.
- **Convert Video:** Four modes are available:
  - `copy original`: Keeps the original audio track(s).
  - `remove audio`: Strips all audio.
  - `replace with new`: Replaces existing audio with the audio you supply with the first track used if the audio contains multiple tracks and the `-shortest` flag used to trim the longer between video and audio to fit the shorter. This mode is only supported when the video comes from ComfyUI's default loader. If the video comes from **Load Video by Path**, audio replacement is not possible and falls back to `copy original`.
  - `skip`: Disables all audio‑related options, letting you control audio via `output_file_opt`.

### Bitrate Settings

The **audio bitrate** in **Save Images to Video (FFmpeg)** and **Convert Video (FFmpeg)** nodes and **bitrate** in **Convert Audio (FFmpeg)** node takes an integer value in knps:
- If set to `0`, the `-b:a` flag is omitted.  
- Otherwise, `-b:a <value>k` is added (e.g., `192` → `-b:a 192k`).

### Custom FFmpeg Options

The `output_file_opt` field allows you to append **any** FFmpeg flags directly.  
- One option per line or space‑separated.  
- Supports both **value‑taking** flags (e.g., `-preset slow`) and **valueless** flags (e.g., `-an`)
- User‑supplied options **override** any GUI‑set values with warnings logged).  
- Example:
  ```
  -c:v libsvtav1
  -svtav1-params lossless=1
  -preset -2
  -c:a flac
  ```
- If a flag does not start with `-`, a warning is issued, but the token is still processed.

### Timeout

The `timeout` parameter (in seconds) limits how long FFmpeg is allowed to run. Default is 300 seconds. Increase it for long encodes.

### Metadata Embedding

The `metadata` input offers five strategies:

| Strategy | Behaviour |
|----------|-----------|
| `original` | Embed raw JSON string as `-metadata comment='{...}'` |
| `original, non‑Windows only` | Same as `original`, but **disabled on Windows** (to avoid command‑line length issues) |
| `base64` | Encode JSON in Base64 and embed as `-metadata comment=b64:...`, which is safer for special characters |
| `base64, non‑Windows only` | Same as `base64`, but **disabled on Windows** (to avoid command‑line length issues) |
| `none` | No metadata embedded |

## Video Input Performance of Convert Video

The **Convert Video (FFmpeg)** node works with two types of video inputs:

- **ComfyUI's default loader**: It is first decoded into individual images and audio, which is memory‑intensive and slower.  
- **Load Video by Path node**: The original file path is passed directly to FFmpeg. This avoids intermediate image extraction and significantly speeds up conversion, especially for large videos. However, `replace with new` audio muxing is not supported, and the **Load Video by Path** node's output is not compatible with nodes other than **Convert Video (FFmpeg)**.

## Output

- All generated videos are saved in ComfyUI's output directory (typically `ComfyUI/output/`).
- All generated audios are saved in the subfolder `audio` ComfyUI's output directory (typically `ComfyUI/output/audio/`).
- You can preview videos in the ComfyUI queue view by pressing `Q`.

## License

This project is licensed under [GNU GENERAL PUBLIC LICENSE Version 3](LICENSE).

