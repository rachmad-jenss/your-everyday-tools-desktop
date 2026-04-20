import os
import shutil
import subprocess
import tempfile
from flask import Blueprint, render_template, request, send_file, jsonify

bp = Blueprint("media", __name__)

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

AUDIO_FORMATS = ["mp3", "wav", "ogg", "flac", "aac", "m4a", "opus"]
VIDEO_FORMATS = ["mp4", "webm", "mkv", "mov", "avi"]

FFMPEG_INSTALL_NOTE = (
    '<p><strong>FFmpeg is required for this tool.</strong></p>'
    '<details><summary>How to install FFmpeg</summary>'
    '<p><strong>Windows:</strong> Download from '
    '<a href="https://www.gyan.dev/ffmpeg/builds/" target="_blank">gyan.dev</a> or '
    '<a href="https://github.com/BtbN/FFmpeg-Builds/releases" target="_blank">BtbN builds</a>, '
    'extract, and add the <code>bin</code> folder to your PATH.</p>'
    '<p><strong>macOS:</strong> <code>brew install ffmpeg</code></p>'
    '<p><strong>Linux:</strong> <code>sudo apt install ffmpeg</code> (Debian/Ubuntu) '
    'or <code>sudo dnf install ffmpeg</code> (Fedora).</p>'
    '<p>Restart the server after installing so the new PATH is picked up.</p>'
    '</details>'
)


def _ffmpeg_available_notes():
    if FFMPEG:
        return (
            f'<p><i class="bi bi-check-circle-fill" style="color:#2ec4b6"></i> '
            f'<strong>FFmpeg detected:</strong> <code>{FFMPEG}</code></p>'
        )
    return (
        '<p><i class="bi bi-exclamation-triangle-fill" style="color:#ffb703"></i> '
        '<strong>FFmpeg was not found on PATH.</strong> This tool will not work until FFmpeg is installed.</p>'
        + FFMPEG_INSTALL_NOTE
    )


def _run_ffmpeg(args: list[str], timeout: int = 180):
    if not FFMPEG:
        return None, "FFmpeg is not installed or not on PATH."
    try:
        proc = subprocess.run(
            [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + args,
            capture_output=True, timeout=timeout,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace") or "unknown error"
            return None, f"FFmpeg failed: {err[:500]}"
        return proc, None
    except subprocess.TimeoutExpired:
        return None, "FFmpeg timed out."


def _save_upload(file_storage, tmpdir: str) -> str:
    path = os.path.join(tmpdir, "input_" + file_storage.filename.replace("/", "_").replace("\\", "_"))
    file_storage.save(path)
    return path


# ── Audio convert ──────────────────────────────────────

@bp.route("/convert-audio", methods=["GET", "POST"])
def convert_audio():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Convert Audio",
            description="Convert between common audio formats using FFmpeg.",
            notes=_ffmpeg_available_notes(),
            endpoint="/media/convert-audio",
            accept=".mp3,.wav,.ogg,.flac,.aac,.m4a,.opus,.wma",
            multiple=False,
            options=[
                {
                    "name": "format",
                    "label": "Target format",
                    "type": "select",
                    "default": "mp3",
                    "choices": [{"value": f, "label": f.upper()} for f in AUDIO_FORMATS],
                },
                {
                    "name": "bitrate",
                    "label": "Bitrate",
                    "type": "select",
                    "default": "192k",
                    "choices": [
                        {"value": "96k", "label": "96 kbps"},
                        {"value": "128k", "label": "128 kbps"},
                        {"value": "192k", "label": "192 kbps"},
                        {"value": "256k", "label": "256 kbps"},
                        {"value": "320k", "label": "320 kbps"},
                    ],
                },
            ],
            button_text="Convert",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    fmt = request.form.get("format", "mp3")
    if fmt not in AUDIO_FORMATS:
        return jsonify({"error": "Unsupported target format."}), 400
    bitrate = request.form.get("bitrate", "192k")

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, f"output.{fmt}")

        args = ["-i", in_path]
        if fmt == "wav" or fmt == "flac":
            args += [out_path]
        else:
            args += ["-b:a", bitrate, out_path]

        _, err = _run_ffmpeg(args)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        mimetype=f"audio/{fmt}",
        as_attachment=True,
        download_name=f"{base}.{fmt}",
    )


# ── Video convert ──────────────────────────────────────

