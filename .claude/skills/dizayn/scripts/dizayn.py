#!/usr/bin/env python3
"""Bovari dizayn toolkit: HTML/CSS -> PNG postlar, bannerlar, karusellar.

Buyruqlar:
  formats                         — o'lchamlar ro'yxati
  fonts                           — o'rnatilgan shriftlar
  templates                       — shablonlar va ularning maydonlari
  make TEMPLATE out.png [--format post] [--set key=qiymat ...]
  render in.html out.png [--format post | --size 1080x1350] [--scale 1]
  carousel dir_or_html... outdir [--format post]  — bir nechta HTML -> 01.png, 02.png...
  icon NAME out.svg [--set lucide|tabler] [--color #fff] [--stroke 2] [--size 96]
  cutout in.jpg out.png [--model isnet-general-use|u2net_human_seg|u2netp]
  palette in.jpg [--n 6]          — rasmdan rang palitrasi
  sheet out.jpg a.png b.png ...   — preview to'ri (ko'z bilan tekshirish uchun)

HTML ichida {{ASSETS}} — assets papkasining absolyut yo'li (base.css, shriftlar, ikonlar).
"""
import argparse, html, os, re, shutil, subprocess, sys, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
TEMPLATES = ASSETS / "templates"
ICON_CACHE = ASSETS / "icons"
RENDER_JS = Path(__file__).resolve().parent / "render.js"

FORMATS = {
    "post":      (1080, 1350, "Instagram feed 4:5 (asosiy)"),
    "square":    (1080, 1080, "Instagram/Facebook 1:1"),
    "story":     (1080, 1920, "Stories / Reels cover 9:16"),
    "reels-cover": (1080, 1920, "Reels cover (markaziy 1080x1440 grid'da ko'rinadi)"),
    "telegram":  (1280, 720,  "Telegram post rasmi 16:9"),
    "youtube":   (1280, 720,  "YouTube thumbnail"),
    "banner":    (1920, 1080, "Keng banner / prezentatsiya 16:9"),
    "fb-cover":  (1640, 624,  "Facebook cover"),
    "linkedin":  (1200, 627,  "LinkedIn / OG image"),
    "a4":        (2480, 3508, "A4 300dpi (print)"),
    "billboard": (3000, 1000, "3:1 tashqi banner"),
}

ICON_SETS = {
    "lucide": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{n}.svg",
    "tabler": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{n}.svg",
    "tabler-filled": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/filled/{n}.svg",
}


def size_of(a):
    if getattr(a, "size", None):
        w, h = a.size.lower().split("x")
        return int(w), int(h)
    f = getattr(a, "format", None) or "post"
    if f not in FORMATS:
        sys.exit(f"Noma'lum format: {f}. `formats` buyrug'ini ko'ring.")
    return FORMATS[f][:2]


def fill(text, values):
    text = text.replace("{{ASSETS}}", ASSETS.as_uri())
    def rep(m):
        key, default = m.group(1), (m.group(2) or "")
        v = values.get(key, default)
        return v  # HTML ruxsat: <span class="hl">...</span> ishlatish mumkin
    return re.sub(r"\{\{(\w+)(?:\|([^}]*))?\}\}", rep, text)


def render_html(src_html_text, out, w, h, scale):
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, dir=str(ASSETS)) as t:
        t.write(src_html_text)
        tmp = t.name
    try:
        subprocess.run(["node", str(RENDER_JS), tmp, str(out), str(w), str(h), str(scale)], check=True)
    finally:
        os.unlink(tmp)
    print(f"✓ {out}  ({int(w*scale)}x{int(h*scale)})")


def template_fields(path):
    return sorted(set(re.findall(r"\{\{(\w+)(?:\|[^}]*)?\}\}", path.read_text())) - {"ASSETS"})


# ---------- buyruqlar ----------
def cmd_formats(a):
    for k, (w, h, d) in FORMATS.items():
        print(f"{k:12} {w}x{h:<6} {d}")


def cmd_fonts(a):
    for f in sorted((ROOT / "fonts").glob("*.ttf")):
        print(f.stem)
    print("\nTizimda ham: Inter, Inter Display, JetBrains Mono, Noto Color Emoji")


def cmd_templates(a):
    for t in sorted(TEMPLATES.glob("*.html")):
        first = t.read_text().split("\n", 1)[0]
        desc = re.sub(r"<!--\s*|\s*-->", "", first)
        print(f"{t.stem:10} {desc}\n           maydonlar: {', '.join(template_fields(t))}")


def cmd_make(a):
    t = TEMPLATES / f"{a.template}.html"
    if not t.exists():
        sys.exit(f"Shablon yo'q: {a.template}. `templates` ni ko'ring.")
    values = {}
    for kv in a.set or []:
        k, _, v = kv.partition("=")
        if k == "image" and v and not v.startswith(("http", "file:", "data:")):
            v = Path(v).resolve().as_uri()
        values[k] = v
    w, h = size_of(a)
    render_html(fill(t.read_text(), values), a.out, w, h, a.scale)


