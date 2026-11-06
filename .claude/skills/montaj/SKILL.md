---
name: montaj
description: Video montaj — Reels/Shorts (9:16) ga o'tkazish, kesish, ulash, pauzalarni kesish (jump-cut), subtitr yondirish, hook matni, fon musiqasi (ducking), ovozni -14 LUFS ga normallashtirish, kadrlarni ko'rish. Foydalanuvchi video fayl berib "montaj qil", "Reels qil", "kes", "subtitr qo'y", "musiqa qo'y", "pauzalarni olib tashla" desa ishlatiladi.
---

# Montaj (Bovari Agency)

Barcha amallar `scripts/montaj.py` orqali bajariladi (faqat ffmpeg + Python stdlib).

```bash
M=.claude/skills/montaj/scripts/montaj.py
python3 $M <buyruq> --help
```

## Ish tartibi

1. **Brifni aniqlash** (biznes maqsaddan boshlash): video nima uchun — lead, ishonch, sotuv?
   Platforma, davomiylik, hook, CTA. Ssenariy bo'lsa: Hook → Problem → Insight → Solution → CTA.
2. **Materialni ko'rish:** `info` → `contact` (kadrlar to'ri) → rasmni Read bilan ko'rish.
   Videoni "ko'rmasdan" montaj qilma.
3. **Montaj zanjiri** (har qadam alohida fayl, asl fayl o'zgarmaydi):
   `cut`/`concat` → `jumpcut` (gapiruvchi kadr) → `reels` → `subs` → `text` (hook, 0–3 s) → `music`.
4. **Tekshirish:** yakuniy fayldan `frames`/`contact` olib, ko'z bilan tekshir;
   davomiylik va o'lchamni `info` bilan tasdiqla.
5. **Topshirish:** natijani `SendUserFile` bilan yubor; nima qilinganini qisqa yoz.

## Buyruqlar

| Buyruq | Vazifa | Muhim parametrlar |
|---|---|---|
| `info in.mp4` | o'lcham, fps, davomiylik, audio | — |
| `cut in out --start 00:05 --end 00:20` | bo'lak kesish | vaqt `ss`, `mm:ss` yoki `hh:mm:ss` |
| `concat out a.mp4 b.mp4 ...` | turli formatdagi kliplarni ulash | `--size 1080x1920`, `--fps 30` |
| `reels in out` | 1080x1920 ga o'tkazish | `--mode crop` (markaz, `--x 0..1`) yoki `--mode blur` (xira fon) |
| `jumpcut in out` | pauzalarni kesish | `--noise -35` (shovqinli xona: -30), `--min-silence 0.5`, `--pad 0.12` |
| `subs in s.srt out` | subtitr yondirish | `--size 14`, `--margin 70` |
| `text in out --text "..."` | hook/sarlavha | `--pos top/center/bottom`, `--start 0 --end 3` |
| `music in m.mp3 out` | fon musiqasi + ducking | `--volume 0.25`, `--no-duck` |
| `loudnorm in out` | ovoz -14 LUFS | — |
| `frames in dir --count 6` | kadrlar (JPG) | — |
| `contact in sheet.jpg` | kadrlar to'ri | `--cols 4 --rows 3` |
| `transcribe in out.srt` | ovozdan SRT | faster-whisper + model yuklash uchun internet kerak |

## Standartlar (Reels/TikTok/Shorts)

- 1080x1920, 30 fps, H.264 CRF 18, AAC 192k, ovoz −14 LUFS.
- Hook birinchi 3 soniyada ham ekranda (matn), ham ovozda bo'lsin.
- Subtitr ekranning pastki 1/3 qismida, interfeys tugmalari ostida qolmasin (`--margin 70+`).
- Gapiruvchi kadrda `reels --mode crop`, gorizontal/keng kadrda `--mode blur`.

## Uslublar kutubxonasi

Akobir yuborgan referens videolar tahlili: `references/uslublar.md`.
Ijodiy taklif yoki montaj rejasi tuzishdan oldin shu faylni o'qi va mos usulni taklif qil.
Yangi referens kelsa, tahlilini shu faylga qo'sh (vaqt jadvali, usullar, ovoz, qo'llash).

## Cheklovlar

- Bulut sessiyasida HuggingFace yopiq bo'lishi mumkin → `transcribe` ishlamaydi.
  Unda foydalanuvchidan SRT so'ra yoki matnni o'zing SRT qilib yoz.
- Video fayllar repo'ga commit qilinmaydi (katta hajm) — scratchpad'da ishlang.
- Ijodiy qarorlar (qaysi dubl, ritm, musiqa) — foydalanuvchi bilan kelishiladi.
