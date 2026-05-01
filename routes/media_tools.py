import os
import shutil
import subprocess
import tempfile
from flask import Blueprint, render_template, request, send_file, jsonify

from routes._helpers import safe_int, safe_float, log_error, NO_FILE_SINGLE

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
        return jsonify({"error": NO_FILE_SINGLE}), 400
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
        return jsonify({"error": NO_FILE_SINGLE}), 400
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
        return jsonify({"error": NO_FILE_SINGLE}), 400
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
        return jsonify({"error": NO_FILE_SINGLE}), 400

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
        return jsonify({"error": NO_FILE_SINGLE}), 400

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
        return jsonify({"error": NO_FILE_SINGLE}), 400

    fps = safe_int(request.form.get("fps"), 15, min_val=1, max_val=30)
    width = safe_int(request.form.get("width"), 480, min_val=100, max_val=1920)

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
            description="Convert subtitles between SRT and WebVTT. Also shift timing by a positive or negative offset.",
            notes=(
                '<p><strong>Pure Python conversion — no FFmpeg or external tools needed.</strong></p>'
                '<p><strong>Supported inputs:</strong> SubRip <code>.srt</code> and WebVTT <code>.vtt</code> files. '
                'BOM-prefixed UTF-8 files are handled. Other formats (ASS/SSA, SUB, etc.) are not supported here — '
                'convert to SRT first using a tool like Aegisub.</p>'
                '<p><strong>Time shift</strong> is in seconds and can be negative. Use to fix subtitles that '
                'are consistently early (positive shift) or late (negative shift) compared to the audio. '
                'For non-uniform drift (subtitles speeding up over time), this tool can\'t help — you need '
                'a re-timing tool.</p>'
            ),
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
        return jsonify({"error": NO_FILE_SINGLE}), 400
    target = request.form.get("target", "srt").lower()
    if target not in ("srt", "vtt"):
        return jsonify({"error": "Unsupported target format."}), 400
    offset = safe_float(request.form.get("offset"), 0.0,
                        min_val=-3600.0, max_val=3600.0)

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

    font_size = safe_int(request.form.get("font_size"), 22, min_val=10, max_val=72)
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


# ── Audio Normalize (FFmpeg loudnorm, EBU R128) ────────

