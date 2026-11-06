# Montaj uslublari kutubxonasi (referenslar tahlili)

Akobir yuborgan referens videolardan o'rganilgan usullar. Har yangi referens shu faylga qo'shiladi.

---

## #1 — "Derazadagi bola" (burger yetkazib berish reklamasi, 13 s)

**Format:** 9:16 (720x1280), 24 fps, 13.2 s, ovoz −16 LUFS. Bitta uzluksiz kadr — **birorta ham kesim yo'q** (scene-detect 0 ta kesim).

### Struktura (vaqt bo'yicha)

| Vaqt | Nima bo'ladi | Funksiya |
|---|---|---|
| 0–3 s | Shahar ko'p qavatli uylari, minglab derazalar → tez **push-in (zoom)** bitta yoritilgan derazaga | Hook: "minglab odamdan bittasi" — ko'z qayerga qarashni o'zi izlaydi |
| 3–5 s | Zoom sekinlashib to'xtaydi, deraza kadrda markazda, statik | Kontekst: bola, stol, qora paket |
| 5–9 s | Bola paketni ochib, burger oladi, tishlaydi | Mahsulot — tabiiy holatda, "reklama"siz |
| 9–12 s | Bola **kameraga qarab qoladi** ("qo'lga tushdim") | Emotsional cho'qqi, tomoshabin bilan aloqa, hazil |
| 12–13 s | **Parda yopiladi** — kadr yopiq parda bilan tugaydi | Punchline / "button" — tabiiy final, loop'ga qulay |

### Montaj usullari

1. **One-take (bitta kadr) hikoya.** Kesimsiz — ishonchlilik va "josuslik" hissi. Ritmni kesim emas, kadr ichidagi harakat beradi.
2. **Ease-out push-in.** Zoom boshida tez (0–2 s), keyin silliq sekinlashadi va to'xtaydi (ease-out). Keng plandan detalga — "spot the one" hook.
3. **Rang orqali yo'naltirish.** Butun kadr sovuq ko'k-to'q (kechki shahar, blue hour), faqat bitta deraza **iliq sariq** yorug'lik bilan. Ko'z avtomatik iliq nuqtaga boradi. Komplementar kontrast: ko'k fasad ↔ to'q sariq interyer.
4. **Kadr ichida kadr (frame within frame).** Deraza romi — tabiiy vin'etka, subyektni izolyatsiya qiladi; simmetrik grafik kompozitsiya (fasad panellari).
5. **Vuayeristik (tashqaridan kuzatuvchi) nuqtai nazar** — tomoshabin "begona derazaga" qaraydi → qiziquvchanlik.
6. **4-devorni buzish:** qahramon kameraga qaraydi — kulgili lahza va xotirada qoladigan kadr.
7. **Tabiiy final ("button"):** parda yopilishi — matnsiz, gapsiz yopilish; "sahna tugadi" belgisi.
8. **Mahsulot yumshoq joylashtirilgan:** brend logotipi faqat paketda, kichik; hech qanday matn, ovoz, CTA yo'q — hikoya o'zi sotadi (emotsiya: "shunchalik mazaliki, yashirincha yeydi").

### Ovoz dizayni

- **Musiqa yo'q, gap yo'q.** Faqat shahar ambiyensi (fon gul-guli) + aniq **foley** zarbalari: paket shitirlashi, qog'oz, tishlash, oxirida parda "vush"i.
- Ovoz cho'qqilari harakat bilan sinxron (spektrogrammada vertikal "zarbalar").
- Boshida kuchliroq (−10…−16 LU), oxiriga tinchlanadi (−22…−23) → parda tovushi bilan yakun.

### Nega ishlaydi (marketing mantiq)

- Hook vizual savol: "qaysi derazaga zoom qilyapmiz?" — 3 soniyada scroll to'xtaydi.
- 13 s — to'liq ko'riladi, loop qilinadi (watch time ↑).
- Tilsiz → har qanday bozorda ishlaydi; ovozsiz ko'rilganda ham tushunarli.
- Insight: mahsulotni maqtamaydi, **xulq-atvorni** ko'rsatadi.

### Bovari uchun qanday qo'llash

- **To'y industriyasi:** zaldagi yuzlab mehmonlar → push-in bitta kichik real lahzaga (bobo yig'layapti, bola tortni yashirincha yeyapti). Restoran/banket zali reklamasi uchun ideal.
- **Restoran/kafe:** ko'chadan oyna orqali bitta stolga zoom; mijoz kameraga qaraydi → parda/eshik yopiladi.
- **Shaxsiy brend Reels:** ochilish kadri sifatida — keng plan → Akobir, hook ovozi zoom tugashi bilan boshlanadi.

### Texnik takrorlash

- **S'yomka:** shtativ + telefoto (70–200 mm yoki 100–400) uzoqdan; optik zoom yoki 4K/6K dan raqamli kroping. Blue hour (quyosh botgandan 15–30 daq keyin), interyerda iliq 3200K chiroq.
- **Montajda raqamli push-in (ffmpeg, ease-out):** 4K manbadan 1080x1920 ga
  ```bash
  # D = zoom davomiyligi (kadr), Z = yakuniy masshtab, cx/cy = maqsad nuqta (0..1)
  ffmpeg -i in.mp4 -vf "zoompan=z='1+(Z-1)*(1-pow(1-min(on/D,1),3))':x='(iw-iw/zoom)*cx':y='(ih-ih/zoom)*cy':d=1:s=1080x1920:fps=24" -c:a copy out.mp4
  ```
  (`1-(1-t)^3` — ease-out cubic; masalan Z=6, D=72 (3 s @24fps)). Yaxshi sifat uchun manba kamida 4K bo'lsin, aks holda tez zoom'da piksellar ko'rinadi.
- **Rang:** soyalar va fasadni ko'k/teal'ga, interyer yorug'ligini to'q sariqqa (teal & orange), kontrastni o'rtacha.
- **Ovoz:** musiqasiz; ambiyens bed −28…−30 LUFS, foley zarbalar ustida; yakuniy −14…−16 LUFS.
- **AI-generatsiya varianti:** kadr AI-video uslubiga juda mos (statik kompozitsiya, bitta harakat). Prompt g'oyasi: "slow telephoto push-in from dusk city skyline to a single warm-lit apartment window, child secretly eating a burger, looks at camera, closes curtain, 9:16, cinematic, blue hour".
