---
name: dizayn
description: Grafik dizayn — Instagram postlar (4:5, 1:1), Stories, Reels cover, karusellar, bannerlar, Telegram/YouTube rasmlari, masterklass e'lonlari, keys/natija postlari. HTML/CSS + Playwright orqali PNG/JPG/PDF render, 13 ta brend shrift, Lucide/Tabler ikonlar, fonni olib tashlash (rembg), rasmdan palitra. "post qil", "banner yasa", "karusel", "dizayn", "obloshka", "e'lon rasmi" deganda ishlatiladi.
---

# Dizayn (Bovari Agency)

```bash
D=.claude/skills/dizayn/scripts/dizayn.py
bash .claude/skills/dizayn/scripts/setup.sh   # yangi sessiyada 1 marta (shrift + rembg)
python3 $D --help
```

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
- Shrift juftliklari: `Unbounded + Manrope` (ekspert/biznes), `Playfair/Cormorant + Great Vibes` (wedding),
  `Bebas Neue/Oswald + Manrope` (aksiya, dinamik). Script shriftni faqat 1–2 so'zga.
- Ranglar `assets/base.css` `:root` da — brendbuk tasdiqlangach shu yerda almashtiriladi.
- Matn foto ustida bo'lsa — gradient/`shade`; kontrast WCAG AA (4.5:1) dan kam bo'lmasin.
- Story/Reels cover: yuqori 250px va pastki 300px ga muhim matn qo'yma (interfeys yopadi).
- Feed grid'da Reels cover markaziy 1080x1440 qismi ko'rinadi — sarlavhani markazga qo'y.
- Karusel: 1-slayd = hook, oxirgi = CTA (saqlash/DM/kalit so'z), 5–8 slayd.

## Cheklovlar

- AI rasm generatsiyasi yo'q — fotolar foydalanuvchidan; abstrakt fonlarni CSS/SVG bilan chiz.
- Yangi shrift: `raw.githubusercontent.com/google/fonts/main/ofl/<nom>/` dan `fonts/` ga yukla va
  `base.css` ga `@font-face` qo'sh (faqat OFL litsenziyali).
- Real brendlar (logotip, nom) mijoz ruxsatisiz ishlatilmaydi; tayyor fayllar repo'ga commit qilinmaydi.
