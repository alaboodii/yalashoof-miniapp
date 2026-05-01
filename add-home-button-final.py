#!/usr/bin/env python3
"""Add a centered home button at the very top of player pages (inside Telegram
   the user wants a quick way to return to the matches list).
   - Top-center fixed position, sits inside the 90px padding area
   - Only injected on player pages (__ext2 block)
   - Only visible on top window (auto-removes inside iframes)
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# Find the __ext2 </body> sub_filter (the wrap_v10.js loader) and prepend the button.
OLD_BODY = ('sub_filter "</body>" "<img src=x style=display:none '
            'onerror=\\"this.remove();var s=document.createElement(\'script\');'
            's.src=\'/__yala_wrap_v10.js?v=12\';s.defer=true;'
            '(document.head||document.documentElement).appendChild(s)\\"></body>";')

HOME_HTML = (
    '<a id=\\"alab-home\\" href=\\"/shoot/\\">'
    '<span class=\\"alab-home-icon\\">⌂</span>'
    '<span class=\\"alab-home-label\\">الصفحة الرئيسية</span>'
    '</a>'
    '<script>(function(){try{if(window.self!==window.top){var b=document.getElementById(\'alab-home\');if(b)b.remove();}}catch(_){}})();</script>'
    '<style>'
    # Top-center fixed FAB. Sits inside the 90px telegram padding area so it does
    # not cover any in-page content. z-index above everything.
    '#alab-home{position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:2147483647;'
    'display:inline-flex;align-items:center;gap:8px;'
    'padding:9px 18px;border-radius:999px;text-decoration:none;'
    'background:linear-gradient(135deg,#b91c1c 0%,#7f1d1d 100%);'
    'box-shadow:0 4px 14px rgba(185,28,28,0.45),0 0 0 1px rgba(255,255,255,0.08);'
    "font-family:'IBM Plex Sans Arabic','Poppins','Segoe UI',sans-serif;"
    'transition:transform .15s ease,box-shadow .15s ease;cursor:pointer}'
    '#alab-home:active{transform:translateX(-50%) translateY(1px)}'
    '#alab-home:hover{transform:translateX(-50%) translateY(-1px);'
    'box-shadow:0 6px 18px rgba(185,28,28,0.6),0 0 0 1px rgba(255,255,255,0.15)}'
    '#alab-home .alab-home-icon{font-size:17px;line-height:1;color:#fff;font-weight:700}'
    '#alab-home .alab-home-label{font-weight:600;font-size:14px;color:#fff;direction:rtl;line-height:1}'
    '@media (max-width:600px){#alab-home{padding:8px 14px;gap:7px}'
    '#alab-home .alab-home-icon{font-size:16px}'
    '#alab-home .alab-home-label{font-size:13px}}'
    '</style>'
)

NEW_BODY = ('sub_filter "</body>" "' + HOME_HTML +
            '<img src=x style=display:none '
            'onerror=\\"this.remove();var s=document.createElement(\'script\');'
            's.src=\'/__yala_wrap_v10.js?v=12\';s.defer=true;'
            '(document.head||document.documentElement).appendChild(s)\\"></body>";')

if OLD_BODY in c:
    c = c.replace(OLD_BODY, NEW_BODY, 1)
    print("[OK] home button injected at top-center of player pages")
else:
    print("[FAIL] </body> marker not found")

with open(p, "w") as f:
    f.write(c)
