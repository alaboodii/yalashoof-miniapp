# Yala/Alaboodi TV — Snapshot 2026-05-01

نسخة احتياطية من الحالة المستقرّة بعد تحسينات اليوم.

## 📦 الملفّات المحفوظة

| الملف | المسار على السيرفر |
|---|---|
| `yala.zaboni.store.conf` | `/etc/nginx/sites-enabled/yala.zaboni.store` |
| `__yala_wrap_v10.js` | `/var/www/yala.zaboni.store/__yala_wrap_v10.js` |
| `__yala_styles.css` | `/var/www/yala.zaboni.store/__yala_styles.css` |

## 🛠️ التغييرات المطبَّقة اليوم

### 1) البقاء على النطاق
- **`proxy_redirect`** wildcard في كلا blockين (`/` و `/__ext2?/`):
  ```nginx
  proxy_redirect ~^https?://([^/]+)(/.*)?$ /__ext2/$1$2;
  ```
- يلتقط أي 30x redirect من السيرفر الخارجي ويُعيد كتابة الـ Location header ليبقى داخل `yala.zaboni.store`.

### 2) إخفاء الإعلانات والتشويش على صفحة المشغّل
في `</head>` sub_filter داخل `__ext2` block:
- النافذة المنبثقة "اشترك في تيليجرام": `#_sm`, `#_smb`, `[id^="_sm"]`
- إطارات الإعلانات: `iframe[src*="ads"]`, `doubleclick`, `googlesyndication`, `eruptpriority`, `propeller`, `adsterra`, `popcash`, `adcash`, `onclickads`, `exoclick`, `juicy`
- **شريط العنوان فوق المشغّل** (مثل "On Sport Max"): `.bg-sl-block-head{display:none}`
- **الكابشن الوصفي تحت المشغّل**: `.post-body > p, h1-h6, ul, ol, blockquote, figure, pre, table, hr` (الـ player wrapper يبقى ظاهراً)

### 3) الوضع النهاري افتراضي
- إزالة `sub_filter "<html " "<html class=\"dark\" "` من / block.
- المستخدم يبقى قادراً على التبديل لليلي يدوياً عبر زر القمر.

### 4) تكامل تيليجرام WebApp
سكربت يُحقن في `<head>` لكلا الـ block`/` و`__ext2`:
```js
(function(){try{
  var s = document.createElement('script');
  s.src = 'https://telegram.org/js/telegram-web-app.js';
  s.onload = function(){try{
    var tg = window.Telegram && window.Telegram.WebApp;
    if (!tg || !tg.platform) return;
    try { tg.ready(); } catch(_){}
    try { tg.expand(); } catch(_){}
    var st = document.createElement('style');
    st.textContent = 'body{padding-top:100px!important;box-sizing:border-box}'
                   + 'html,body{background-color:#004ea8!important}'; // /shoot/ only
    (document.head||document.documentElement).appendChild(st);
  }catch(_){}};
  (document.head||document.documentElement).appendChild(s);
}catch(_){}})();
```
- `tg.ready()` يُختفي شريط التحميل الأزرق في تيليجرام مبكراً
- `tg.expand()` يجعل التطبيق على كامل الشاشة
- `padding-top: 100px` يُنزّل المحتوى تحت زرّ "إغلاق"
- خلفية زرقاء `#004ea8` تمتدّ للأعلى على /shoot/ (تطابق لون الـ header)

### 5) زر "الصفحة الرئيسية"
على صفحات المشغّل فقط (`__ext2` block):
- موقع: `position: fixed; bottom: 50px; left: 50%; transform: translateX(-50%);` (وسط أسفل الشاشة)
- موبايل (≤600px): `bottom: 40px`
- مخفي داخل iframe (لا يظهر إلا في الصفحة الأم)
- يُحوّل إلى `/shoot/`

### 6) تسريع تحميل صفحة المشغّل
- **`<script src=... defer>`** بدل `<img onerror>` لتحميل `__yala_wrap_v10.js`
- **`dns-prefetch` + `preconnect`** لـ:
  - `https://fastly.live.brightcove.com` (CDN البث)
  - `https://live2.d-kora.online` (مزوّد المشغّل)
- يوفّر 50-200ms من DNS lookup + TCP/TLS handshake في تيليجرام WebView على iOS

### 7) عكس الأمان لـ wrap_v10.js
- إزالة `Object.defineProperty` على `window.location.href`, `window.open`, `window.Notification`
- iOS Telegram WebView (WKWebView) كان يفشل صامتاً مع هذه الـ overrides ويكسر النقر على الروابط
- الـ click handler و DOM walker (للحماية من الإعلانات) ما زالا فعّالين

## 🧪 السلوك المتوقّع

| الإجراء | المتصفّح | تيليجرام |
|---|---|---|
| فتح /shoot/ | يعمل، وضع نهاري | يعمل، وضع نهاري + مساحة زرقاء 100px |
| النقر على مباراة | ينتقل للمشغّل، يبقى على yala.zaboni.store | نفس السلوك (سرعة محسّنة) |
| المشغّل | يفتح فوراً، بدون إعلانات | شريط التحميل يختفي بسرعة، الفيديو يبدأ |
| زر العودة للرئيسية | متوفّر أسفل الوسط | متوفّر أسفل الوسط |

## ♻️ الاسترجاع
لاسترجاع هذه الحالة:
```bash
scp yala-2026-05-01/* root@178.238.230.179:/tmp/
ssh root@178.238.230.179 '
  cp /tmp/yala.zaboni.store.conf /etc/nginx/sites-enabled/yala.zaboni.store
  cp /tmp/__yala_wrap_v10.js /var/www/yala.zaboni.store/__yala_wrap_v10.js
  cp /tmp/__yala_styles.css /var/www/yala.zaboni.store/__yala_styles.css
  nginx -t && systemctl reload nginx
'
```

## 📝 سكربتات الـ patches المستخدمة (في مجلد المشروع)
- `add-telegram-blue-pad.py` — إضافة padding+خلفية زرقاء لـ /shoot/
- `add-telegram-pad-player.py` — إضافة padding للمشغّل + رفع زر الرئيسية
- `add-home-button-final.py` — زر الصفحة الرئيسية أسفل الوسط
- `reset-and-bottom-button.py` — استعادة كاملة + زر سفلي
- `speed-up-player.py` — تسريع المشغّل (preconnect + script defer)
- `fix-head-placement.py` — تصحيح موقع `<head>` filters
- `soften-wrap-v10.py` — إزالة الـ overrides الخطيرة من wrap.js
