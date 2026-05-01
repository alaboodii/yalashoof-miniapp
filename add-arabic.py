#!/usr/bin/env python3
"""Add Arabic translation sub_filter rules to the hesgoal yala.zaboni.store config."""
path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# (pattern, replacement) — longer English phrases FIRST so they match before short tokens
TRANSLATIONS = [
    # === HTML attributes — RTL + Arabic locale ===
    ('lang="en-GB"',  'lang="ar" dir="rtl"'),
    ('lang="en-US"',  'lang="ar" dir="rtl"'),
    ('lang="en"',      'lang="ar" dir="rtl"'),
    ('<html lang="ar" dir="rtl" dir="rtl"', '<html lang="ar" dir="rtl"'),  # cleanup if double

    # === Long phrases ===
    ("Watch Free Live Soccer Streams HD 2026",  "بث مباشر للمباريات بجودة عالية 2026"),
    ("Watch Free Live Soccer Streams HD",       "بث مباشر للمباريات بجودة عالية"),
    ("Watch Free Live Soccer Streams",          "بث مباشر للمباريات"),
    ("Free Live Soccer Streams",                "بث مباشر للمباريات"),
    ("Live Scores & Real-Time Updates",         "نتائج مباشرة وتحديثات لحظية"),
    ("All Major Leagues Covered",               "تغطية شاملة للدوريات الكبرى"),
    ("Works on Every Device",                   "يعمل على جميع الأجهزة"),
    ("Free Soccer Streams HD",                  "بث مجاني عالي الجودة"),
    ("Football Streams Free",                   "بث مباريات مجاني"),
    ("Free Football Streams",                   "بث مجاني للمباريات"),
    ("Reddit Soccer Streams",                   "بث المباريات"),
    ("Skip to main content",                    "انتقل إلى المحتوى الرئيسي"),
    ("HesGoal site navigation",                 "قائمة موقع العبودي تي في"),
    ("All rights reserved",                     "جميع الحقوق محفوظة"),
    ("minute-by-minute updates and goal alerts", "تحديثات لحظة بلحظة وتنبيهات الأهداف"),
    ("no app download needed",                  "بدون تطبيق"),
    ("no app download or plugin needed",        "بدون تطبيق أو إضافات"),
    ("fully mobile-optimised",                  "مُحسَّن للهواتف بالكامل"),
    ("fully responsive",                        "متجاوب بالكامل"),
    ("works on any device",                     "يعمل على أي جهاز"),
    ("works on all devices",                    "يعمل على جميع الأجهزة"),
    ("Frequently Asked Questions",              "الأسئلة الشائعة"),
    ("Live scores",                             "نتائج مباشرة"),

    # === Leagues ===
    ("Premier League",       "الدوري الإنجليزي"),
    ("Champions League",     "دوري أبطال أوروبا"),
    ("Europa League",        "الدوري الأوروبي"),
    ("UEFA Champions League","دوري أبطال أوروبا"),
    ("Bundesliga",           "الدوري الألماني"),
    ("La Liga",              "الدوري الإسباني"),
    ("Serie A",              "الدوري الإيطالي"),
    ("Ligue 1",              "الدوري الفرنسي"),
    ("Eredivisie",           "الدوري الهولندي"),
    ("Primeira Liga",        "الدوري البرتغالي"),
    ("Saudi Pro League",     "دوري روشن السعودي"),
    ("Saudi League",         "الدوري السعودي"),
    ("Egyptian Premier League","الدوري المصري"),
    ("MLS",                  "دوري MLS"),
    ("FA Cup",               "كأس الاتحاد الإنجليزي"),
    ("Copa del Rey",         "كأس ملك إسبانيا"),
    ("Coppa Italia",         "كأس إيطاليا"),
    ("DFB Pokal",            "كأس ألمانيا"),
    ("World Cup",            "كأس العالم"),
    ("Euro",                 "بطولة أوروبا"),
    ("AFC Champions League", "دوري أبطال آسيا"),
    ("CAF Champions League", "دوري أبطال أفريقيا"),
    ("AFCON",                "كأس أمم أفريقيا"),

    # === Common UI words (do these LAST so phrases above hit first) ===
    (">Today<",          ">اليوم<"),
    (">Yesterday<",      ">الأمس<"),
    (">Tomorrow<",       ">الغد<"),
    (">Live<",           ">مباشر<"),
    (">LIVE<",           ">مباشر<"),
    (">Schedule<",       ">جدول المباريات<"),
    (">Matches<",        ">المباريات<"),
    (">Watch Now<",      ">شاهد الآن<"),
    (">WATCH NOW<",      ">شاهد الآن<"),
    (">Watch<",          ">شاهد<"),
    (">Stream<",         ">بث<"),
    (">Streams<",        ">بثوث<"),
    (">FAQ<",            ">أسئلة شائعة<"),
    (">About<",          ">حول<"),
    (">Home<",           ">الرئيسية<"),
    (">Contact<",        ">اتصل بنا<"),
    (">Privacy<",        ">الخصوصية<"),
    (">Terms<",          ">الشروط<"),
    (" vs ",             " ضد "),
    (" VS ",             " ضد "),
    (">vs<",             ">ضد<"),
    (">VS<",             ">ضد<"),
    (">FT<",             ">انتهت<"),
    (">HT<",             ">شوط أول<"),
    (">Postponed<",      ">مؤجلة<"),
    (">Cancelled<",      ">ملغية<"),
    (">Finished<",       ">انتهت<"),
    (">Upcoming<",       ">قادمة<"),
    (">Soon<",           ">قريباً<"),
    (">No matches<",     ">لا توجد مباريات<"),
    (">Loading...<",     ">جاري التحميل...<"),
    ("Stadium:",         "الملعب:"),
    ("Referee:",         "الحكم:"),
    ("Channel:",         "القناة:"),

    # FAQ-style
    ("Yes.", "نعم."),
    ("Does HesGoal work on iPhone and Android?", "هل العبودي تي في يعمل على iPhone و Android؟"),
    ("What is the difference between HesGoal and HesGoals?", "ما الفرق بين العبودي تي في وما يشبهه؟"),
    ("Does HesGoal work on mobile?", "هل العبودي تي في يعمل على الجوال؟"),

    # Hero descriptors
    ("HesGoal streams Premier League, Champions League, La Liga, Serie A &amp; 50+ competitions",
     "العبودي تي في يبث الدوري الإنجليزي ودوري أبطال أوروبا والدوري الإسباني والدوري الإيطالي و50+ بطولة"),

    # Feature card descriptions
    ("HesGoal TV is fully optimised for mobile, tablet and desktop — no app needed",
     "العبودي تي في مُحسَّن بالكامل للجوال والتابلت والكمبيوتر — بدون تطبيق"),
    ("HesGoal TV is fully responsive and works on all devices — iPhone, Android, tablet and desktop — with no app download needed",
     "العبودي تي في متجاوب بالكامل ويعمل على جميع الأجهزة — iPhone و Android والتابلت والكمبيوتر — بدون تطبيق"),
    ("HesGoal TV is fully mobile-optimised and works on any device — iPhone, Android, tablet or desktop — with no app download or plugin needed",
     "العبودي تي في مُحسَّن للجوال ويعمل على أي جهاز — iPhone و Android والتابلت أو الكمبيوتر — بدون تطبيق أو إضافات"),

    # Iframe titles etc.
    ('aria-label="HesGoal',  'aria-label="العبودي تي في'),
    ('alt="HesGoal',         'alt="العبودي تي في'),
    ('title="HesGoal',       'title="العبودي تي في'),
]

# Build the sub_filter snippet
lines = ["        # === Arabic translations ==="]
for src, dst in TRANSLATIONS:
    # Escape any double quotes in src/dst for nginx string literal
    src_esc = src.replace('"', '\\"')
    dst_esc = dst.replace('"', '\\"')
    lines.append('        sub_filter "' + src_esc + '" "' + dst_esc + '";')
arabic_block = "\n".join(lines) + "\n\n"

# Insert after the brand rename rules (before the head injection)
anchor = "        # === Inject styling + dark default + custom font + logo replace + footer ==="
if "Arabic translations" not in content and anchor in content:
    content = content.replace(anchor, arabic_block + anchor, 1)
    print("inserted")
else:
    print("already present or anchor missing")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
