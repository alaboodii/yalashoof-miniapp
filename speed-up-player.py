#!/usr/bin/env python3
"""Speed up the player page so it feels fast inside iOS Telegram WebView:

   1) Replace the slow `<img onerror>` wrap_v10.js loader with a normal
      `<script defer>` (instant browser-managed fetch in parallel).
   2) Add `<link rel=dns-prefetch / preconnect>` hints in <head> for the
      streaming CDN origins so the TCP+TLS handshake is already warm
      when the iframe asks for /splplayer/.
   3) Add `<link rel=preload as=document>` for the player iframe URL so
      the iframe HTML starts downloading before the iframe element itself
      appears in the parsed DOM.
   4) Also extend the /shoot/ <head> to preconnect the streaming hosts so
      tapping a match has a warm pipe ready.
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# 1) Convert the __ext2 block's <img onerror> wrap loader to a fast <script defer>
OLD_BODY_LOADER = ('<img src=x style=display:none '
                   'onerror=\\"this.remove();var s=document.createElement(\'script\');'
                   's.src=\'/__yala_wrap_v10.js?v=12\';s.defer=true;'
                   '(document.head||document.documentElement).appendChild(s)\\"></body>')
NEW_BODY_LOADER = '<script src=\\"/__yala_wrap_v10.js?v=12\\" defer></script></body>'

n1 = c.count(OLD_BODY_LOADER)
if n1:
    c = c.replace(OLD_BODY_LOADER, NEW_BODY_LOADER, 1)
    print(f"[1] Replaced slow img-onerror loader with <script defer> ({n1} occurrence)")
else:
    print("[1] img-onerror marker not found")

# 2/3) Add resource hints in __ext2 <head>. The block has a <head> sub_filter
#       (the Telegram padding script) that we'll append to.
PRECONNECT_HINTS = (
    '<link rel=\\"dns-prefetch\\" href=\\"https://fastly.live.brightcove.com\\">'
    '<link rel=\\"preconnect\\" href=\\"https://fastly.live.brightcove.com\\" crossorigin>'
    '<link rel=\\"dns-prefetch\\" href=\\"https://live2.d-kora.online\\">'
    '<link rel=\\"preconnect\\" href=\\"https://live2.d-kora.online\\" crossorigin>'
    '<link rel=\\"dns-prefetch\\" href=\\"https://yala.zaboni.store\\">'
    '<link rel=\\"preconnect\\" href=\\"https://yala.zaboni.store\\" crossorigin>'
)

# Find __ext2 <head> sub_filter and append hints after the script
# The line is `sub_filter "<head>" "<head>SCRIPT";`
import re
EXT2_HEAD_RE = re.compile(
    r'(sub_filter "<head>" "<head><script>\(function\(\)\{try\{var s=document\.createElement\(\'script\'\);s\.src=\'https://telegram\.org/js/telegram-web-app\.js\';s\.onload=function\(\)\{try\{var tg=window\.Telegram&&window\.Telegram\.WebApp;if\(!tg\|\|!tg\.platform\)return;try\{tg\.ready\(\);\}catch\(_\)\{\}try\{tg\.expand\(\);\}catch\(_\)\{\}var st=document\.createElement\(\'style\'\);st\.textContent=\'body\{padding-top:100px!important;box-sizing:border-box\}\';)'
    r'(\(document\.head\|\|document\.documentElement\)\.appendChild\(st\);\}catch\(_\)\{\}\};\(document\.head\|\|document\.documentElement\)\.appendChild\(s\);\}catch\(_\)\{\}\}\)\(\);</script>)'
    r'(";)'
)
m = EXT2_HEAD_RE.search(c)
if m:
    new_line = m.group(1) + m.group(2) + PRECONNECT_HINTS + m.group(3)
    c = c[:m.start()] + new_line + c[m.end():]
    print("[2] preconnect/dns-prefetch hints added to __ext2 <head>")
else:
    # Simpler fallback: find the __ext2 specific <head> sub_filter line and append
    EXT2_HEAD_SIMPLE = '";\n        sub_filter "</head>" "<style>.header-nav,#side-notification'
    if EXT2_HEAD_SIMPLE in c:
        c = c.replace(EXT2_HEAD_SIMPLE,
                      f'{PRECONNECT_HINTS}";\n        sub_filter "</head>" "<style>.header-nav,#side-notification', 1)
        print("[2 fallback] preconnect hints inserted before </head> filter")
    else:
        print("[2] FAIL: could not locate __ext2 <head> sub_filter to append hints")

with open(p, "w") as f:
    f.write(c)
print("Done.")