def cmd_render(a):
    w, h = size_of(a)
    render_html(fill(Path(a.input).read_text(), {}), a.out, w, h, a.scale)


def cmd_carousel(a):
    files = []
    for p in a.inputs:
        p = Path(p)
        files += sorted(p.glob("*.html")) if p.is_dir() else [p]
    w, h = size_of(a)
    for i, f in enumerate(files, 1):
        render_html(fill(f.read_text(), {"N": str(i), "TOTAL": str(len(files))}),
                    Path(a.outdir) / f"{i:02d}.png", w, h, a.scale)


def cmd_icon(a):
    ICON_CACHE.mkdir(parents=True, exist_ok=True)
    cache = ICON_CACHE / f"{a.set}-{a.name}.svg"
    if not cache.exists():
        url = ICON_SETS[a.set].format(n=a.name)
        try:
            cache.write_bytes(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            sys.exit(f"Ikonka topilmadi: {a.name} ({a.set}) — {e}. Nomlar: lucide.dev/icons, tabler.io/icons")
    svg = cache.read_text()
    svg = re.sub(r'width="\d+"', f'width="{a.size}"', svg, count=1)
    svg = re.sub(r'height="\d+"', f'height="{a.size}"', svg, count=1)
    svg = svg.replace("currentColor", a.color)
    svg = re.sub(r'stroke-width="[\d.]+"', f'stroke-width="{a.stroke}"', svg, count=1)
    Path(a.out).write_text(svg)
    print(f"✓ {a.out}")


def cmd_cutout(a):
    from rembg import remove, new_session
    from PIL import Image
    out = remove(Image.open(a.input), session=new_session(a.model))
    bbox = out.getbbox()
    if bbox and not a.no_trim:
        out = out.crop(bbox)
    out.save(a.out)
    print(f"✓ {a.out}  {out.size[0]}x{out.size[1]}")


def cmd_palette(a):
    from PIL import Image
    im = Image.open(a.input).convert("RGB")
    im.thumbnail((300, 300))
    q = im.quantize(colors=a.n, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: a.n * 3]
    counts = sorted(q.getcolors(), reverse=True)
    for cnt, idx in counts:
        r, g, b = pal[idx * 3: idx * 3 + 3]
        print(f"#{r:02X}{g:02X}{b:02X}  {cnt * 100 // sum(c for c, _ in counts):3d}%")


def cmd_sheet(a):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in a.images]
    th = 600
    ims = [im.resize((int(im.width * th / im.height), th)) for im in ims]
    rows = [ims[i:i + a.cols] for i in range(0, len(ims), a.cols)]
    W = max(sum(im.width for im in r) + 20 * (len(r) + 1) for r in rows)
    sheet = Image.new("RGB", (W, len(rows) * th + (len(rows) + 1) * 20), "#222")
    for ri, r in enumerate(rows):
        x = 20
        for im in r:
            sheet.paste(im, (x, 20 + ri * (th + 20))); x += im.width + 20
    sheet.save(a.out, quality=90)
    print(f"✓ {a.out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)

    def sized(sp):
        sp.add_argument("--format", default="post")
        sp.add_argument("--size", help="WxH, masalan 1200x628 (formatdan ustun)")
        sp.add_argument("--scale", type=float, default=1, help="2 = retina/print sifati")

    s.add_parser("formats").set_defaults(f=cmd_formats)
    s.add_parser("fonts").set_defaults(f=cmd_fonts)
    s.add_parser("templates").set_defaults(f=cmd_templates)

    sp = s.add_parser("make"); sp.add_argument("template"); sp.add_argument("out")
    sp.add_argument("--set", action="append", metavar="key=qiymat"); sized(sp); sp.set_defaults(f=cmd_make)

    sp = s.add_parser("render"); sp.add_argument("input"); sp.add_argument("out"); sized(sp); sp.set_defaults(f=cmd_render)

    sp = s.add_parser("carousel"); sp.add_argument("inputs", nargs="+"); sp.add_argument("outdir")
    sized(sp); sp.set_defaults(f=cmd_carousel)

    sp = s.add_parser("icon"); sp.add_argument("name"); sp.add_argument("out")
    sp.add_argument("--set", default="lucide", choices=list(ICON_SETS))
    sp.add_argument("--color", default="#0E0E10"); sp.add_argument("--stroke", default="2")
    sp.add_argument("--size", default="96"); sp.set_defaults(f=cmd_icon)

    sp = s.add_parser("cutout"); sp.add_argument("input"); sp.add_argument("out")
    sp.add_argument("--model", default="isnet-general-use"); sp.add_argument("--no-trim", action="store_true")
    sp.set_defaults(f=cmd_cutout)

    sp = s.add_parser("palette"); sp.add_argument("input"); sp.add_argument("--n", type=int, default=6)
    sp.set_defaults(f=cmd_palette)

    sp = s.add_parser("sheet"); sp.add_argument("out"); sp.add_argument("images", nargs="+")
    sp.add_argument("--cols", type=int, default=4); sp.set_defaults(f=cmd_sheet)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
