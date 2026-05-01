#!/usr/bin/env python3
"""Re-add ONLY the home button — but as a bottom-left floating action button (FAB).
   This avoids:
   - body padding (which broke layout / hid player on Telegram)
   - overlap with the 'تحديث تلقائي' notification at top
   - any pushState/popstate scripts (those broke navigation)
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# Find the original </body> sub_filter in __ext2 location block
OLD_BODY = ('sub_filter "</body>" "<img src=x style=display:none '
            'onerror=\\"this.remove();var s=document.createElement(\'script\');'
            's.src=\'/__yala_wrap_v10.js\';s.defer=true;'
            '(document.head||document.documentElement).appendChild(s)\\"></body>";')

# Home button: fixed bottom-left, compact, with Alaboodi TV branding.
# Wrapped in iframe-detect that ONLY removes itself (does not touch other DOM/JS).
HOME_HTML = (
    '<a id=\\"alab-home\\" href=\\"/shoot/\\">'
    '<span class=\\"alab-home-icon\\">⌂</span>'
    '<span class=\\"alab-home-label\\">الصفحة الرئيسية</span>'
    '</a>'
    '<script>(function(){try{if(window.self!==window.top){var b=document.getElementById(\'alab-home\');if(b)b.remove();}}catch(_){}})();</script>'
    '<style>'
    # Bottom-left FAB — does not push any content, does not overlap player or notification
    '#alab-home{position:fixed;bottom:18px;left:18px;z-index:2147483647;'
    'display:inline-flex;align-items:center;gap:8px;'
    'padding:10px 16px;border-radius:999px;text-decoration:none;'
    'background:linear-gradient(135deg,#b91c1c 0%,#7f1d1d 100%);'
    'box-shadow:0 4px 16px rgba(185,28,28,0.45),0 0 0 1px rgba(255,255,255,0.08);'
    "font-family:'IBM Plex Sans Arabic','Poppins','Segoe UI',sans-serif;"
    'transition:transform .15s ease,box-shadow .15s ease;cursor:pointer}'
    '#alab-home:hover{transform:translateY(-2px);'
    'box-shadow:0 6px 20px rgba(185,28,28,0.6),0 0 0 1px rgba(255,255,255,0.15)}'
    '#alab-home .alab-home-icon{font-size:18px;line-height:1;color:#fff;font-weight:700}'
    '#alab-home .alab-home-label{font-weight:600;font-size:14px;color:#fff;direction:rtl;line-height:1}'
    '@media (max-width:600px){#alab-home{bottom:14px;left:14px;padding:9px 14px;gap:7px}'
    '#alab-home .alab-home-icon{font-size:16px}'
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
    print("[OK] home button (bottom-left FAB) injected")
else:
    print("[FAIL] </body> marker not found")

with open(p, "w") as f:
    f.write(c)