@bp.route("/normalize-audio", methods=["GET", "POST"])
def normalize_audio():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Normalize Audio",
            description="Normalize loudness to a target LUFS level (EBU R128 standard).",
            notes=_ffmpeg_available_notes() + (
                '<p><strong>Loudness targets — pick one that matches where the audio will be played:</strong></p>'
                '<ul style="margin:.4rem 0 .6rem 1.2rem">'
                '<li><strong>-14 LUFS</strong> — Spotify, YouTube, Apple Music, podcasts</li>'
                '<li><strong>-16 LUFS</strong> — most podcast networks (Apple Podcasts spec)</li>'
                '<li><strong>-23 LUFS</strong> — EBU R128 broadcast standard (Europe TV/radio)</li>'
                '<li><strong>-24 LUFS</strong> — ATSC A/85 broadcast (US TV)</li>'
                '</ul>'
            ),
            endpoint="/media/normalize-audio",
            accept=".mp3,.wav,.ogg,.flac,.aac,.m4a,.opus,.wma,.mp4,.mkv,.mov",
            multiple=False,
            options=[
                {
                    "name": "lufs",
                    "label": "Target loudness",
                    "type": "select",
                    "default": "-14",
                    "choices": [
                        {"value": "-14", "label": "-14 LUFS (Streaming, podcasts)"},
                        {"value": "-16", "label": "-16 LUFS (Apple Podcasts)"},
                        {"value": "-23", "label": "-23 LUFS (EBU R128 broadcast)"},
                        {"value": "-24", "label": "-24 LUFS (ATSC A/85 broadcast)"},
                    ],
                },
                {
                    "name": "format",
                    "label": "Output format",
                    "type": "select",
                    "default": "same",
                    "choices": [
                        {"value": "same", "label": "Same as input"},
                        {"value": "mp3",  "label": "MP3 (192 kbps)"},
                        {"value": "wav",  "label": "WAV (lossless)"},
                        {"value": "flac", "label": "FLAC (lossless)"},
                    ],
                },
            ],
            button_text="Normalize",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": NO_FILE_SINGLE}), 400

    lufs_str = request.form.get("lufs", "-14")
    if lufs_str not in ("-14", "-16", "-23", "-24"):
        lufs_str = "-14"
    out_fmt = request.form.get("format", "same").lower()

    in_ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "mp3"
    out_ext = in_ext if out_fmt == "same" else out_fmt

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)
        out_path = os.path.join(tmp, f"output.{out_ext}")

        # loudnorm linear=true: single-pass normalisation; faster and safe
        # for casual use. Two-pass is more accurate but doubles encode time.
        af = f"loudnorm=I={lufs_str}:TP=-1.5:LRA=11:linear=true:print_format=summary"

        args = ["-i", in_path, "-af", af]
        if out_ext == "mp3":
            args += ["-b:a", "192k"]
        elif out_ext == "flac":
            args += ["-c:a", "flac"]
        elif out_ext == "wav":
            args += ["-c:a", "pcm_s16le"]
        args += [out_path]

        _, err = _run_ffmpeg(args, timeout=600)
        if err:
            return jsonify({"error": err}), 400

        with open(out_path, "rb") as fp:
            data = fp.read()

    base = f.filename.rsplit(".", 1)[0]
    mime_map = {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
                "ogg": "audio/ogg", "m4a": "audio/mp4", "opus": "audio/opus"}
    mime = mime_map.get(out_ext, "application/octet-stream")
    return send_file(
        _bytes_io(data),
        mimetype=mime,
        as_attachment=True,
        download_name=f"{base}_normalized.{out_ext}",
    )


# ── Speech to Text (Whisper, optional) ──────────────

try:
    import whisper as _whisper  # type: ignore
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
_whisper_model_cache: dict = {}


