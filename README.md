# Savol javob

Ishtirokchilarni hakamlar bilan savol-javob qilish va baholash dasturi.

## Python bilan qiynalsangiz: doimiy .exe fayl yasash

Ba'zi Windows kompyuterlarda "python" buyrug'i to'g'ri ishlamaydi (Microsoft Store bilan bog'lanib qoladi). Agar `ishga_tushirish.bat` xato bersa va bu tuzatilmasa, **bir marta** Python'ni to'g'ri ishlatib (masalan python.org saytidan rasman o'rnatib), `exe_yasash.bat` ni ishga tushiring.

Bu sizga **"Savol javob.exe"** nomli, hech qanday Python kerak bo'lmaydigan doimiy dastur yasab beradi. Shundan keyin bu bitta faylni istalgan Windows kompyuterga (hatto Python o'rnatilmagan kompyuterga ham) nusxalab, shunchaki ikki marta bosib ishlatavershingiz mumkin — boshqa hech qanday sozlash kerak emas.

**Ochig'ini aytish kerak:** bu skriptni men Windows kompyuterda sinab ko'ra olmadim (bu yerda faqat Linux muhitim bor). Odatiy, hujjatlashtirilgan usul bilan yozilgan, lekin birinchi urinishda xato chiqsa, to'liq xabar matnini menga yuboring — darhol tuzataman.

## Ishchi stolga o'rnatish (bir martalik)

Har safar papkani ochib yurmaslik uchun `Ishchi_stolga_qoshish.bat` ni bir marta ishga tushiring — bu Ishchi stolingizga "Savol javob" nomli belgicha qo'yadi. Shundan keyin dasturni ochish uchun shu belgichani ikki marta bossangiz yetarli, xuddi o'rnatilgan dastur kabi.

## Ishga tushirish (server kompyuterda)
- Windows: `ishga_tushirish.bat` ni ikki marta bosing.
- Linux/Mac: `./ishga_tushirish.sh`

Bu kompyuterda dastur **alohida dastur oynasida** ochiladi (brauzer manzil satri, yorliqlari ko'rinmaydi) — o'rnatilgan dastur kabi. Bu birinchi marta pywebview kutubxonasini ham o'rnatgani uchun biroz ko'proq vaqt oladi.

Boshqa kompyuterlar (hakamlar, ishtirokchi) esa **o'z brauzerida** ekranda chiqqan manzilni ochib ulanadi (masalan `http://192.168.1.10:8000`) — bu ularga hech narsa o'rnatmasdan, bir nechta kompyuterdan bir vaqtda kirish imkonini beradi. Hammasi bir tarmoqda (Wi-Fi yoki tochka) bo'lishi kerak. Windows firewall so'rasa, 8000-portga ruxsat bering.

Agar pywebview biror sababga ko'ra ishlamasa (masalan juda eski Windows), dastur avtomatik oddiy brauzer tabida ochiladi — hech narsa buzilmaydi.

## Admin
Dastur oynasi ochilgach, **Boshqaruv** sahifasining yuqorisida hakamlar va ishtirokchi uchun ulanish manzili katta harflar bilan ko'rsatiladi — uni belgilab (tanlab) nusxalab, boshqa kompyuterlarga yuboring yoki aytib bering. Bosh sahifada yuqoridagi "Admin" tugmasi. Dastlabki parol: `admin` (Sozlamalarda o'zgartiriladi).
Admin hakam emas: u hamma narsani boshqaradi.

Menyular: Boshqaruv, Yo'nalishlar, Savollar, Ishtirokchilar, Hakamlar, Natijalar, Sozlamalar.

## Ishlash tartibi
1. **Yo'nalishlar**: yo'nalishlarni bittadan qo'shing (masalan Dasturlash, Matematika).
2. **Savollar**: yuqorida yo'nalish tanlanadi (savol shu yo'nalishga qo'shiladi) va savollar tartibi (tasodifiy yoki ketma-ket). Har bir savolga javob ham yoziladi. Javobni hakamlar ko'radi, ishtirokchi ko'rmaydi. Savolni tahrirlash mumkin.
3. **Hakamlar**: hakam raqami, ismi, familyasi (tug'ilgan sana ixtiyoriy) kiritiladi, tizim unga 6 xonali kod beradi. Hakamni o'chirish, yangi kod berish (chiqarib yuborish) mumkin. Hakamlar bir marta kirib, siz o'chirmaguncha ulanib turadi.
4. **Ishtirokchilar**: bu menyuda faqat ro'yxatdagilar ko'rinadi va boshqariladi, kod berish shart emas.
5. Bosh sahifada ikkita bo'lim bor: "Ishtirokchi" (kod kerak emas, to'g'ridan-to'g'ri "Ro'yxatdan o'tish") va "Hakam" (kod kiritiladi). Ism, familya va tug'ilgan sana majburiy (yulduzcha bilan belgilangan); manzil ixtiyoriy. Bo'sh qoldirilgan maydonlar qizil bilan va tagida izoh bilan ko'rsatiladi, siz kiritgan boshqa ma'lumotlar yo'qolmaydi.
6. Ro'yxatdan o'tgach, ishtirokchi navbatga tushadi (yoki "Savol-javobni boshlash" tugmasini ko'radi). Tugma bosilgach, ishtirokchi o'ziga biriktirilgan savollar ro'yxatini ko'radi va **xohlagan tartibda, xohlagan savolni tanlaydi**. Qaysi savolni tanlasa, o'sha savol (va uning javobi) hakamlarga shu zahoti ko'rinadi.
7. Hakamlarda savol tagida "To'g'ri javob" yashirin turadi, uning yonidagi ko'z belgisi bosilsa ko'rinadi. Hakamlar 1 dan maksimal ballgacha baho qo'yadi. Baholangach ishtirokchi keyingi xohlagan savolini tanlaydi. Hammasi baho qo'ygach ishtirokchi (yoki admin) keyingi savolga o'tadi.
7. Bir vaqtda bitta ishtirokchi javob beradi, boshqalari navbatda kutadi. Ishtirokchi savol-javobni tugatmasdan "Chiqish" ni bossa, suhbat yopiladi (hakamlarga ko'rinmaydi, natijasi admin panelida "Yopilgan" bo'lib qoladi).
8. Ishtirokchilar jadvalida har bir ishtirokchi yonidagi uch nuqta ustiga bosilsa, uning barcha ma'lumotlari, nechta savol yechgani va har bir hakam qo'ygan ballar chiqadi.
9. **Natijalar**: reyting va har ishtirokchi bo'yicha jadval. "PDF yuklab olish" tugmasi ishtirokchi, hakam va admin uchun bor.
10. **Sozlamalar**: savollar soni, har bir savol necha ball (1-10; hakamlar 1 dan shu ballgacha baholaydi), admin paroli, natijalarni tozalash.

Ma'lumotlar `savol_javob_v3.db` faylida saqlanadi. Zaxira uchun shu faylni nusxalang.

## Admin parolini unutib qo'ysangiz

`parolni_tiklash.bat` (Windows) yoki `./parolni_tiklash.sh` (Linux/Mac) ni ishga tushiring. Bu parolni standart `admin` ga qaytaradi, boshqa hech narsaga (ishtirokchilar, hakamlar, savollar, natijalar) tegmaydi. Keyin `/admin` ga `admin` paroli bilan kirib, Sozlamalarda darhol yangi parol qo'ying.

## Internetga chiqarish

Dastur hozir mahalliy tarmoq (bitta xona, bitta Wi-Fi) uchun mo'ljallangan. Uni internetga (masalan, boshqa shaharlardagi hakamlar kirishi uchun) chiqarish mumkin, lekin bir nechta narsani hisobga oling:

- **Admin parolini albatta o'zgartiring.** Standart parol `admin` ni internetga chiqarishdan oldin almashtiring — buni hamma biladi.
- **HTTPS kerak.** Dastur hozir oddiy `http://` orqali ishlaydi. Internetda parollar va ma'lumotlar shifrlanmagan holda yuboriladi. Buning uchun serveringiz oldiga Nginx yoki Caddy kabi "reverse proxy" qo'yib, unga bepul Let's Encrypt sertifikati bilan HTTPS qo'shish kerak. Bu qismni siz yoki serveringizni sozlagan odam qiladi — men buni to'g'ridan-to'g'ri dastur ichiga qo'sha olmayman.
- **Bu hali ham "dasturchi rejimi" server.** Ekranda chiqadigan "Do not use it in a production deployment" ogohlantirishi shuning uchun. Kichik musobaqa (bitta faol ishtirokchi, bir necha hakam) uchun muammo bo'lmaydi, lekin juda ko'p odam bir vaqtda kirsa, `waitress` (Windows'da ham ishlaydi) yoki `gunicorn` (Linux) kabi "production" serverga o'tkazish tavsiya etiladi. Kerak bo'lsa, buni ham sozlab beraman.
- **Ma'lumotlar fayli (`savol_javob_v3.db`) doimiy saqlanadigan joyda turishi kerak.** Ba'zi bepul hosting xizmatlari (masalan, ba'zi "serverless" platformalar) har qayta ishga tushirishda fayllarni tozalab yuboradi — bunday joyda ma'lumotlar yo'qolib qolishi mumkin. Oddiy VPS (masalan DigitalOcean, Timeweb, Beget kabi) yoki doimiy diskli hosting bunga mos.
- Ishga tushirishda endi `PORT` muhit o'zgaruvchisi orqali portni tanlash mumkin (ko'p hosting xizmatlari buni talab qiladi): `PORT=80 python app.py`. Server rejimida brauzer o'zi ochilmasin desangiz, `NO_BROWSER=1` qo'shing.

Xohlasangiz, tanlagan hosting xizmatingizga moslab (masalan, qaysi provayder, qanday domen) qadamma-qadam sozlab berishim mumkin.

## Supabase bilan sinxronlash (ixtiyoriy)

Bu dastur kompyuterda, lokal tarmoq orqali ishlayveradi — Supabase shart emas. Lekin xohlasangiz, natijalarni (va savollar bankini) Supabase'ga zaxira/markazlashtirish uchun ulash mumkin: har ishtirokchi suhbatni tugatgach, natijasi avtomatik Supabase'ga yuboriladi.

**Sozlash:**
1. [supabase.com](https://supabase.com) da bepul loyiha oching.
2. Loyihada **SQL Editor** ni oching, `supabase_schema.sql` faylining ichini to'liq joylashtiring va "Run" bosing. Bu 3 ta jadval yaratadi: `yonalishlar`, `savollar`, `natijalar`.
3. Loyihada **Settings → API Keys** ga o'ting, **Project URL** ni va **Secret keys** bo'limidagi kalitni (eski loyihalarda "service_role" deb ataladi; "Publishable key" emas) nusxalab oling.
4. Dasturda **Supabase** menyusiga kirib, URL va kalitni joylashtiring, xohlasangiz filial nomini yozing, "Saqlash" bosing.

**Ishlatish:**
- Har ishtirokchi suhbatni tugatganda natijasi avtomatik yuboriladi. Internet bo'lmasa yoki xato ketsa, dastur ishlashda davom etadi — natija "Yuborilmagan natijalar" ro'yxatida qoladi, keyin "Qayta yuborish" bilan qo'lda jo'natasiz.
- "Savollar banki" bo'limidagi **"Supabase'dan yuklab olish"** tugmasi Supabase'dagi umumiy yo'nalish/savollarni shu kompyuterga qo'shadi (mavjudlarini takrorlamaydi). **"Mahalliy savollarni yuklash"** esa aksincha — shu kompyuterda kiritilgan savollarni Supabase'ga yuboradi. Bir nechta filial/kompyuter shu tarzda bitta umumiy savollar bankidan foydalanishi va natijalarini bitta joyga to'plashi mumkin.
- Bu maxfiy (secret) kalitni hech kimga bermang — u butun bazangizga to'liq kirish huquqini beradi.

**Muhim eslatma — turli joydan (internet orqali) kirish haqida:** Supabase faqat ma'lumotlarni saqlaydi/sinxronlaydi; u hakamlar yoki ishtirokchining sizning kompyuteringizga tarmoq orqali ulanishini ta'minlamaydi. Agar ular boshqa shahar yoki uydan, o'sha kunning o'zida jonli suhbatga qo'shilishi kerak bo'lsa, kompyuteringiz internetga "ochiq" bo'lishi kerak (masalan Cloudflare Tunnel yoki port forwarding orqali) — bu alohida sozlash, xohlasangiz shuni ham tayyorlab beraman.

## Har bir suhbat tugagach avtomatik saqlanadigan fayllar

Ishtirokchi suhbatni tugatgan zahoti, tizim quyidagilarni **avtomatik** diskka saqlaydi (hech narsa bosish shart emas):
- Shu ishtirokchining natija PDF fayli
- Yangilangan umumiy reyting PDF fayli

Bu fayllar dastur papkasidagi **`natijalar`** papkasida to'planadi (masalan `natijalar/0001-Bobur Aliyev.pdf`, `natijalar/reyting.pdf`). Natijalar juda muhim bo'lgani uchun bu — Supabase'dan tashqari yana bir, hech qanday internetga bog'liq bo'lmagan zaxira nusxa. Kompyuter xotirasi bunday PDF fayllar bilan deyarli to'lmaydi (har biri bir necha o'n kilobayt).

Bu saqlash (va Supabase'ga yuborish) orqa fonda amalga oshadi — hakam yoki ishtirokchining ekrani buning tugashini kutib turmaydi, tizim tezligiga ta'sir qilmaydi.

## Butunlay bulutda (brauzer orqali) ishlatish

Agar dasturni bitta kompyuterda emas, **istalgan joydan brauzer orqali** ishlatmoqchi bo'lsangiz, uni Supabase (ma'lumotlar bazasi) + Render (dasturning o'zi) bilan internetga chiqarish mumkin. Bu holda kompyuterda hech narsa o'rnatish shart emas — hamma (siz ham, hakamlar ham, ishtirokchi ham) faqat bitta havolani brauzerda ochadi.

**Halol ogohlantirish:** bu yo'l qulay, lekin **lokal versiyadan sekinroq** ishlaydi, chunki har bir amal internet orqali, boshqa mamlakatdagi serverga borib qaytadi. Agar hakamlar bitta xonada bo'lsa, lokal versiya (kompyuterda) tezroq va ishonchliroq. Bu yo'l hakamlar/ishtirokchi **turli joylarda** bo'lganda kerak bo'ladi.

### 1-qadam: Supabase'ni ma'lumotlar bazasi sifatida ulash

Bu safar Supabase shunchaki zaxira emas, balki dasturning **asosiy** bazasi bo'ladi.

1. Supabase loyihangizda (avvalgi qadamlarda ochgan) **Settings → Database** ga o'ting.
2. **Connection string** bo'limidan **"URI"** turini tanlang va nusxalang (masalan `postgresql://postgres:[PAROL]@db.xxxx.supabase.co:5432/postgres`). `[PAROL]` o'rniga loyiha yaratganda o'zingiz belgilagan baza parolini yozing.
3. Bu qatorni saqlab qo'ying — hostingga joylashtirganda kerak bo'ladi.

*(Eslatma: bu bosqichda `supabase_schema.sql` orqali yaratgan jadvallaringiz endi kerak emas — dastur o'zi ishga tushganda kerakli jadvallarni avtomatik yaratadi. Eski jadvallarni o'chirishingiz shart emas, ular shunchaki ishlatilmay qoladi.)*

### 2-qadam: Kodni GitHub'ga joylash

Agar sizda GitHub akkaunt bo'lsa, `savol-javob` papkasini yangi repository qilib yuklang (GitHub Desktop yoki `git` orqali). Bo'lmasa, ayting — buni ham qadamma-qadam ko'rsataman.

### 3-qadam: Render'da joylashtirish

1. [render.com](https://render.com) da ro'yxatdan o'ting (GitHub akkauntingiz bilan kirsa qulay).
2. **New → Web Service** ni tanlang, GitHub repongizni ulang.
3. Sozlamalarda:
   - **Build Command:** `pip install -r requirements-server.txt`
   - **Start Command:** (Procfile avtomatik aniqlanadi, alohida yozish shart emas)
4. **Environment Variables** bo'limiga qo'shing:
   - `DATABASE_URL` — 1-qadamda olgan Supabase ulanish qatori
   - `ADMIN_PASSWORD` — o'zingiz xohlagan boshlang'ich admin parol
5. **Create Web Service** ni bosing. Bir necha daqiqadan so'ng Render sizga doimiy havola beradi (masalan `https://savol-javob.onrender.com`) — shu havolani hamma ochadi.

**Yana bir eslatma:** bu qismni (Postgres/Supabase bilan ishlash kodini) men haqiqiy Supabase bazasida sinab ko'rolmadim — bu muhitda menda Postgres yo'q. Kod odatiy, hujjatlashtirilgan usul bilan yozilgan va lokal SQLite versiyasi to'liq sinovdan o'tgan, lekin joylashtirganingizda biron xato chiqsa, to'liq xabar matnini yuboring — birga tuzatamiz.
