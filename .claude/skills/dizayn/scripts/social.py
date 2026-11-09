#!/usr/bin/env python3
"""Ijtimoiy tarmoq dizayni: muqovalar, eksport, sifat, tekshiruv.

  cover PHOTO out.png --hook "1-QATOR|2-QATOR" [--hl 1] [--sub "..."] [--brand HIKARI --mark 光]
        [--accent #E0261B] [--fg #FFF4E2] [--ink #0A0807] [--offset 0] [--format story] [--all]
        — foto + katta hook muqova (Reels/Stories/post). SVG manba + PNG; --all: PDF va qatlamli PSD ham.
  export in.svg outdir [--psd] [--pdf]   — SVG (yuqori <g id> = qatlam) -> PNG/PDF/PSD
  upscale in out [--x 4] [--model espcn|edsr|fsrcnn] — AI bilan kattalashtirish (EDSR: sifat, ESPCN: tez)
  clean in out [--auto-icon] [--box x,y,w,h ...]   — belgi/yozuvni o'chirish (inpaint)
  grid out.jpg a.png b.png ...  [--crop 34|45|none] — Instagram profil to'ri (3:4) ko'rinishi
  safezone in.png out.png [--ui reels|story|ads|feed] — interfeys zonalarini ustiga chizish
"""
import argparse, base64, io, json, os, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
EXPORT_JS = Path(__file__).resolve().parent / "export.js"
CSS = (ROOT / "assets" / "base.css").as_uri()
SR_DIR = Path.home() / ".cache" / "dizayn" / "sr"
SR_URLS = {
    "edsr": "https://raw.githubusercontent.com/Saafke/EDSR_Tensorflow/master/models/EDSR_x{x}.pb",
    "espcn": "https://raw.githubusercontent.com/fannymonori/TF-ESPCN/master/export/ESPCN_x{x}.pb",
    "fsrcnn": "https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN_x{x}.pb",
}
SIZES = {"story": (1080, 1920), "post": (1080, 1350), "post34": (1080, 1440), "square": (1080, 1080)}
CYR = re.compile(r"[Ѐ-ӿ]")


# ---------------- yordamchi ----------------
def svg_wrap(svg):
    return (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{CSS}">'
            f'<style>html,body{{background:transparent;margin:0}}svg{{display:block}}</style></head><body>{svg}</body></html>')


def svg_size(svg):
    m = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', svg)
    return int(m.group(1)), int(m.group(2))


def run_export(svg_path, outdir, psd=False, pdf=False):
    svg = Path(svg_path).read_text()
    w, h = svg_size(svg)
    layers = re.findall(r'^<g id="([^"]+)"', svg, flags=re.M)
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    stem = Path(svg_path).stem
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "p.html"; page.write_text(svg_wrap(svg))
        job = dict(html=str(page), w=w, h=h, png=str(outdir / f"{stem}.png"),
                   pdf=str(outdir / f"{stem}.pdf") if pdf else None,
                   layers=layers if psd else [], layerdir=td)
        subprocess.run(["node", str(EXPORT_JS), json.dumps(job)], check=True)
        print(f"✓ {job['png']}")
        if pdf: print(f"✓ {job['pdf']}")
        if psd:
            from PIL import Image
            from psd_tools import PSDImage
            from psd_tools.api.layers import PixelLayer
            doc = PSDImage.new("RGB", (w, h))
            for L in layers:
                im = Image.open(Path(td) / f"{L}.png").convert("RGBA")
                bb = im.getbbox()
                if bb:
                    doc.append(PixelLayer.frompil(im.crop(bb), doc, L, top=bb[1], left=bb[0]))
            doc.save(str(outdir / f"{stem}.psd"))
            print(f"✓ {outdir / (stem + '.psd')}  qatlamlar: {', '.join(layers)}")


def text_w(font, text, size):
    from PIL import ImageFont
    return ImageFont.truetype(str(font), size).getlength(text)


