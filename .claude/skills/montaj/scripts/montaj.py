#!/usr/bin/env python3
"""Bovari montaj vositasi — ffmpeg ustidagi yupqa qobiq.

Faqat Python standart kutubxonasi va ffmpeg/ffprobe kerak.
Har bir buyruq: python3 montaj.py <buyruq> --help
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REELS_W, REELS_H = 1080, 1920
VIDEO_ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
AUDIO_ENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"  # Instagram/TikTok uchun -14 LUFS


def run(cmd):
    print("$ " + " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path],
        check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def duration(path):
    return float(probe(path)["format"]["duration"])


def has_audio(path):
    return any(s["codec_type"] == "audio" for s in probe(path)["streams"])


def ensure_parent(path):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)


# ---------- buyruqlar ----------

def cmd_info(a):
    info = probe(a.input)
    fmt = info["format"]
    print(f"Fayl: {a.input}")
    print(f"Davomiylik: {float(fmt['duration']):.2f} s, hajm: {int(fmt['size'])/1e6:.1f} MB")
    for s in info["streams"]:
        if s["codec_type"] == "video":
            fps = s.get("avg_frame_rate", "0/1")
            n, d = (fps.split("/") + ["1"])[:2]
            fps_v = float(n) / float(d) if float(d) else 0
            rot = ""
            for sd in s.get("side_data_list", []):
                if "rotation" in sd:
                    rot = f", rotation {sd['rotation']}"
            print(f"Video: {s['codec_name']} {s['width']}x{s['height']} @ {fps_v:.2f} fps{rot}")
        elif s["codec_type"] == "audio":
            print(f"Audio: {s['codec_name']} {s.get('sample_rate')} Hz, {s.get('channels')} ch")


def cmd_cut(a):
    ensure_parent(a.output)
    cmd = ["ffmpeg", "-y", "-ss", a.start, "-i", a.input]
    if a.end:
        cmd += ["-to", str(_to_sec(a.end) - _to_sec(a.start))]
    cmd += VIDEO_ENC + AUDIO_ENC + [a.output]
    run(cmd)


def _to_sec(t):
    t = str(t)
    if ":" not in t:
        return float(t)
    parts = [float(p) for p in t.split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def _norm_filter(w, h, fps):
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p")


def cmd_concat(a):
    """Turli formatdagi kliplarni bitta o'lchamga keltirib ulaydi."""
    ensure_parent(a.output)
    w, h = map(int, a.size.lower().split("x"))
    cmd = ["ffmpeg", "-y"]
    for f in a.inputs:
        cmd += ["-i", f]
    parts, labels = [], ""
    for i, f in enumerate(a.inputs):
        parts.append(f"[{i}:v]{_norm_filter(w, h, a.fps)}[v{i}]")
        if has_audio(f):
            parts.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
        else:
            d = duration(f)
            parts.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{d}[a{i}]")
        labels += f"[v{i}][a{i}]"
    parts.append(f"{labels}concat=n={len(a.inputs)}:v=1:a=1[v][a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]"]
    cmd += VIDEO_ENC + AUDIO_ENC + [a.output]
    run(cmd)


def cmd_reels(a):
    """Istalgan videoni 1080x1920 (9:16) Reels formatiga o'tkazadi."""
    ensure_parent(a.output)
    W, H = REELS_W, REELS_H
    if a.mode == "crop":
        # markazdan (yoki --x bo'yicha) kesish
        vf =(f"crop='min(iw,ih*{W}/{H})':'min(ih,iw*{H}/{W})':"
              f"'(iw-min(iw,ih*{W}/{H}))*{a.x}':'(ih-min(ih,iw*{H}/{W}))/2',"
              f"scale={W}:{H},setsar=1,fps={a.fps}")
        filt = ["-vf", vf]
    else:
        # blur: orqa fonda xiralashtirilgan kattalashgan kadr, ustida asl kadr
        fc = (f"[0:v]split=2[bg][fg];"
              f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"gblur=sigma=40,eq=brightness=-0.08[bgb];"
              f"[fg]scale={W}:-2:force_original_aspect_ratio=decrease[fgs];"
              f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={a.fps}[v]")
        filt = ["-filter_complex", fc, "-map", "[v]", "-map", "0:a?"]
    cmd = ["ffmpeg", "-y", "-i", a.input] + filt
    if has_audio(a.input):
        cmd += ["-af", LOUDNORM]
    cmd += VIDEO_ENC + AUDIO_ENC + [a.output]
    run(cmd)


def detect_silences(path, noise_db, min_sil):
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-af",
         f"silencedetect=noise={noise_db}dB:d={min_sil}", "-f", "null", "-"],
        capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", res.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", res.stderr)]
    total = duration(path)
    if len(ends) < len(starts):
        ends.append(total)
    return list(zip(starts, ends)), total