@bp.route("/convert-video", methods=["GET", "POST"])
def convert_video():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Convert Video",
            description="Convert between common video formats using FFmpeg.",
            notes=_ffmpeg_available_notes(),
            endpoint="/media/convert-video",
            accept=".mp4,.webm,.mkv,.mov,.avi,.flv,.wmv",
            multiple=False,
            options=[
                {
                    "name": "format",
                    "label": "Target format",
                    "type": "select",
                    "default": "mp4",
                    "choices": [{"value": f, "label": f.upper()} for f in VIDEO_FORMATS],
                },
            ],
            button_text="Convert",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    fmt = request.form.get("format", "mp4")
    if fmt not in VIDEO_FORMATS:
        return jsonify({"error": "Unsupported target format."}), 400

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, f"output.{fmt}")

        args = ["-i", in_path]
        if fmt == "webm":
            args += ["-c:v", "libvpx-vp9", "-c:a", "libopus", out_path]
        elif fmt == "mp4":
            args += ["-c:v", "libx264", "-c:a", "aac", "-preset", "medium", out_path]
        else:
            args += [out_path]

        _, err = _run_ffmpeg(args, timeout=600)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        mimetype=f"video/{fmt}",
        as_attachment=True,
        download_name=f"{base}.{fmt}",
    )


# ── Extract audio from video ───────────────────────────

@bp.route("/extract-audio", methods=["GET", "POST"])
def extract_audio():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Extract Audio",
            description="Extract the audio track from a video file.",
            notes=_ffmpeg_available_notes(),
            endpoint="/media/extract-audio",
            accept=".mp4,.webm,.mkv,.mov,.avi,.flv,.wmv",
            multiple=False,
            options=[
                {
                    "name": "format",
                    "label": "Audio format",
                    "type": "select",
                    "default": "mp3",
                    "choices": [
                        {"value": "mp3", "label": "MP3"},
                        {"value": "wav", "label": "WAV"},
                        {"value": "ogg", "label": "OGG"},
                        {"value": "m4a", "label": "M4A (AAC)"},
                    ],
                },
            ],
            button_text="Extract",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    fmt = request.form.get("format", "mp3")
    if fmt not in ("mp3", "wav", "ogg", "m4a"):
        return jsonify({"error": "Unsupported audio format."}), 400

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, f"output.{fmt}")

        args = ["-i", in_path, "-vn"]
        if fmt == "mp3":
            args += ["-b:a", "192k"]
        elif fmt == "m4a":
            args += ["-c:a", "aac", "-b:a", "192k"]
        args += [out_path]

        _, err = _run_ffmpeg(args)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        mimetype=f"audio/{fmt}",
        as_attachment=True,
        download_name=f"{base}.{fmt}",
    )


# ── Trim media ─────────────────────────────────────────

@bp.route("/trim", methods=["GET", "POST"])
def trim():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Trim Media",
            description="Trim an audio or video file by start and end time (HH:MM:SS or seconds).",
            notes=_ffmpeg_available_notes(),
            endpoint="/media/trim",
            accept=".mp4,.webm,.mkv,.mov,.avi,.mp3,.wav,.ogg,.flac,.m4a",
            multiple=False,
            options=[
                {
                    "name": "start",
                    "label": "Start (e.g. 0 or 00:00:05)",
                    "type": "text",
                    "default": "0",
                },
                {
                    "name": "end",
                    "label": "End (leave blank for end-of-file)",
                    "type": "text",
                    "default": "",
                },
            ],
            button_text="Trim",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400

    start = (request.form.get("start") or "0").strip()
    end = (request.form.get("end") or "").strip()
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "mp4"

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, f"output.{ext}")

        args = ["-i", in_path, "-ss", start]
        if end:
            args += ["-to", end]
        args += ["-c", "copy", out_path]

        _, err = _run_ffmpeg(args)
        if err:
            # Re-encode fallback if stream copy fails (e.g. keyframe issues)
            args = ["-i", in_path, "-ss", start]
            if end:
                args += ["-to", end]
            args += [out_path]
            _, err = _run_ffmpeg(args, timeout=600)
            if err:
                return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        as_attachment=True,
        download_name=f"{base}_trimmed.{ext}",
    )


# ── Compress video ─────────────────────────────────────

