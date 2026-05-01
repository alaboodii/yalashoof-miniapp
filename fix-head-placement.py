#!/usr/bin/env python3
"""Fix: the previous patch put 2 <head> sub_filters in / block; the __ext2
   block ended up with NO <head> filter. So Telegram padding + preconnect
   hints never get applied to player pages. This script:
   - Removes the orphan duplicate <head> filter from / block
   - Inserts a clean <head> filter into __ext2 block (telegram padding + preconnect)
"""
import re

p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

DUP_HEAD = re.compile(
    r"\n        sub_filter \"<head>\" \"<head><script>\(function\(\)\{try\{"
    r"var s=document\.createElement\('script'\);s\.src='https://telegram\.org/js/telegram-web-app\.js';"
    r"[^\"]*?body\{padding-top:100px!important;box-sizing:border-box\}'[^\"]*?"
    r"<link rel=\\\"dns-prefetch\\\"[^\"]*?\";\n"
)
c, n1 = DUP_HEAD.subn("", c)
print(f"[1] removed {n1} duplicate <head> filter from / block")

TG_HEAD = (
    '        sub_filter "<head>" "<head>'
    '<script>(function(){try{'
    "var s=document.createElement('script');"
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
    "(document.head||document.documentElement).appendChild(s);"
    "}catch(_){}})();</script>"
    '<link rel=\\"dns-prefetch\\" href=\\"https://fastly.live.brightcove.com\\">'
    '<link rel=\\"preconnect\\" href=\\"https://fastly.live.brightcove.com\\" crossorigin>'
    '<link rel=\\"dns-prefetch\\" href=\\"https://live2.d-kora.online\\">'
    '<link rel=\\"preconnect\\" href=\\"https://live2.d-kora.online\\" crossorigin>'
    '";\n'
)

EXT2_CLOSE_MARKER = '        sub_filter "</head>" "<style>.header-nav,#side-notification,.tawk-min-container,.server-switcher,iframe[src*=\\"tawk\\"],#_sm,#_smb'
idx = c.find(EXT2_CLOSE_MARKER)
if idx >= 0:
    c = c[:idx] + TG_HEAD + c[idx:]
    print("[2] <head> filter inserted into __ext2 block (telegram padding + preconnect)")
else:
    print("[2] FAIL: __ext2 </head> marker not found")

with open(p, "w") as f:
    f.write(c)
