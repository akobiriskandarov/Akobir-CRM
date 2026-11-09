---
name: dizayn
description: Grafik va ijtimoiy tarmoq dizayni — Instagram postlar (4:5, 3:4, 1:1), Reels/Stories muqovalari (obloshka), target reklama kreativlari, karusellar, bannerlar, Highlights, Telegram/YouTube rasmlari. HTML/SVG + Playwright render, 40 ta shrift (lotin/kirill/kanji), Lucide/Tabler/brend ikonlar, fon olib tashlash (rembg), AI sifat oshirish (EDSR), belgi tozalash, profil to'ri va xavfsiz zona tekshiruvi, qatlamli PSD/SVG/PDF eksport. "post qil", "muqova", "obloshka", "banner", "reklama kreativi", "karusel", "dizayn", "PSD qilib ber" deganda ishlatiladi.
---

# Dizayn (Bovari Agency)

```bash
D=.claude/skills/dizayn/scripts/dizayn.py
bash .claude/skills/dizayn/scripts/setup.sh   # yangi sessiyada 1 marta (shrift + rembg)
python3 $D --help
```

## Avval o'qing
- `references/instagram.md` — o'lchamlar, xavfsiz zonalar, muqova va reklama qoidalari, topshirish formatlari.
- `references/shriftlar.md` — qaysi shriftda kirill, oʻ, kanji bor (Bebas'da kirill YO'Q).

## Ijtimoiy tarmoq buyruqlari (`scripts/social.py`)

```bash
S=.claude/skills/dizayn/scripts/social.py
python3 $S cover foto.jpg out.png --hook "1-QATOR|2-QATOR" --hl 1 --sub "IZOH" --brand HIKARI --mark 光 [--offset 180] [--format story|post|post34] [--all]
python3 $S export dizayn.svg outdir --psd --pdf     # <g id> qatlamlari -> PSD qatlamlari
python3 $S clean skrin.png toza.png --auto-icon     # play/karusel belgisini o'chirish; --box x,y,w,h
python3 $S upscale toza.png katta.png --model edsr --sharpen   # x4; espcn = tez, edsr = sifat (~60 s)
python3 $S grid grid.jpg 1.png 2.png 3.png          # profil to'ri (3:4) qanday ko'rinadi
python3 $S safezone out.png check.jpg --ui reels|story|ads   # interfeys yopadigan joylar
```
`dizayn.py icon instagram i.svg --set brand` — brend ikonlari (simple-icons).

## Ish tartibi

1. **Brif (biznes maqsaddan):** post nima uchun — ishonch, lead, sotuv, e'lon? Auditoriya kim
   (to'yxona egasi, videograf, tadbirkor)? Bitta asosiy fikr + bitta CTA. Matnni avval yoz, keyin dizayn.
2. **Format:** `formats`. Feed uchun default `post` (1080x1350) — feed'da eng ko'p joy egallaydi.
3. **Tez yo'l — shablon:** `templates` → `make <shablon> out.png --set key=qiymat`.
   Qiymatda HTML mumkin: `<span class='hl'>so'z</span>` (oltin), `hl2` (qizil), `mark` (marker fon).
4. **Maxsus dizayn:** scratchpad'da o'z HTML'ingni yoz (`<link rel="stylesheet" href="{{ASSETS}}/base.css">`),
   o'lchamlarni `vw/vh` da ber, `render in.html out.png --format post`.
5. **Tekshirish (majburiy):** natijani Read bilan ko'r; bir nechta bo'lsa `sheet` bilan to'r qil.
   Matn chiqib ketmaganmi, kontrast, chekka (88px), o'zbek harflari (o', g', ʼ) to'g'rimi.
6. **Topshirish:** `SendUserFile`; nima uchun shunday qilinganini 1–2 jumlada yoz.

## Buyruqlar

| Buyruq | Vazifa |
|---|---|
| `formats` / `fonts` / `templates` | ro'yxatlar |
| `make hook out.png --set title=... --set kicker=...` | shablondan post |
| `render in.html out.png --format story --scale 2` | o'z HTML'ingdan (`.jpg`, `.pdf` ham) |
| `carousel slides_dir/ outdir/` | ko'p HTML → `01.png, 02.png…`, `{{N}}/{{TOTAL}}` avtomatik |
| `icon heart h.svg --set lucide --color "#E8B44A" --stroke 1.5` | ikonka (lucide, tabler, tabler-filled) GitHub'dan, keshlanadi |
| `cutout photo.jpg person.png` | fonni olib tashlash (`--model u2net_human_seg` odam uchun) |
| `palette photo.jpg --n 6` | fotodan rang palitrasi (brendni foto bilan moslash) |
| `sheet out.jpg a.png b.png … --cols 3` | preview to'ri |

## Shablonlar

- `hook` — matnli ekspert post, qora fon. Story uchun `--format story --set title_size=10vw`.
- `photo` — to'liq foto + gradient + serif sarlavha (wedding/production). `image=`, `focus="50% 20%"`.
- `case` — katta raqam + 2 ta ko'rsatkich (keys). Raqam uzun bo'lsa `num_size=16vw`.
- `slide` — karusel slaydi (`big=01`, `title`, `body`).
- `banner` — e'lon/masterklass, `--format banner`; sana/joy/narx + CTA tugma + rasm.

## Dizayn qoidalari

- **1 post = 1 fikr.** Sarlavha ≤ 10 so'z, telefonda 1 soniyada o'qilsin.
- Iyerarxiya: sarlavha → urg'u so'z (rang) → izoh → imzo/CTA. 3 tadan ko'p shrift o'lchami ishlatma.
- Shrift juftliklari va harf qo'llab-quvvatlashi: `references/shriftlar.md`. Script shriftni faqat 1–2 so'zga.
- Ranglar `assets/base.css` `:root` da — brendbuk tasdiqlangach shu yerda almashtiriladi.
- Matn foto ustida bo'lsa — gradient/`shade`; kontrast WCAG AA (4.5:1) dan kam bo'lmasin.
- Story/Reels cover: yuqori 250px va pastki 300px ga muhim matn qo'yma (interfeys yopadi).
- Feed grid'da Reels cover markaziy 1080x1440 qismi ko'rinadi — sarlavhani markazga qo'y.
- Karusel: 1-slayd = hook, oxirgi = CTA (saqlash/DM/kalit so'z), 5–8 slayd.

## Cheklovlar

- Fotolar: avval mijozning o'zidan. AI rasm: ElevenLabs `creative_generate_image` (kredit sarflaydi, bepul rejada kunlik limit bor) — real mahsulot o'rniga emas, faqat atmosfera/test uchun.
- Stok saytlar (Unsplash, Pexels, Wikimedia) bu muhitda yopiq; GitHub ochiq.
- Yangi shrift: `raw.githubusercontent.com/google/fonts/main/ofl/<nom>/` dan `fonts/` ga yukla va
  `base.css` ga `@font-face` qo'sh (faqat OFL litsenziyali).
- Real brendlar (logotip, nom) mijoz ruxsatisiz ishlatilmaydi; tayyor fayllar repo'ga commit qilinmaydi.