@bp.route("/compress-video", methods=["GET", "POST"])
def compress_video():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Compress Video",
            description="Reduce video file size by re-encoding with H.264 at a chosen quality level.",
            notes=_ffmpeg_available_notes(),
            endpoint="/media/compress-video",
            accept=".mp4,.webm,.mkv,.mov,.avi,.flv",
            multiple=False,
            options=[
                {
                    "name": "quality",
                    "label": "Quality (CRF)",
                    "type": "select",
                    "default": "28",
                    "choices": [
                        {"value": "23", "label": "High (23 – larger, better)"},
                        {"value": "28", "label": "Medium (28 – balanced)"},
                        {"value": "32", "label": "Low (32 – smaller)"},
                        {"value": "36", "label": "Very low (36 – smallest)"},
                    ],
                },
                {
                    "name": "preset",
                    "label": "Encoding preset",
                    "type": "select",
                    "default": "medium",
                    "choices": [
                        {"value": "ultrafast", "label": "Ultrafast (largest)"},
                        {"value": "fast", "label": "Fast"},
                        {"value": "medium", "label": "Medium"},
                        {"value": "slow", "label": "Slow (smallest)"},
                    ],
                },
            ],
            button_text="Compress",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400

    crf = request.form.get("quality", "28")
    preset = request.form.get("preset", "medium")
    if crf not in ("23", "28", "32", "36"):
        crf = "28"
    if preset not in ("ultrafast", "fast", "medium", "slow"):
        preset = "medium"

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, "output.mp4")

        args = ["-i", in_path, "-c:v", "libx264", "-crf", crf, "-preset", preset, "-c:a", "aac", "-b:a", "128k", out_path]

        _, err = _run_ffmpeg(args, timeout=900)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        mimetype="video/mp4",
        as_attachment=True,
        download_name=f"{base}_compressed.mp4",
    )


# ── Video to GIF ───────────────────────────────────────

@bp.route("/video-to-gif", methods=["GET", "POST"])
def video_to_gif():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Video to GIF",
            description="Convert a short video clip into an animated GIF.",
            notes=_ffmpeg_available_notes()
                + "<p><strong>Tip:</strong> keep clips under ~10 seconds — GIFs are large.</p>",
            endpoint="/media/video-to-gif",
            accept=".mp4,.webm,.mkv,.mov,.avi",
            multiple=False,
            options=[
                {"name": "fps", "label": "FPS", "type": "number", "default": 15, "min": 1, "max": 30},
                {"name": "width", "label": "Width (px)", "type": "number", "default": 480, "min": 100, "max": 1920},
                {"name": "start", "label": "Start (seconds or HH:MM:SS)", "type": "text", "default": "0"},
                {"name": "duration", "label": "Duration (seconds, blank for all)", "type": "text", "default": "5"},
            ],
            button_text="Convert",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400

    try:
        fps = max(1, min(30, int(request.form.get("fps", 15))))
        width = max(100, min(1920, int(request.form.get("width", 480))))
    except ValueError:
        return jsonify({"error": "FPS and width must be integers."}), 400

    start = (request.form.get("start") or "0").strip()
    duration = (request.form.get("duration") or "").strip()

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, "output.gif")

        args = ["-ss", start]
        if duration:
            args += ["-t", duration]
        args += [
            "-i", in_path,
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos",
            out_path,
        ]

        _, err = _run_ffmpeg(args, timeout=300)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        mimetype="image/gif",
        as_attachment=True,
        download_name=f"{base}.gif",
    )


# ── Subtitle convert / shift ───────────────────────────

import io as _io
import re as _re


def _parse_ts(s: str) -> float:
    s = s.strip()
    if not s:
        raise ValueError("empty timestamp")
    s = s.replace(",", ".")
    parts = s.split(":")
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + float(sec)
    if len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + float(sec)
    return float(parts[0])


def _fmt_srt(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec - h * 3600 - m * 60
    whole = int(s)
    ms = int(round((s - whole) * 1000))
    if ms == 1000:
        whole += 1; ms = 0
    return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"


def _fmt_vtt(sec: float) -> str:
    return _fmt_srt(sec).replace(",", ".")


_CUE_RE = _re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
)


def _parse_subs(text: str):
    """Parse SRT or WebVTT. Returns list of (start_sec, end_sec, text)."""
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cues = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.upper().startswith("WEBVTT"):
            i += 1
            continue
        m = _CUE_RE.search(line)
        if not m:
            i += 1
            continue
        try:
            start = _parse_ts(m.group(1))
            end = _parse_ts(m.group(2))
        except (ValueError, IndexError):
            i += 1
            continue
        i += 1
        body = []
        while i < len(lines) and lines[i].strip() != "":
            body.append(lines[i])
            i += 1
        cues.append((start, end, "\n".join(body).strip()))
        while i < len(lines) and lines[i].strip() == "":
            i += 1
    return cues


def _write_srt(cues) -> str:
    parts = []
    for idx, (start, end, body) in enumerate(cues, 1):
        parts.append(f"{idx}\n{_fmt_srt(start)} --> {_fmt_srt(end)}\n{body}\n")
    return "\n".join(parts).rstrip() + "\n"


