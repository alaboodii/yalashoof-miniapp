#!/usr/bin/env python3
"""Revert ALL back-button-related changes that broke the player.
   Keep only the safe popup/ad/header/article hide CSS + proxy_redirect.
"""
import re, shutil, time

NGINX = "/etc/nginx/sites-enabled/yala.zaboni.store"
WRAP_JS = "/var/www/yala.zaboni.store/__yala_wrap_v10.js"

shutil.copy(NGINX, "/root/yala.zaboni.store.pre-revert." + str(int(time.time())))

with open(NGINX) as f:
    c = f.read()

# 1) Remove home button HTML+CSS+iframe-detect script from </body> sub_filter
HOME_HTML = (
    '<a id=\\"alab-home\\" href=\\"/shoot/\\">'
    '<span class=\\"alab-home-logo\\">Alaboodi TV</span>'
    '<span class=\\"alab-home-label\\">الصفحة الرئيسية</span>'
    '</a>'
    "<script>(function(){if(window.self!==window.top){var b=document.getElementById('alab-home');if(b)b.remove();}})();</script>"
    '<style>'
    'body{padding-top:64px!important}'
    '#alab-home{position:fixed;top:10px;left:50%;transform:translateX(-50%);'
    'z-index:2147483647;display:inline-flex;align-items:center;gap:10px;'
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

if HOME_HTML in c:
    c = c.replace(HOME_HTML, "", 1)
    print("[1] Home button HTML+CSS+script removed")
else:
    # Fallback: regex remove anything between alab-home <a> and the wrap loader <img>
    PATTERN = re.compile(r'<a id=\\"alab-home\\".*?</style>', re.DOTALL)
    c, n = PATTERN.subn("", c)
    print(f"[1] Regex fallback removed {n} block(s)")

# Make sure no leftover popstate/pushState scripts
PUSHSTATE_RE = re.compile(r"<script>\(function\(\)\{try\{var op=history\.pushState[^<]*?\}\)\(\);</script>", re.DOTALL)
c, n2 = PUSHSTATE_RE.subn("", c)
print(f"[2] Removed {n2} pushState/popstate script block(s)")

with open(NGINX, "w") as f:
    f.write(c)
print("nginx config saved")

# 3) Revert wrap_v10.js rewriteExternalToProxy to its original form
with open(WRAP_JS) as f:
    js = f.read()

OLD_FN = (
    'function rewriteExternalToProxy(url){\n'
    '  try {\n'
    '    var u = new URL(url, location.href);\n'
    '    if (!u.host || u.host === location.host) return null;\n'
    '    if (u.protocol !== "https:" && u.protocol !== "http:") return null;\n'
    '    if (u.pathname.indexOf("/__ext/") === 0) return null;\n'
    '    if (u.pathname.indexOf("/__ext2/") === 0) return null;\n'
    '    if (isBadUrl(u.href)) return null;       // ad domain — let it be blocked, don\'t proxy\n'
    '    if (isDirectHost(u.host)) return null;   // pass through (YouTube etc need original origin)\n'
    '    // Ensure trailing slash on directory-like paths so upstream does not 302-redirect\n'
    '    // (e.g. /one-sport-max -> /one-sport-max/), which would add an extra history entry.\n'
    '    var path = u.pathname || "/";\n'
    '    if (path.length > 1 && !path.endsWith("/") && !/\\.[a-zA-Z0-9]{2,5}$/.test(path)) {\n'
    '      path += "/";\n'
    '    }\n'
    '    return "/__ext2/" + u.host + path + u.search + u.hash;\n'
    '  } catch(_) { return null; }\n'
    '}'
)
ORIGINAL_FN = (
    'function rewriteExternalToProxy(url){\n'
    '  try {\n'
    '    var u = new URL(url, location.href);\n'
    '    if (!u.host || u.host === location.host) return null;\n'
    '    if (u.protocol !== "https:" && u.protocol !== "http:") return null;\n'
    '    if (u.pathname.indexOf("/__ext/") === 0) return null;\n'
    '    if (isBadUrl(u.href)) return null;       // ad domain — let it be blocked, don\'t proxy\n'
    '    if (isDirectHost(u.host)) return null;   // pass through (YouTube etc need original origin)\n'
    '    return "/__ext/" + u.host + u.pathname + u.search + u.hash;\n'
    '  } catch(_) { return null; }\n'
    '}'
)

if OLD_FN in js:
    js = js.replace(OLD_FN, ORIGINAL_FN, 1)
    print("[3] wrap_v10.js rewriteExternalToProxy reverted to original (/__ext/, no trailing slash)")
else:
    print("[3] wrap_v10.js: function not in expected modified state — leaving as-is")

with open(WRAP_JS, "w") as f:
    f.write(js)
print("wrap_v10.js saved")