# ---------------- cover ----------------
def photo_layer(photo, W, H, offset):
    from PIL import Image, ImageFilter, ImageEnhance
    ph = Image.open(photo).convert("RGB")
    ph = ph.resize((W, round(ph.height * W / ph.width)), Image.LANCZOS)
    bg = ph.resize((W, H)).filter(ImageFilter.GaussianBlur(60))
    bg = ImageEnhance.Brightness(bg).enhance(.35)
    out = bg.copy()
    if ph.height >= H:  # balandroq foto: pastki qismini ko'rsat
        top = H - ph.height + offset
        out.paste(ph, (0, top))
    else:  # kalta foto: pastga joylab, tepasini yumshoq aralashtir
        top = H - ph.height + offset
        mask = Image.new("L", ph.size, 255)
        fade = min(240, ph.height // 4)
        for y in range(fade):
            mask.paste(int(255 * (y / fade) ** 1.4), (0, y, W, y + 1))
        out.paste(ph, (0, top), mask)
    noise = Image.effect_noise((W, H), 22).convert("RGB")
    out = Image.blend(out, noise, .035)
    buf = io.BytesIO(); out.save(buf, "JPEG", quality=93)
    return base64.b64encode(buf.getvalue()).decode()


def cmd_cover(a):
    W, H = SIZES[a.format]
    lines = [s.strip() for s in a.hook.split("|")]
    cyr = any(CYR.search(l) for l in lines)
    fam, ffile = ("Oswald", FONTS / "Oswald.ttf") if cyr else ("Bebas Neue", FONTS / "BebasNeue.ttf")
    maxw = W - 2 * 90
    f = min(min(a.max_size, int(maxw * 100 / max(text_w(ffile, l, 100), 1))) for l in lines)
    weight = ' font-weight="700"' if cyr else ""
    # vertikal joylashuv: Reels profil to'ri markaziy 3:4 (y 240..1680) ichida
    top0 = {"story": 300, "post": 120, "post34": 140, "square": 110}[a.format]
    brand_h = 0
    logo = ""
    if a.brand:
        cx = W / 2
        mark = (f'<circle cx="{cx}" cy="{top0 - 8}" r="27" fill="{a.accent}"/>'
                f'<text x="{cx}" y="{top0 + 4}" text-anchor="middle" font-family="IPAGothic, Dela Gothic One" font-size="30" fill="{a.fg}">{a.mark}</text>') if a.mark else ""
        logo = (f'<g id="Logo">{mark}<text x="{cx}" y="{top0 + (64 if a.mark else 20)}" text-anchor="middle" font-family="Unbounded" '
                f'font-weight="700" font-size="26" letter-spacing="13" fill="{a.fg}">{a.brand}</text></g>')
        brand_h = 110 if a.mark else 60
    y = top0 + brand_h + f * .82
    hook = []
    for i, l in enumerate(lines):
        col = a.accent if i == a.hl else a.fg
        hook.append(f'<text x="{W/2}" y="{y:.0f}" text-anchor="middle" font-family="{fam}"{weight} font-size="{f}" fill="{col}">{l}</text>')
        y += f * .9
    sub = ""
    if a.sub:
        sub = (f'<g id="Izoh"><line x1="{W/2-30}" y1="{y - f*.9 + 42:.0f}" x2="{W/2+30}" y2="{y - f*.9 + 42:.0f}" stroke="{a.accent}" stroke-width="4"/>'
               f'<text x="{W/2}" y="{y - f*.9 + 92:.0f}" text-anchor="middle" font-family="Manrope" font-weight="700" font-size="26" letter-spacing="5" fill="{a.fg}">{a.sub}</text></g>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><linearGradient id="sh" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{a.ink}" stop-opacity=".95"/><stop offset=".30" stop-color="{a.ink}" stop-opacity=".78"/>
<stop offset=".46" stop-color="{a.ink}" stop-opacity="0"/><stop offset=".88" stop-color="{a.ink}" stop-opacity="0"/><stop offset="1" stop-color="{a.ink}" stop-opacity=".6"/></linearGradient></defs>
<g id="Foto"><image width="{W}" height="{H}" href="data:image/jpeg;base64,{photo_layer(a.photo, W, H, a.offset)}"/></g>
<g id="Soya"><rect width="{W}" height="{H}" fill="url(#sh)"/></g>
{logo}
<g id="Hook">{"".join(hook)}</g>
{sub}
</svg>'''
    out = Path(a.out)
    svg_path = out.with_suffix(".svg")
    svg_path.write_text(svg)
    run_export(svg_path, out.parent, psd=a.all, pdf=a.all)
    if cyr:
        print("ℹ kirill matn: Bebas Neue'da kirill yo'q, Oswald ishlatildi")


# ---------------- upscale / clean ----------------
def cmd_upscale(a):
    import cv2
    SR_DIR.mkdir(parents=True, exist_ok=True)
    f = SR_DIR / Path(SR_URLS[a.model].format(x=a.x)).name
    if not f.exists():
        print("model yuklanmoqda:", f.name)
        f.write_bytes(urllib.request.urlopen(SR_URLS[a.model].format(x=a.x), timeout=120).read())
    sr = cv2.dnn_superres.DnnSuperResImpl_create(); sr.readModel(str(f)); sr.setModel(a.model, a.x)
    im = cv2.imread(a.input)
    out = sr.upsample(im)
    if a.sharpen:
        blur = cv2.GaussianBlur(out, (0, 0), 2)
        out = cv2.addWeighted(out, 1.5, blur, -.5, 0)
    cv2.imwrite(a.out, out)
    print(f"✓ {a.out}  {im.shape[1]}x{im.shape[0]} → {out.shape[1]}x{out.shape[0]}")


def cmd_clean(a):
    import cv2, numpy as np
    im = cv2.imread(a.input); h, w = im.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    if a.auto_icon:  # Instagram "play"/carousel belgisi: yuqori o'ng burchakdagi oq shakl
        rw, rh = int(w * .27), int(h * .16)
        g = cv2.cvtColor(im[0:rh, w - rw:w], cv2.COLOR_BGR2GRAY)
        m = cv2.dilate((g > 200).astype(np.uint8) * 255, np.ones((9, 9), np.uint8), 2)
        mask[0:rh, w - rw:w] = m
    for b in a.box or []:
        x, y, bw, bh = map(int, b.split(","))
        mask[y:y + bh, x:x + bw] = 255
    out = cv2.inpaint(im, mask, 9, cv2.INPAINT_TELEA)
    cv2.imwrite(a.out, out)
    print(f"✓ {a.out}  ({int(mask.astype(bool).sum())} px tozalandi)")


# ---------------- grid / safezone ----------------
def cmd_grid(a):
    from PIL import Image
    cells = []
    for p in a.images:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        tw, th = w, round(w * 4 / 3)
        if th > h:  # 4:5 post: yon tomonlar kesiladi
            th, tw = h, round(h * 3 / 4)
        x0, y0 = (w - tw) // 2, (h - th) // 2
        cells.append(im.crop((x0, y0, x0 + tw, y0 + th)).resize((360, 480), Image.LANCZOS))
    rows = (len(cells) + 2) // 3
    g = Image.new("RGB", (3 * 360 + 8, rows * 480 + (rows - 1) * 4), "#000")
    for i, c in enumerate(cells):
        g.paste(c, ((i % 3) * 364, (i // 3) * 484))
    g.save(a.out, quality=90)
    print(f"✓ {a.out}  (Instagram profil to'ri, 3:4)")


UI = {  # 1080x1920 bo'yicha, Instagram interfeysi egallaydigan zonalar
    "reels": [(0, 0, 1080, 210), (0, 1420, 1080, 1920), (960, 1000, 1080, 1700)],
    "ads": [(0, 0, 1080, 210), (0, 1420, 1080, 1920), (960, 1000, 1080, 1700)],
    "story": [(0, 0, 1080, 250), (0, 1580, 1080, 1920)],
    "feed": [],
}


def cmd_safezone(a):
    from PIL import Image, ImageDraw
    im = Image.open(a.input).convert("RGBA")
    k = im.width / 1080
    o = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    for (x0, y0, x1, y1) in UI[a.ui]:
        d.rectangle([x0 * k, y0 * k, x1 * k, y1 * k], fill=(255, 0, 60, 70), outline=(255, 0, 60, 220), width=3)
    if a.ui in ("reels", "ads") and im.height / im.width > 1.7:
        y0, y1 = 240 * k, 1680 * k
        d.rectangle([2, y0, im.width - 3, y1], outline=(0, 220, 255, 255), width=4)
        d.text((12, y0 + 8), "profil to'ri 3:4", fill=(0, 220, 255, 255))
    if a.ui == "ads":
        d.rounded_rectangle([40 * k, 1437 * k, 912 * k, 1520 * k], 24 * k, fill=(80, 80, 80, 210))
    Image.alpha_composite(im, o).convert("RGB").save(a.out, quality=92)
    print(f"✓ {a.out}  (qizil = interfeys yopadi, ko'k = profil to'ri)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("cover"); c.add_argument("photo"); c.add_argument("out")
    c.add_argument("--hook", required=True); c.add_argument("--hl", type=int, default=1)
    c.add_argument("--sub", default=""); c.add_argument("--brand", default=""); c.add_argument("--mark", default="")
    c.add_argument("--accent", default="#E0261B"); c.add_argument("--fg", default="#FFF4E2"); c.add_argument("--ink", default="#0A0807")
    c.add_argument("--offset", type=int, default=0); c.add_argument("--max-size", type=int, default=210)
    c.add_argument("--format", default="story", choices=list(SIZES)); c.add_argument("--all", action="store_true")
    c.set_defaults(f=cmd_cover)
    e = s.add_parser("export"); e.add_argument("svg"); e.add_argument("outdir")
    e.add_argument("--psd", action="store_true"); e.add_argument("--pdf", action="store_true")
    e.set_defaults(f=lambda a: run_export(a.svg, a.outdir, a.psd, a.pdf))
    u = s.add_parser("upscale"); u.add_argument("input"); u.add_argument("out")
    u.add_argument("--x", type=int, default=4, choices=[2, 3, 4]); u.add_argument("--model", default="espcn", choices=list(SR_URLS))
    u.add_argument("--sharpen", action="store_true"); u.set_defaults(f=cmd_upscale)
    k = s.add_parser("clean"); k.add_argument("input"); k.add_argument("out")
    k.add_argument("--auto-icon", action="store_true"); k.add_argument("--box", action="append", metavar="x,y,w,h")
    k.set_defaults(f=cmd_clean)
    g = s.add_parser("grid"); g.add_argument("out"); g.add_argument("images", nargs="+"); g.set_defaults(f=cmd_grid)
    z = s.add_parser("safezone"); z.add_argument("input"); z.add_argument("out")
    z.add_argument("--ui", default="reels", choices=list(UI)); z.set_defaults(f=cmd_safezone)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
