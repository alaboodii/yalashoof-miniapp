#!/usr/bin/env python3
"""Add a Telegram-only padding-top + blue background extension to /shoot/.
   When the page is opened inside Telegram (window.Telegram.WebApp.platform set),
   we push the sticky header down by 60px and paint that gap blue so it merges
   visually with the existing site-header blue. Result: nothing extends above
   the close button.
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# Build the inline script (will be embedded inside an nginx double-quoted string)
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
    "st.textContent='html,body{background-color:#004ea8!important}'+"
    "'body{padding-top:60px!important;box-sizing:border-box}';"
    "(document.head||document.documentElement).appendChild(st);"
    "}catch(_){}};"
    '(document.head||document.documentElement).appendChild(s);'
    '}catch(_){}})();</script>'
)

ROOT_HEAD = 'sub_filter "<head>" "<head>'
if ROOT_HEAD in c and TG_PAD_SCRIPT not in c:
    c = c.replace(ROOT_HEAD, f'sub_filter "<head>" "<head>{TG_PAD_SCRIPT}', 1)
    print("[OK] Telegram padding+blue-bg script prepended to / block <head>")
elif TG_PAD_SCRIPT in c:
    print("[SKIP] already present")
else:
    print("[FAIL] / block <head> sub_filter marker not found")

with open(p, "w") as f:
    f.write(c)