def _write_vtt(cues) -> str:
    parts = ["WEBVTT", ""]
    for start, end, body in cues:
        parts.append(f"{_fmt_vtt(start)} --> {_fmt_vtt(end)}")
        parts.append(body)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


@bp.route("/subtitle-convert", methods=["GET", "POST"])
def subtitle_convert():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Convert Subtitles",
            description="Convert subtitles between SRT and WebVTT. Also shift timing by a positive or negative offset (seconds).",
            endpoint="/media/subtitle-convert",
            accept=".srt,.vtt",
            multiple=False,
            options=[
                {
                    "name": "target",
                    "label": "Target format",
                    "type": "select",
                    "default": "srt",
                    "choices": [
                        {"value": "srt", "label": "SubRip (.srt)"},
                        {"value": "vtt", "label": "WebVTT (.vtt)"},
                    ],
                },
                {
                    "name": "offset",
                    "label": "Time shift (seconds, can be negative, e.g. -1.5)",
                    "type": "text",
                    "default": "0",
                },
            ],
            button_text="Convert",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    target = request.form.get("target", "srt").lower()
    if target not in ("srt", "vtt"):
        return jsonify({"error": "Unsupported target format."}), 400
    try:
        offset = float(request.form.get("offset", "0"))
    except ValueError:
        return jsonify({"error": "Offset must be a number."}), 400

    raw = f.read().decode("utf-8-sig", errors="replace")
    cues = _parse_subs(raw)
    if not cues:
        return jsonify({"error": "No subtitle cues found in that file."}), 400

    if offset:
        cues = [(max(0.0, s + offset), max(0.0, e + offset), t) for s, e, t in cues]

    out_text = _write_srt(cues) if target == "srt" else _write_vtt(cues)
    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(out_text.encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"{base}.{target}",
    )


# ── Burn subtitles ─────────────────────────────────────

@bp.route("/burn-subtitles", methods=["GET", "POST"])
def burn_subtitles():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Burn Subtitles",
            description="Permanently render a subtitle file onto a video (hardsub).",
            notes=_ffmpeg_available_notes()
                + "<p>Upload the <strong>video</strong> as the main file, and select the <strong>.srt/.vtt</strong> file below.</p>",
            endpoint="/media/burn-subtitles",
            accept=".mp4,.webm,.mkv,.mov,.avi",
            multiple=False,
            options=[
                {"type": "file", "name": "subtitle",
                 "label": "Subtitle file (.srt or .vtt)",
                 "accept": ".srt,.vtt", "required": True},
                {
                    "name": "font_size",
                    "label": "Font size",
                    "type": "number",
                    "default": 22,
                    "min": 10,
                    "max": 72,
                },
                {
                    "name": "quality",
                    "label": "Output quality (CRF)",
                    "type": "select",
                    "default": "23",
                    "choices": [
                        {"value": "18", "label": "Best (18)"},
                        {"value": "23", "label": "Good (23)"},
                        {"value": "28", "label": "Smaller (28)"},
                    ],
                },
            ],
            button_text="Burn subtitles",
        )

    if not FFMPEG:
        return jsonify({"error": "FFmpeg is not installed or not on PATH."}), 400

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No video uploaded."}), 400
    sub = request.files.get("subtitle")
    if not sub or not sub.filename:
        return jsonify({"error": "Please upload a subtitle file."}), 400

    try:
        font_size = max(10, min(72, int(request.form.get("font_size", 22))))
    except ValueError:
        font_size = 22
    crf = request.form.get("quality", "23")
    if crf not in ("18", "23", "28"):
        crf = "23"

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        sub_ext = sub.filename.rsplit(".", 1)[-1].lower() if "." in sub.filename else "srt"
        sub_path = os.path.join(tmp, f"subs.{sub_ext}")
        sub.save(sub_path)
        out_path = os.path.join(tmp, "output.mp4")

        sub_arg = sub_path.replace("\\", "/").replace(":", "\\:")
        vf = (
            f"subtitles='{sub_arg}':force_style='Fontsize={font_size},"
            f"OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0'"
        )

        args = [
            "-i", in_path,
            "-vf", vf,
            "-c:v", "libx264", "-crf", crf, "-preset", "medium",
            "-c:a", "copy",
            out_path,
        ]
        _, err = _run_ffmpeg(args, timeout=1200)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    return send_file(
        _bytes_io(data),
        mimetype="video/mp4",
        as_attachment=True,
        download_name=f"{base}_subs.mp4",
    )


# ── helpers ────────────────────────────────────────────

def _bytes_io(data: bytes):
    return _io.BytesIO(data)