def cmd_jumpcut(a):
    """Jimlik joylarini kesib tashlaydi (talking-head / podcast uchun)."""
    ensure_parent(a.output)
    sil, total = detect_silences(a.input, a.noise, a.min_silence)
    keep, cur = [], 0.0
    for s, e in sil:
        s2, e2 = s + a.pad, e - a.pad
        if s2 > cur:
            keep.append((cur, s2))
        cur = max(cur, e2)
    if cur < total:
        keep.append((cur, total))
    keep = [(s, e) for s, e in keep if e - s > 0.05]
    if not keep:
        sys.exit("Hamma joy jim deb topildi — --noise qiymatini pasaytiring (masalan -45).")
    removed = total - sum(e - s for s, e in keep)
    print(f"{len(sil)} ta pauza topildi, {removed:.1f} s olib tashlanadi "
          f"({total:.1f} s → {total - removed:.1f} s)", file=sys.stderr)
    sel = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in keep)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB[v];"
                 f"[0:a]aselect='{sel}',asetpts=N/SR/TB[a]")
        script = fh.name
    try:
        run(["ffmpeg", "-y", "-i", a.input, "-filter_complex_script", script,
             "-map", "[v]", "-map", "[a]"] + VIDEO_ENC + AUDIO_ENC + [a.output])
    finally:
        os.unlink(script)


def cmd_subs(a):
    """SRT subtitrni videoga yondirib qo'yadi (Reels uslubida)."""
    ensure_parent(a.output)
    style = (f"FontName={a.font},FontSize={a.size},Bold=1,"
             f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             f"BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV={a.margin}")
    srt = a.srt.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    vf = f"subtitles='{srt}':force_style='{style}'"
    run(["ffmpeg", "-y", "-i", a.input, "-vf", vf] + VIDEO_ENC + ["-c:a", "copy", a.output])


def cmd_music(a):
    """Fon musiqasini qo'shadi; ovoz bo'lsa musiqa avtomatik pasayadi (ducking)."""
    ensure_parent(a.output)
    d = duration(a.input)
    fade_st = max(d - a.fade, 0)
    mus = (f"[1:a]volume={a.volume},atrim=0:{d},afade=t=in:d=1,"
           f"afade=t=out:st={fade_st}:d={a.fade},aformat=channel_layouts=stereo[m]")
    if has_audio(a.input) and not a.no_duck:
        fc = (f"{mus};[0:a]aformat=channel_layouts=stereo,asplit=2[voice][sc];"
              f"[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
              f"[voice][duck]amix=inputs=2:duration=first:normalize=0,{LOUDNORM}[a]")
    elif has_audio(a.input):
        fc = f"{mus};[0:a][m]amix=inputs=2:duration=first:normalize=0,{LOUDNORM}[a]"
    else:
        fc = f"{mus};[m]{LOUDNORM}[a]"
    run(["ffmpeg", "-y", "-i", a.input, "-stream_loop", "-1", "-i", a.music,
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy"]
        + AUDIO_ENC + ["-shortest", a.output])


def cmd_loudnorm(a):
    ensure_parent(a.output)
    run(["ffmpeg", "-y", "-i", a.input, "-af", LOUDNORM, "-c:v", "copy"]
        + AUDIO_ENC + [a.output])


def cmd_text(a):
    """Videoga matn (hook/sarlavha) qo'yadi, ixtiyoriy vaqt oralig'ida."""
    ensure_parent(a.output)
    txt = a.text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")
    y = {"top": "h*0.12", "center": "(h-text_h)/2", "bottom": "h*0.78"}[a.pos]
    enable = f":enable='between(t,{a.start},{a.end})'" if a.end else ""
    font = shutil.which("fc-match") and subprocess.run(
        ["fc-match", "-f", "%{file}", "DejaVu Sans:bold"],
        capture_output=True, text=True).stdout
    fontopt = f"fontfile='{font}':" if font else ""
    vf = (f"drawtext={fontopt}text='{txt}':fontsize={a.size}:fontcolor=white:"
          f"box=1:boxcolor=black@0.55:boxborderw=24:x=(w-text_w)/2:y={y}{enable}")
    run(["ffmpeg", "-y", "-i", a.input, "-vf", vf] + VIDEO_ENC + ["-c:a", "copy", a.output])


def cmd_frames(a):
    """Kadrlarni rasm qilib chiqaradi — Claude videoni 'ko'rishi' uchun."""
    os.makedirs(a.outdir, exist_ok=True)
    d = duration(a.input)
    step = d / (a.count + 1)
    paths = []
    for i in range(1, a.count + 1):
        t = step * i
        p = os.path.join(a.outdir, f"frame_{i:02d}_{t:06.1f}s.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", a.input,
                        "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", p], check=True)
        paths.append(p)
    print("\n".join(paths))


