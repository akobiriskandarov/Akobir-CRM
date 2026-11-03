# Bovari Agency — AI agentlar jamoasi (Telegram bot)

Bovari Agency marketing jamoasi uchun 7 ta AI agent, bitta **«Bovari Agency»** Telegram botida.
Agentlar Claude (Anthropic) modeli asosida ishlaydi va agentlik konteksti, metodologiyasi
(Business Goal → Market → … → KPI → Optimization) hamda ishlash tamoyillarini biladi.

| Agent | Buyruq | Nima qiladi |
|---|---|---|
| 🎯 Marketolog | `/marketolog` | Strategiya, pozitsiyalash, oferta, voronka, media-reja, unit economics (+ web qidiruv) |
| 📱 SMM menejer | `/smm` | SMM strategiya, kontent-reja, rubrikalar, profil upakovkasi |
| 📋 Proyekt menejer | `/pm` | Loyiha rejasi, vazifalar, mas'ullar, muddatlar, SOP, status-hisobot |
| 🎨 Dizayner | `/dizayner` | Vizual konsepsiya, TZ, palitra, AI-rasm promptlari, rasm tanqidi |
| ✍️ Kopirayter | `/kopirayter` | Post va reklama matnlari, Reels ssenariy (Hook→Problem→Insight→Solution→CTA), KP |
| 📊 Analitik | `/analitik` | KPI, reklama tahlili, ROMI/CAC/LTV, A/B test, CSV/PDF tahlil (+ web qidiruv) |
| 🎬 Video montajyor | `/montajyor` | Montaj rejasi, shot-list, retention montaj, rang/ovoz, eksport sozlamalari |

## Imkoniyatlar

- **Agent almashtirish** — pastki tugmalar, `/agentlar` yoki `/kopirayter <vazifa>` shaklida darhol vazifa bilan.
- **👥 Jamoa rejimi** — `/jamoa <vazifa>`: koordinator vazifani 2–5 agentga taqsimlaydi, har bir agent
  oldingilarning natijasiga tayanib ishlaydi, oxirida koordinator xulosa va harakat rejasini beradi.
- **Xotira** — har bir agent har bir xodim bilan suhbatni alohida eslab qoladi (`/yangi` — qayta boshlash).
- **Fayllar** — rasm (dizayn tahlili), PDF, CSV/TXT/MD/JSON/SRT.
- **Kirish nazorati** — faqat `ALLOWED_USER_IDS` dagi jamoa a'zolari foydalanadi.
- **Xarajat nazorati** — `/statistika` (admin): oxirgi 30 kun bo'yicha agentlar kesimida taxminiy xarajat.
- **Guruhda ishlash** — guruhga qo'shilsa, faqat `@bot` deb murojaat qilinganda yoki botga reply qilinganda javob beradi.

## O'rnatish (10 daqiqa)

1. **Bot yaratish.** Telegram'da [@BotFather](https://t.me/BotFather) → `/newbot` → nom: `Bovari Agency`,
   username: masalan `bovari_agency_bot`. Tokenni saqlang.
   (Bot ishga tushganda nomini, tavsifini va buyruqlar menyusini o'zi «Bovari Agency» qilib sozlaydi.)
2. **Claude API kaliti.** [console.anthropic.com](https://console.anthropic.com) → API Keys → kalit yarating,
   balansni to'ldiring.
3. **Sozlash.**
   ```bash
   cp .env.example .env
   # .env ichida TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USER_IDS, ADMIN_USER_IDS ni to'ldiring
   ```
   Telegram ID ni bilish: botni ishga tushirib `/start` yozing — ruxsat bo'lmasa, bot ID ni ko'rsatadi.
4. **Ishga tushirish.**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m bovari_bot
   ```
   yoki serverda Docker bilan (24/7 ishlashi uchun):
   ```bash
   docker compose up -d --build
   ```

## Sozlamalar (`.env`)

| O'zgaruvchi | Standart | Izoh |
|---|---|---|
| `CLAUDE_MODEL` | `claude-opus-5-5` | Model |
| `CLAUDE_EFFORT` | `medium` | Fikrlash chuqurligi: `low` (arzon, tez) … `max`. Marketolog va Analitik doim `high` |
| `HISTORY_TURNS` | `12` | Har bir agent eslab qoladigan oxirgi savol-javoblar soni |
| `WEB_SEARCH` | `true` | Marketolog va Analitik uchun internet qidiruvi |
| `DB_PATH` | `data/bovari.db` | SQLite baza (tarix va statistika) |

## Agentlarni moslashtirish

Barcha ko'rsatmalar `bovari_bot/agents.py` faylida:
- `AGENCY_CONTEXT` — barcha agentlar uchun umumiy: agentlik haqida, tamoyillar, bozor konteksti.
  Bu yerga narx-navo, paketlar, keyslar, brend tone of voice qo'shilsa, agentlar ancha aniqroq ishlaydi.
- Har bir agentning `role_prompt` — rol, vazifalar va javob formati.
- Yangi agent qo'shish: yangi `Agent(...)` yarating va `AGENTS` ga qo'shing — buyruq va tugma avtomatik paydo bo'ladi.

## Tuzilma

```
bovari_bot/
  agents.py      — 7 agent va koordinator ko'rsatmalari
  llm.py         — Claude API (adaptive thinking, web qidiruv, prompt cache, refusal fallback)
  bot.py         — Telegram handlerlari, klaviaturalar, jamoa rejimi
  storage.py     — SQLite: tanlangan agent, suhbat tarixi, xarajat logi
  formatting.py  — Markdown → Telegram HTML, uzun javoblarni bo'laklash
tests/           — pytest testlari (API ga murojaat qilmaydi)
```

Testlar: `pip install pytest && python -m pytest -q`
