#!/usr/bin/env python3
"""1) Add Telegram-only padding to player pages (__ext2 block) so content
      starts below the close button — same scheme as /shoot/.
   2) Lift the home button up: bottom: 18px -> 50px so it does not sit at
      the very edge of the viewport.
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# 1) Add <head> sub_filter to __ext2 block. The block currently has only a
#    </head> filter. We need to insert a new <head> filter with the Telegram
#    padding script before the </head> filter.
TG_PAD_SCRIPT = (
    '<script>(function(){try{'
    'var s=document.createElement(\'script\');'
    "s.src='https://telegram.org/js/telegram-web-app.js';"
    "s.onload=function(){try{"
    "var tg=window.Telegram&&window.Telegram.WebApp;"
    "if(!tg||!tg.platform)return;"
    "try{tg.ready();}catch(_){}"
    "try{tg.expand();}catch(_){}"
    "var st=document.createElement('style');"
    "st.textContent='body{padding-top:100px!important;box-sizing:border-box}';"
    "(document.head||document.documentElement).appendChild(st);"
    "}catch(_){}};"
    '(document.head||document.documentElement).appendChild(s);'
    '}catch(_){}})();</script>'
)

# Find the EXACT __ext2 </head> sub_filter line and insert a <head> filter just BEFORE it.
# The __ext2 </head> filter starts with this fixed prefix:
EXT2_CLOSING_HEAD_LINE_PREFIX = '        sub_filter "</head>" "<style>.header-nav,#side-notification,.tawk-min-container'

new_head_line = f'        sub_filter "<head>" "<head>{TG_PAD_SCRIPT}";\n'

idx = c.find(EXT2_CLOSING_HEAD_LINE_PREFIX)
if idx >= 0:
    # Check it's not already present
    line_above_start = c.rfind("\n", 0, idx) + 1
    line_above = c[max(0, line_above_start-300):idx]
    if 'telegram-web-app.js' not in line_above:
        c = c[:idx] + new_head_line + c[idx:]
        print("[1] <head> sub_filter (Telegram padding) inserted before __ext2 </head> filter")
    else:
        print("[1] Already present — skipping")
else:
    print("[1] FAIL: __ext2 </head> filter line not found")

# 2) Lift home button: bottom:18px -> 50px (and the @media-mobile bottom:14px -> 40px)
c = c.replace(
    "#alab-home{position:fixed;bottom:18px;left:50%",
    "#alab-home{position:fixed;bottom:50px;left:50%",
    1,
)
c = c.replace(
    "@media (max-width:600px){#alab-home{bottom:14px;",
    "@media (max-width:600px){#alab-home{bottom:40px;",
    1,
)
print("[2] Home button lifted: bottom 18->50px (mobile 14->40px)")

with open(p, "w") as f:
    f.write(c)