def cmd_contact(a):
    """Bitta rasmda kadrlar to'ri (contact sheet)."""
    ensure_parent(a.output)
    d = duration(a.input)
    n = a.cols * a.rows
    fps = n / d
    run(["ffmpeg", "-y", "-v", "error", "-i", a.input, "-vf",
         f"fps={fps:.5f},scale=320:-2,tile={a.cols}x{a.rows}", "-frames:v", "1", a.output])


def cmd_transcribe(a):
    """faster-whisper bilan SRT yaratadi (model yuklab olinishi uchun internet kerak)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper o'rnatilmagan: pip install faster-whisper")
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(a.input, language=a.lang, word_timestamps=False)

    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    ensure_parent(a.output)
    with open(a.output, "w", encoding="utf-8") as fh:
        for i, s in enumerate(segs, 1):
            fh.write(f"{i}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n\n")
    print(a.output)


def main():
    p = argparse.ArgumentParser(description="Bovari montaj vositasi (ffmpeg)")
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("info", help="video haqida ma'lumot"); s.add_argument("input")
    s.set_defaults(f=cmd_info)

    s = sp.add_parser("cut", help="bo'lak kesish")
    s.add_argument("input"); s.add_argument("output")
    s.add_argument("--start", default="0"); s.add_argument("--end")
    s.set_defaults(f=cmd_cut)

    s = sp.add_parser("concat", help="kliplarni ulash")
    s.add_argument("output"); s.add_argument("inputs", nargs="+")
    s.add_argument("--size", default="1080x1920"); s.add_argument("--fps", default="30")
    s.set_defaults(f=cmd_concat)

    s = sp.add_parser("reels", help="9:16 Reels formatiga o'tkazish")
    s.add_argument("input"); s.add_argument("output")
    s.add_argument("--mode", choices=["blur", "crop"], default="crop")
    s.add_argument("--x", type=float, default=0.5, help="crop: gorizontal joy 0..1 (0.5=markaz)")
    s.add_argument("--fps", default="30")
    s.set_defaults(f=cmd_reels)

    s = sp.add_parser("jumpcut", help="pauzalarni kesish")
    s.add_argument("input"); s.add_argument("output")
    s.add_argument("--noise", type=float, default=-35, help="jimlik chegarasi, dB")
    s.add_argument("--min-silence", type=float, default=0.5, help="eng qisqa pauza, s")
    s.add_argument("--pad", type=float, default=0.12, help="kesimlar atrofida zaxira, s")
    s.set_defaults(f=cmd_jumpcut)

    s = sp.add_parser("subs", help="SRT subtitrni yondirish")
    s.add_argument("input"); s.add_argument("srt"); s.add_argument("output")
    s.add_argument("--font", default="DejaVu Sans"); s.add_argument("--size", type=int, default=14)
    s.add_argument("--margin", type=int, default=70)
    s.set_defaults(f=cmd_subs)

    s = sp.add_parser("music", help="fon musiqasi + ducking")
    s.add_argument("input"); s.add_argument("music"); s.add_argument("output")
    s.add_argument("--volume", type=float, default=0.25)
    s.add_argument("--fade", type=float, default=2.0)
    s.add_argument("--no-duck", action="store_true")
    s.set_defaults(f=cmd_music)

    s = sp.add_parser("loudnorm", help="ovozni -14 LUFS ga normallashtirish")
    s.add_argument("input"); s.add_argument("output"); s.set_defaults(f=cmd_loudnorm)

    s = sp.add_parser("text", help="matn/hook qo'yish")
    s.add_argument("input"); s.add_argument("output"); s.add_argument("--text", required=True)
    s.add_argument("--pos", choices=["top", "center", "bottom"], default="top")
    s.add_argument("--size", type=int, default=64)
    s.add_argument("--start", default="0"); s.add_argument("--end")
    s.set_defaults(f=cmd_text)

    s = sp.add_parser("frames", help="kadrlarni rasmga chiqarish")
    s.add_argument("input"); s.add_argument("outdir"); s.add_argument("--count", type=int, default=6)
    s.set_defaults(f=cmd_frames)

    s = sp.add_parser("contact", help="kadrlar to'ri (bitta rasm)")
    s.add_argument("input"); s.add_argument("output")
    s.add_argument("--cols", type=int, default=4); s.add_argument("--rows", type=int, default=3)
    s.set_defaults(f=cmd_contact)

    s = sp.add_parser("transcribe", help="ovozdan SRT (faster-whisper)")
    s.add_argument("input"); s.add_argument("output")
    s.add_argument("--model", default="small"); s.add_argument("--lang", default="uz")
    s.set_defaults(f=cmd_transcribe)

    a = p.parse_args()
    try:
        a.f(a)
    except subprocess.CalledProcessError as e:
        sys.exit(f"ffmpeg xatosi (kod {e.returncode})")


if __name__ == "__main__":
    main()
