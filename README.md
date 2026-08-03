# Firdavs VIP Bot — Premium Anonymous Admin Chat

> 🤍 **@FirdavsVipBot** — Mukammal, kuchli, xavfsiz anonim chat bot.

Foydalanuvchilar siz (admin) bilan anonim tarzda suhbatlashadi. Boshqa foydalanuvchilar bir-birini ko'rmaydi. To'liq admin panel, statistika, anti-spam, ko'p tilli interfeys.

![Python](https://img.shields.io/badge/Python-3.11+-00E5FF?style=flat-square)
![aiogram](https://img.shields.io/badge/aiogram-3.7-8B5CF6?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-F472B6?style=flat-square)

---

## ✨ Funksiyalar

### 🎭 Foydalanuvchi
- `/start` — botni boshlash
- `/help` — yordam
- `/profile` — profilingiz, taxallus, statistika
- `/status` — admin onlaynmi
- `/clear` — tarixni tozalash
- `/stop` — suhbatni to'xtatish
- `/feedback` — baho berish (1-5 ⭐)
- 💬 **Xabaringiz → admin'ga boradi, admin javobi sizga qaytadi**

### 👑 Admin (siz)
- `/admin` — to'liq panel (PIN himoyalangan)
- 📊 **Statistika** — userlar, xabarlar, faollik
- 👥 **Foydalanuvchilar** — kim onlayn, kim faol
- 💬 **Inbox** — barcha suhbatlar
- 🔍 **Qidiruv** — user yoki xabar bo'yicha
- 📢 **Broadcast** — hammaga yoki segmentga
- 🚫 **Block / Unblock** — foydalanuvchini bloklash
- ⚠️ **Warning** — ogohlantirish
- 🏷 **Teglar** — VIP, regular, blocked
- 📈 **Analytics** — kunlik/haftalik/oylik
- 💾 **Export** — JSON/CSV
- 🤖 **Auto-reply** — siz bo'lmaganingizda
- 🔐 **PIN-kod** — admin panel himoyasi
- 🔔 **Push** — yangi xabar haqida bildirishnoma
- 🌙 **Toggle** — admin onlayn/offline

### 🔒 Xavfsizlik
- Anti-flood (rate limiting)
- Spam detection (kalit so'zlar)
- Bloklangan user tracking
- Audit log
- Auto-reply off (siz onlayn bo'lsangiz)

### 🌐 Ko'p tilli
- 🇺🇿 O'zbekcha
- 🇷🇺 Ruscha
- 🇬🇧 Inglizcha
- Foydalanuvchi tanlaydi, saqlanadi

---

## 🚀 O'rnatish

### 1. Repository'ni clone qiling
```bash
git clone https://github.com/KRYZENSYS/firdavsvipbot.git
cd firdavsvipbot
```

### 2. Virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki Windows: venv\Scripts\activate
```

### 3. Kutubxonalarni o'rnating
```bash
pip install -r requirements.txt
```

### 4. Sozlamalarni kiriting
```bash
cp .env.example .env
# .env ni tahrirlang: BOT_TOKEN, ADMIN_ID, ADMIN_PIN
```

**Token olish:**
1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. Nom: **Firdavs VIP Bot**
3. Username: **FirdavsVipBot**
4. Token olasiz → `.env` ga qo'ying

**Sizning ID:**
1. [@userinfobot](https://t.me/userinfobot) → `/start`
2. ID ko'rinadi → `.env` ga qo'ying

**Admin PIN:**
- 4-6 raqamli parol o'ylab toping (masalan: `2026`)

### 5. Ishga tushiring
```bash
python bot.py
```

---

## ☁️ Deploy (Render.com — bepul)

1. [render.com](https://render.com) → New → Background Worker
2. Repository: `KRYZENSYS/firdavsvipbot`
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Environment variables qo'shing (`.env` dan)
6. **Disk:** `/data` ni persistent qiling (SQLite uchun)
7. Deploy ✅

---

## 📂 Tuzilma

```
firdavsvipbot/
├── bot.py                  # Asosiy bot
├── config.py               # Sozlamalar
├── requirements.txt        # Kutubxonalar
├── render.yaml             # Render konfiguratsiya
├── .env.example            # Muhit o'zgaruvchilari
├── README.md               # Hujjat
├── database/
│   ├── __init__.py
│   ├── db.py               # DB ulanish
│   └── models.py           # Modellar
├── handlers/
│   ├── __init__.py
│   ├── user.py             # User handlerlar
│   ├── admin.py            # Admin panel
│   └── errors.py           # Xatolar
├── middlewares/
│   ├── __init__.py
│   ├── antiflood.py        # Anti-spam
│   └── auth.py             # Admin auth
├── keyboards/
│   ├── __init__.py
│   ├── inline.py           # Inline tugmalar
│   └── reply.py            # Reply tugmalar
├── utils/
│   ├── __init__.py
│   ├── states.py           # FSM holatlar
│   ├── helpers.py          # Yordamchilar
│   ├── analytics.py        # Statistika
│   └── i18n.py             # Tarjimalar
├── locales/
│   ├── uz.json
│   ├── ru.json
│   └── en.json
└── data/                   # SQLite (gitignore)
```

---

## 🧪 Tekshirish

- `/start` — javob berishi kerak
- `/help` — ko'rsatmalar
- `/profile` — taxallus ko'rinadi
- Biror xabar yozing → admin'ga boradi
- Admin'ning `/admin` ishlashi kerak (PIN bilan)

---

## 📜 Litsenziya

MIT — © 2026 Firdavs VIP. All rights reserved.

**Yaratuvchi:** Firdavs (KRYZENSYS)
**Repo:** https://github.com/KRYZENSYS/firdavsvipbot
**Bot:** https://t.me/FirdavsVipBot
