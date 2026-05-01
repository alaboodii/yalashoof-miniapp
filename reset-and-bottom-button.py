#!/usr/bin/env python3
"""Full reset to known-good state, then add home button at BOTTOM CENTER only.
   - Restores wrap_v10.js from backup (.bak.1777648189 — pre-softening, original).
   - Removes all home-button HTML, body padding, Telegram early-ready inject.
   - Adds a NEW home button fixed at the bottom center of player pages.
"""
import re, shutil, time

# ---------- 1) Restore wrap_v10.js to the pre-softened original ----------
WRAP = "/var/www/yala.zaboni.store/__yala_wrap_v10.js"
BAK_WRAP = "/root/__yala_wrap_v10.js.bak.1777648189"
shutil.copy(BAK_WRAP, WRAP)
print("[1] wrap_v10.js restored from", BAK_WRAP)

# ---------- 2) Clean up nginx config ----------
NGINX = "/etc/nginx/sites-enabled/yala.zaboni.store"
shutil.copy(NGINX, "/root/yala.zaboni.store.pre-reset." + str(int(time.time())))

with open(NGINX) as f:
    c = f.read()

# 2a) Remove ALL Telegram early-ready inline scripts injected in <head>
TG_INIT_RE = re.compile(
    r"<script>\(function\(\)\{try\{var s=document\.createElement\('script'\);"
    r"s\.src='https://telegram\.org/js/telegram-web-app\.js';[^<]*?\}\)\(\);</script>"
)
c, n_tg = TG_INIT_RE.subn("", c)
print(f"[2a] removed {n_tg} Telegram early-ready scripts")

# 2b) Remove the standalone <head> sub_filter that we added in __ext2 block (it had only the TG init)
EXT2_HEAD_LINE_RE = re.compile(r'\s*sub_filter "<head>" "<head>";\n', re.MULTILINE)
c, n_h = EXT2_HEAD_LINE_RE.subn("\n", c)
print(f"[2b] removed {n_h} empty <head> sub_filter line(s)")

# 2c) Remove ALL home button HTML / wrap / scripts from the </body> sub_filter in __ext2
HOME_RE = re.compile(
    r'<a id=\\\"alab-home\\\".*?</a>'  # the anchor
    r'(?:<script>\(function\(\)\{[^<]*?\}\)\(\);</script>)?'  # iframe-detect script if present
    r'<style>[^<]*?#alab-home[^<]*?</style>',
    re.DOTALL,
)
c, n_h1 = HOME_RE.subn("", c)
# Also a wrapped variant with #alab-home-wrap
HOME_WRAP_RE = re.compile(
    r'<div id=\\\"alab-home-wrap\\\".*?</div>'
    r'(?:<script>\(function\(\)\{[^<]*?\}\)\(\);</script>)?'
    r'<style>[^<]*?#alab-home[^<]*?</style>',
    re.DOTALL,
)
c, n_h2 = HOME_WRAP_RE.subn("", c)
print(f"[2c] removed {n_h1} unwrapped + {n_h2} wrapped home button block(s)")

# Last-chance regex to remove any straggling <style> with body padding-top from us
PAD_RE = re.compile(
    r'<style>body\{padding-top:[0-9]+px[^}]*\}[^<]*</style>'
)
c, n_p = PAD_RE.subn("", c)
print(f"[2d] removed {n_p} stray body padding style block(s)")

# ---------- 3) Inject new home button: FIXED BOTTOM CENTER ----------
# Find the </body> sub_filter in __ext2 block and prepend our new bottom button.
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
    # FIXED BOTTOM CENTER — sits below the player at the bottom of the viewport
    '#alab-home{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:2147483647;'
    'display:inline-flex;align-items:center;gap:8px;'
    'padding:10px 22px;border-radius:999px;text-decoration:none;'
    'background:linear-gradient(135deg,#b91c1c 0%,#7f1d1d 100%);'
    'box-shadow:0 4px 16px rgba(185,28,28,0.5),0 0 0 1px rgba(255,255,255,0.1);'
    "font-family:'IBM Plex Sans Arabic','Poppins','Segoe UI',sans-serif;"
    'transition:transform .15s ease,box-shadow .15s ease;cursor:pointer}'
    '#alab-home:active{transform:translateX(-50%) translateY(1px)}'
    '#alab-home:hover{transform:translateX(-50%) translateY(-1px);'
    'box-shadow:0 6px 20px rgba(185,28,28,0.65),0 0 0 1px rgba(255,255,255,0.15)}'
    '#alab-home .alab-home-icon{font-size:18px;line-height:1;color:#fff;font-weight:700}'
    '#alab-home .alab-home-label{font-weight:600;font-size:14px;color:#fff;direction:rtl;line-height:1}'
    '@media (max-width:600px){#alab-home{bottom:14px;padding:9px 18px;gap:7px}'
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
    print("[3] new bottom-center home button injected")
else:
    print("[3] FAIL: </body> marker for __ext2 not found")

with open(NGINX, "w") as f:
    f.write(c)

print("Done.")
