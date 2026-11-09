# Shriftlar: qayerda ishlatish va qaysi harflar bor

Avtomatik tekshirilgan (fontTools). ✗ bo'lsa — o'sha harf boshqa shriftga tushib, buziladi.

| Shrift | Vazifa | oʻ (U+02BB) | ' / ’ | Kirill | Oʻzb. kirill | 光 |
|---|---|---|---|---|---|---|
| AlumniSans | Ingichka-tor hook, kirill | ✗ | ✓ | ✓ | ✗ | ✗ |
| Anton | Katta hook, plakat | ✓ | ✓ | ✗ | ✗ | ✗ |
| ArchivoBlack | Qalin plakat (lotin) | ✗ | ✓ | ✗ | ✗ | ✗ |
| BebasNeue | Katta hook/sarlavha (faqat lotin!) | ✗ | ✓ | ✗ | ✗ | ✗ |
| Caveat | Qo'lyozma izoh, kirill | ✗ | ✓ | ✓ | ✓ | ✗ |
| Comfortaa | Bolalar/yumshoq brend | ✓ | ✓ | ✓ | ✗ | ✗ |
| CormorantGaramond | Nafis serif (wedding) | ✓ | ✓ | ✓ | ✓ | ✗ |
| DMSerifDisplay | Jurnal sarlavhasi | ✗ | ✓ | ✗ | ✗ | ✗ |
| DelaGothicOne | Yapon/osiyo uslubi + kanji | ✗ | ✓ | ✓ | ✗ | ✓ |
| Exo2 | Texno/zamonaviy | ✓ | ✓ | ✓ | ✓ | ✗ |
| GolosText | Kirill uchun asosiy matn | ✗ | ✓ | ✓ | ✓ | ✗ |
| GreatVibes | Script — 1-2 so'z (wedding) | ✓ | ✓ | ✓ | ✗ | ✗ |
| InterTight | Ixcham matn, UI | ✓ | ✓ | ✓ | ✓ | ✗ |
| KaushanScript | Brush script (lotin) | ✗ | ✓ | ✗ | ✗ | ✗ |
| Lobster | Kafe/menyu script, kirill | ✓ | ✓ | ✓ | ✗ | ✗ |
| Manrope | Asosiy matn, izoh | ✗ | ✓ | ✓ | ✗ | ✗ |
| MarckScript | Kirill qo'lyozma | ✗ | ✓ | ✓ | ✗ | ✗ |
| Montserrat | Universal sarlavha/matn | ✓ | ✓ | ✓ | ✓ | ✗ |
| Oswald | Hook — kirill ham bor | ✓ | ✓ | ✓ | ✓ | ✗ |
| Pacifico | Yengil script, kirill | ✗ | ✓ | ✓ | ✓ | ✗ |
| PlayfairDisplay | Premium serif (wedding, restoran) | ✓ | ✓ | ✓ | ✗ | ✗ |
| Prata | Kirill premium serif | ✗ | ✓ | ✓ | ✗ | ✗ |
| Rubik | Yumshoq universal | ✗ | ✓ | ✓ | ✗ | ✗ |
| RubikMonoOne | Ko'cha/streetwear, kirill | ✗ | ✓ | ✓ | ✗ | ✗ |
| RussoOne | Sport/texno uslub, kirill | ✗ | ✓ | ✓ | ✗ | ✗ |
| Unbounded | Brend/logo, keng display | ✓ | ✓ | ✓ | ✗ | ✗ |
| YesevaOne | Kirill dekorativ serif | ✗ | ✓ | ✓ | ✗ | ✗ |

## Qoidalar
- **Oʻzbek lotin:** ko'p display shriftlarda `ʻ` (U+02BB) yo'q → oddiy `'` ishlating (to'g'ri ko'rinadi). Matnda `ʻ` bo'lsa, shriftda borligini tekshiring.
- **Kirill matn:** Bebas Neue, Anton, Archivo Black, Kaushan'da kirill YO'Q. `social.py cover` kirillni sezsa, o'zi Oswald'ga o'tadi.
- **Juftliklar:** Bebas/Oswald + Manrope (reklama, food); Unbounded + Manrope (ekspert, agentlik); Playfair/Cormorant + Great Vibes (wedding);
  Dela Gothic One + Manrope (yapon/osiyo restoran); Lobster/Caveat faqat aksent so'z uchun.
- Bitta dizaynda ko'pi bilan 2 oila (+1 aksent). Script shriftni butun gapga ishlatmang.
- Yangi shrift: `raw.githubusercontent.com/google/fonts/main/ofl/<nom>/` (faqat OFL), `fonts/` ga qo'shing, `base.css` ga `@font-face`, jadvalni yangilang.