@bp.route("/transcribe", methods=["GET", "POST"])
def transcribe():
    if request.method == "GET":
        if HAS_WHISPER:
            status_note = (
                '<p><i class="bi bi-check-circle-fill" style="color:#2ec4b6"></i> '
                '<strong>Whisper is installed.</strong> First run with a given model size '
                'downloads the weights from openai.com (one-time, ~75 MB to ~3 GB depending on size).</p>'
            )
        else:
            status_note = (
                '<p><i class="bi bi-exclamation-triangle-fill" style="color:#ffb703"></i> '
                '<strong>Whisper is not installed.</strong> Run <code>pip install openai-whisper</code> '
                'and restart the server. FFmpeg must also be on PATH.</p>'
            )
        return render_template(
            "upload_tool.html",
            title="Speech to Text (Whisper)",
            description="Transcribe spoken audio or video to text or subtitles, fully local.",
            notes=status_note + (
                '<p><strong>Model size guide</strong> (smaller = faster + lower quality):</p>'
                '<ul style="margin:.4rem 0 .6rem 1.2rem">'
                '<li><strong>tiny</strong> — ~75 MB, very fast, ok for clear English</li>'
                '<li><strong>base</strong> — ~150 MB, recommended starting point</li>'
                '<li><strong>small</strong> — ~500 MB, good multilingual quality</li>'
                '<li><strong>medium</strong> — ~1.5 GB, near-best quality, slow on CPU</li>'
                '<li><strong>large</strong> — ~3 GB, best quality, very slow on CPU</li>'
                '</ul>'
                '<p style="font-size:.9em;color:var(--muted)">Without a GPU, expect roughly '
                '0.5×–2× real-time for tiny/base/small, and 5×–20× real-time for medium/large. '
                'A 10-minute audio file at <code>medium</code> on CPU can take 50+ minutes.</p>'
            ),
            endpoint="/media/transcribe",
            accept=".mp3,.wav,.ogg,.flac,.aac,.m4a,.opus,.mp4,.webm,.mkv,.mov",
            multiple=False,
            options=[
                {
                    "name": "model",
                    "label": "Model size",
                    "type": "select",
                    "default": "base",
                    "choices": [{"value": m, "label": m} for m in WHISPER_MODELS],
                },
                {
                    "name": "language",
                    "label": "Language hint (blank = auto-detect)",
                    "type": "text",
                    "placeholder": "e.g. en, id, ja, es",
                },
                {
                    "name": "format",
                    "label": "Output format",
                    "type": "select",
                    "default": "txt",
                    "choices": [
                        {"value": "txt", "label": "Plain text (.txt)"},
                        {"value": "srt", "label": "SubRip subtitles (.srt)"},
                        {"value": "vtt", "label": "WebVTT subtitles (.vtt)"},
                    ],
                },
            ],
            button_text="Transcribe",
        )

    if not HAS_WHISPER:
        return jsonify({"error": "Whisper is not installed. Run: pip install openai-whisper"}), 400
    if not FFMPEG:
        return jsonify({"error": "Whisper needs FFmpeg on PATH. Install FFmpeg and restart the server."}), 400

    f = request.files.get("files")
    if not f:
        return jsonify({"error": NO_FILE_SINGLE}), 400

    model_size = request.form.get("model", "base")
    if model_size not in WHISPER_MODELS:
        model_size = "base"
    language = (request.form.get("language") or "").strip() or None
    out_fmt = request.form.get("format", "txt").lower()
    if out_fmt not in ("txt", "srt", "vtt"):
        out_fmt = "txt"

    with tempfile.TemporaryDirectory() as tmp:
        in_path = _save_upload(f, tmp)

        try:
            model = _whisper_model_cache.get(model_size)
            if model is None:
                model = _whisper.load_model(model_size)
                _whisper_model_cache[model_size] = model
            result = model.transcribe(in_path, language=language, verbose=False)
        except Exception as e:
            from routes._helpers import log_error as _log
            _log(e, f"whisper {model_size}")
            return jsonify({"error": "Transcription failed. Check the server log; first-time model download may also fail without network access."}), 400

    base = f.filename.rsplit(".", 1)[0]

    if out_fmt == "txt":
        return jsonify({"text": (result.get("text") or "").strip() or "(no speech detected)"})

    # Build SRT / VTT from segments
    segments = result.get("segments") or []

    def fmt_srt_ts(sec: float) -> str:
        if sec < 0: sec = 0.0
        h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec - h * 3600 - m * 60
        whole = int(s); ms = int(round((s - whole) * 1000))
        if ms == 1000: whole += 1; ms = 0
        return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"

    if out_fmt == "srt":
        lines = []
        for i, seg in enumerate(segments, 1):
            lines.append(str(i))
            lines.append(f"{fmt_srt_ts(seg['start'])} --> {fmt_srt_ts(seg['end'])}")
            lines.append((seg.get("text") or "").strip())
            lines.append("")
        body = "\n".join(lines).rstrip() + "\n"
        return send_file(_bytes_io(body.encode("utf-8")), mimetype="text/plain",
                         as_attachment=True, download_name=f"{base}.srt")

    # vtt
    lines = ["WEBVTT", ""]
    for seg in segments:
        s = fmt_srt_ts(seg["start"]).replace(",", ".")
        e = fmt_srt_ts(seg["end"]).replace(",", ".")
        lines.append(f"{s} --> {e}")
        lines.append((seg.get("text") or "").strip())
        lines.append("")
    body = "\n".join(lines).rstrip() + "\n"
    return send_file(_bytes_io(body.encode("utf-8")), mimetype="text/plain",
                     as_attachment=True, download_name=f"{base}.vtt")


# ── helpers ────────────────────────────────────────────

def _bytes_io(data: bytes):
    return _io.BytesIO(data)
