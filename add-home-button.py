#!/usr/bin/env python3
"""Cancel back-button fix attempts and inject a centered home button on player pages.
   - Removes any popstate-escape / pushState-block scripts we added.
   - Adds a fixed-position 'الصفحة الرئيسية' button at the top-center of player pages
     branded with the Alaboodi TV logo. Clicking it navigates to /shoot/ directly.
"""
import re, shutil, time

p = "/etc/nginx/sites-enabled/yala.zaboni.store"
shutil.copy(p, "/root/yala.zaboni.store.pre-home-btn." + str(int(time.time())))
with open(p) as f:
    c = f.read()

# 1) Remove our injected back-button defense script entirely.
SCRIPT_RE = re.compile(r"<script>\(function\(\)\{try\{var op=history\.pushState[^<]*?\}\)\(\);</script>")
c, n1 = SCRIPT_RE.subn("", c)
print(f"[1] removed {n1} back-defense script block(s)")

# 2) Inject home button before </body> in the __ext2 location block.
# The </body> sub_filter currently injects a wrap_v10.js loader; we prepend our button HTML+CSS.
# Use a stable, unambiguous marker — the </body> filter line in __ext2.
OLD_BODY = ('sub_filter "</body>" "<img src=x style=display:none '
            'onerror=\\"this.remove();var s=document.createElement(\'script\');'
            's.src=\'/__yala_wrap_v10.js\';s.defer=true;'
            '(document.head||document.documentElement).appendChild(s)\\"></body>";')

# Home button HTML + CSS (escaped for nginx string literal)
HOME_HTML = (
    '<a id=\\"alab-home\\" href=\\"/shoot/\\">'
    '<span class=\\"alab-home-logo\\">Alaboodi TV</span>'
    '<span class=\\"alab-home-label\\">الصفحة الرئيسية</span>'
    '</a>'
    '<style>'
    '#alab-home{position:fixed;top:14px;left:50%;transform:translateX(-50%);'
    'z-index:2147483646;display:inline-flex;align-items:center;gap:10px;'
    'padding:10px 20px;border-radius:999px;text-decoration:none;'
    'background:linear-gradient(135deg,#b91c1c 0%,#7f1d1d 100%);'
    'box-shadow:0 4px 16px rgba(185,28,28,0.45),0 0 0 1px rgba(255,255,255,0.08);'
    "font-family:'Poppins','IBM Plex Sans Arabic','Segoe UI',sans-serif;"
    'transition:transform .15s ease,box-shadow .15s ease;cursor:pointer}'
    '#alab-home:hover{transform:translateX(-50%) translateY(-1px);'
    'box-shadow:0 6px 20px rgba(185,28,28,0.6),0 0 0 1px rgba(255,255,255,0.15)}'
    '#alab-home .alab-home-logo{font-weight:700;font-size:14px;color:#fff;letter-spacing:0.5px;'
    'direction:ltr;padding:4px 10px;border-radius:6px;background:rgba(0,0,0,0.25)}'
    '#alab-home .alab-home-label{font-weight:600;font-size:14px;color:#fff;direction:rtl}'
    '@media (max-width:600px){#alab-home{padding:8px 14px;gap:8px}'
    '#alab-home .alab-home-logo{font-size:12px;padding:3px 8px}'
    '#alab-home .alab-home-label{font-size:13px}}'
    '</style>'
)

NEW_BODY = ('sub_filter "</body>" "' + HOME_HTML +
            '<img src=x style=display:none '
            'onerror=\\"this.remove();var s=document.createElement(\'script\');'
            's.src=\'/__yala_wrap_v10.js\';s.defer=true;'
            '(document.head||document.documentElement).appendChild(s)\\"></body>";')

if OLD_BODY in c:
    c = c.replace(OLD_BODY, NEW_BODY, 1)
    print("[2] home button injected before </body>")
else:
    print("[2] FAIL: </body> marker not found")

with open(p, "w") as f:
    f.write(c)
