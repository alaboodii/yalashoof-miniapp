#!/usr/bin/env python3
"""Fix: Telegram in-app loading bar gets stuck after navigating to a player page.
   Cause: Telegram WebApp dismisses its loading indicator only when the page
   calls Telegram.WebApp.ready(). Currently that call lives inside wrap_v10.js
   which is loaded with `defer`, so on slow iOS Telegram WebView it can fire
   too late — and if the page also has long-lived sub-resources (HLS iframe),
   `window.onload` never fires either, leaving the bar stuck.
   Fix: inject telegram-web-app.js + immediate ready()/expand() inline in <head>
   on BOTH /shoot/ (yshootlive proxy block) AND /__ext2/ (player block).
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# Snippet that loads telegram-web-app.js and calls ready() immediately on load.
# Goes inside a "<head>" sub_filter so it runs before any other script.
TG_INIT = (
    '<script>(function(){try{'
    'var s=document.createElement(\'script\');'
    "s.src='https://telegram.org/js/telegram-web-app.js';"
    "s.onload=function(){try{var tg=window.Telegram&&window.Telegram.WebApp;"
    "if(tg){try{tg.ready();}catch(_){}try{tg.expand();}catch(_){}}}catch(_){}};"
    '(document.head||document.documentElement).appendChild(s);'
    '}catch(_){}})();</script>'
)

# 1) Add to / block (yshootlive). It already has a <head> sub_filter — prepend our script.
ROOT_HEAD = 'sub_filter "<head>" "<head>'
if ROOT_HEAD in c:
    c = c.replace(ROOT_HEAD, f'sub_filter "<head>" "<head>{TG_INIT}', 1)
    print("[1] Telegram early-ready script prepended to / block <head>")
else:
    print("[1] / block <head> sub_filter not found")

# 2) Add NEW <head> sub_filter to __ext2 block (it currently only has </head>).
EXT2_BODY = ('sub_filter "</body>" "<img src=x style=display:none '
             'onerror=\\"this.remove();var s=document.createElement(\'script\');'
             's.src=\'/__yala_wrap_v10.js?v=12\';s.defer=true;'
             '(document.head||document.documentElement).appendChild(s)\\"></body>";')
EXT2_HEAD_INSERT = (
    f'sub_filter "<head>" "<head>{TG_INIT}";\n        '
    + EXT2_BODY
)
if EXT2_BODY in c:
    c = c.replace(EXT2_BODY, EXT2_HEAD_INSERT, 1)
    print("[2] <head> sub_filter (telegram early-ready) added to __ext2 block")
else:
    print("[2] __ext2 </body> marker not found")

with open(p, "w") as f:
    f.write(c)
