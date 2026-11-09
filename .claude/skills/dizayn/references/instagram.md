# Instagram va ijtimoiy tarmoq dizayni: qo'llanma

## O'lchamlar (px)

| Nima | O'lcham | Izoh |
|---|---|---|
| Feed post | 1080x1350 (4:5) | Lentada eng ko'p joy egallaydi, asosiy format |
| Feed post 3:4 | 1080x1440 | Profil to'ri 3:4 bo'lgani uchun to'rda kesilmaydi |
| Kvadrat | 1080x1080 | Karusel, menyu, katalog |
| Reels / Stories / Reels muqova | 1080x1920 (9:16) | Profil to'rida faqat markaziy 1080x1440 ko'rinadi (y 240..1680) |
| Reklama (Reels/Stories joyi) | 1080x1920 | Ads Manager 9:16; 4:5 versiyasi feed uchun |
| Highlights muqova | 1080x1920, markazda ⌀ ~600 doira | Ikonka + 1 so'z, bir xil uslub |
| Telegram post rasmi | 1280x720 | |
| YouTube thumbnail | 1280x720 | |

## Xavfsiz zonalar (1080x1920)

`social.py safezone in.png out.jpg --ui reels|story|ads` ustiga chizib ko'rsatadi.

- **Reels / Reels reklama:** yuqori 0–210 (sarlavha), pastki 1420–1920 (akkaunt nomi, caption, CTA tugmasi ~1437–1520),
  o'ng tomon 960–1080 (y 1000–1700, like/izoh tugmalari). Narx va CTA ≤ 1400 da bo'lsin.
- **Stories:** yuqori 0–250 (progress, profil), pastki 1580–1920 (javob qatori).
- **Reels muqova:** muhim narsa (hook, mahsulot) y 240–1680 ichida, chunki profil to'ri shuni ko'rsatadi.
- **Feed 4:5:** to'rda yon tomonlardan ~34 px kesiladi, chetga matn qo'ymang.

## Muqova (cover) qoidalari

1. **Profil to'ri — bitta vitrina.** Barcha muqovalar bitta tizimda: bir xil fon tonalligi, shrift, logo joyi va aksent rang.
   Tekshirish: `social.py grid grid.jpg *.png`.
2. **Hook ≤ 4 so'z, 2 qator,** to'rda (360 px kenglik) ham o'qilsin. Bitta so'z aksent rangda.
3. **Mahsulot yoki yuz:** kadrda bitta aniq obyekt; qorong'i, toza fon, yon tomondan iliq yorug'lik (food uchun).
4. **Kontrast:** matn ostiga gradient soya (`Soya` qatlami). Qizil matnni qizil-to'q sariq mahsulot ustiga qo'ymang, suratni pastga suring (`--offset`).
5. **Logo kichik, tepada.** Muqovada brend 5–8% joy egallaydi, katta joyni hook oladi.
6. Videodagi tasodifiy kadr muqova bo'lmaydi: maxsus foto yoki eng yaxshi kadr (`montaj frames`) + tipografiya.

## Reklama kreativi (target)

- **Taklif dizayndan kuchli bo'lishi kerak:** chegirma yoki qo'shimcha qiymat bo'lmasa, kreativ "ko'rinadi", lekin sotmaydi.
  Kombo narxi taomlar yig'indisiga teng bo'lsa, taklif yo'q degani.
- Struktura: **Hook (2 qator, katta) → mahsulot surati → tarkib (1–2 qator) → narx stikeri → joylashuv.**
- Narx — stiker yoki muhr shaklida, hookdan keyin eng ko'zga tashlanadigan element.
- 3–4 kreativ variant (rang yoki hook farqi) → A/B test. Har bir variant bitta o'zgaruvchi bilan farq qilsin.
- Stok foto, boshqa joyning taomi yoki AI rasmi real mahsulot o'rniga ishonchni buzadi. Imkon bo'lsa, mijozning o'z surati kerak.
- Boshqa brendlarning logotipini (Pepsi va h.k.) chizmang. Mahsulotni umumiy shaklda ko'rsating yoki real foto ishlating.

## Surat sifati

- Skrinshotdan olingan surat (~420 px) → `social.py clean --auto-icon` ("play" belgisini o'chiradi) → `upscale --model edsr --sharpen` → muqova.
  Natija telefonda yaxshi, katta ekranda yumshoq bo'ladi. Iloji bo'lsa asl faylni so'rang.
- Fon olib tashlash: `dizayn.py cutout` (rembg). Odam uchun `--model u2net_human_seg`.
- Rangni brendga moslash: `dizayn.py palette foto.jpg`.

## Topshirish formatlari

- **PNG**: yuklash uchun. **SVG**: Illustrator/CorelDRAW (matn tahrirlanadi). **PDF**: Illustrator.
  **PSD**: Photoshop, qatlamli, lekin matn rastr holatda. CDR formatini yaratib bo'lmaydi: Corel'da SVG'ni import qilib saqlanadi.
- `social.py export dizayn.svg outdir --psd --pdf`: SVG'dagi har bir yuqori `<g id="...">` PSD qatlamiga aylanadi.
- Paketga shriftlarni ham qo'shing (`fonts/`), aks holda dizayner tomonida matn almashib ketadi.

## Ish oqimi (har bir buyurtma)

1. Biznes maqsad → auditoriya → bitta asosiy fikr → CTA.
2. Mijozning mavjud sahifasini o'rganing (rang, logo, uslub, to'r). Yangi dizayn to'rga mos tushsin.
3. Ma'lumotni tekshiring (narxlar, yig'indilar, nomlar). Xatolarni mijozga ko'rsating.
4. Dizayn → `safezone` va `grid` bilan tekshirish → kamida bitta to'liq o'lchamdagi PNG'ni ko'z bilan ko'rish.
5. Topshirish: PNG + tahrirlanadigan fayllar + shriftlar + OQING.txt (qatlamlar, zonalar).
