#!/usr/bin/env python3
"""Rebuild yshoot + korasimo nginx configs cleanly with NO cross-contamination.

Strategy:
- yshoot: keep current /etc/nginx/sites-available/yala.zaboni.store.yshoot
  (already specific to yshootlive, has today's customizations).
- korasimo: regenerate from /etc/nginx/sites-available/yala.zaboni.store.korasimo.bak
  (the original korasimo-specific config from May 1) and apply today's universal
  customizations on top.

Universal customizations applied to BOTH:
1. proxy_redirect wildcard for staying on-domain
2. <head> sub_filter: telegram-web-app + ready/expand + 100px padding + preconnect hints
3. </head> sub_filter: hide popup #_sm/#_smb + ad iframes + .bg-sl-block-head + post-body text
4. </body> sub_filter: home button (source-specific URL) + wrap_v10.js
5. Sandbox bypass: window.self !== window.top (with AND without spaces)
6. Light mode default: remove `<html class=dark>` injection
"""
import shutil, subprocess, time
from pathlib import Path

AVAIL = Path("/etc/nginx/sites-available")
ENABLED = Path("/etc/nginx/sites-enabled/yala.zaboni.store")
STATE = Path("/var/lib/yala-source")

# --------------------------------------------------------------------------
# Source-specific overrides
# --------------------------------------------------------------------------
SOURCES = {
    "yshoot": {
        "home_url": "/shoot/",
        # Streaming origin to preconnect (live2.d-kora.online)
        "preconnect_extra": "live2.d-kora.online",
    },
    "korasimo": {
        "home_url": "/",
        # Streaming origin (1.soccertvhd.live for korasimo, fastly for player)
        "preconnect_extra": "1.soccertvhd.live",
    },
}

TODAY_PROXY_REDIRECT = '\n        # Wildcard: keep ANY external 30x redirect on-domain via /__ext2/\n        proxy_redirect ~^https?://([^/]+)(/.*)?$ /__ext2/$1$2;\n'

def head_filter(stream_origin: str) -> str:
    """<head> sub_filter: telegram WebApp init + 100px padding + preconnect hints."""
    return (
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
        f'<link rel=\\"dns-prefetch\\" href=\\"https://{stream_origin}\\">'
        f'<link rel=\\"preconnect\\" href=\\"https://{stream_origin}\\" crossorigin>'
        '";\n'
    )

def close_head_filter() -> str:
    """</head> sub_filter: hide popup, ad iframes, header bar, description text."""
    return (
        '        sub_filter "</head>" "<style>'
        '.header-nav,#side-notification,.tawk-min-container,.server-switcher,'
        'iframe[src*=\\"tawk\\"],'
        '#_sm,#_smb,[id^=\\"_sm\\"],'
        '.popup-overlay,.popup-container,#popup,#shahidkoora-popup,#app-popup-overlay,'
        '[class*=\\"download-btn-popup\\"],'
        'iframe[src*=\\"ads\\"],iframe[src*=\\"doubleclick\\"],iframe[src*=\\"googlesyndication\\"],'
        'iframe[src*=\\"eruptpriority\\"],iframe[src*=\\"propeller\\"],iframe[src*=\\"adsterra\\"],'
        'iframe[src*=\\"popcash\\"],iframe[src*=\\"adcash\\"],iframe[src*=\\"onclickads\\"],'
        'iframe[src*=\\"exoclick\\"],iframe[src*=\\"juicy\\"]'
        '{display:none!important;visibility:hidden!important}'
        'body.no-scroll,html.no-scroll{overflow:auto!important}'
        '.bg-sl-block-head{display:none!important}'
        '.post-body > p,.post-body > h1,.post-body > h2,.post-body > h3,.post-body > h4,'
        '.post-body > h5,.post-body > h6,.post-body > ul,.post-body > ol,'
        '.post-body > blockquote,.post-body > figure,.post-body > pre,'
        '.post-body > table,.post-body > hr{display:none!important}'
        '</style></head>";\n'
    )

def body_filter(home_url: str) -> str:
    """</body> sub_filter: home button + wrap_v10.js loader."""
    return (
        '        sub_filter "</body>" "'
        f'<a id=\\"alab-home\\" href=\\"{home_url}\\">'
        '<span class=\\"alab-home-icon\\">⌂</span>'
        '<span class=\\"alab-home-label\\">الصفحة الرئيسية</span>'
        '</a>'
        '<script>(function(){try{if(window.self!==window.top){var b=document.getElementById(\'alab-home\');if(b)b.remove();}}catch(_){}})();</script>'
        '<style>'
        '#alab-home{position:fixed;bottom:50px;left:50%;transform:translateX(-50%);z-index:2147483647;'
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
        '@media (max-width:600px){#alab-home{bottom:40px;padding:9px 18px;gap:7px}'
        '#alab-home .alab-home-icon{font-size:16px}'
        '#alab-home .alab-home-label{font-size:13px}}'
        '</style>'
        '<script src=\\"/__yala_wrap_v10.js?v=12\\" defer></script>'
        '</body>";\n'
    )

SANDBOX_BYPASS = """
        # Sandbox detection bypass — handle both spaced and unspaced JS variants
        sub_filter \"window.self !== window.top\" \"false\";
        sub_filter \"window.self!==window.top\" \"false\";
        sub_filter \"window.top !== window.self\" \"false\";
        sub_filter \"window.top!==window.self\" \"false\";
        sub_filter \"top !== self\" \"false\";
        sub_filter \"top!==self\" \"false\";
        sub_filter \"self !== top\" \"false\";
        sub_filter \"self!==top\" \"false\";
"""

# --------------------------------------------------------------------------
# Patch a single source config
# --------------------------------------------------------------------------
import re

def normalize_source(content: str, source: str) -> str:
    cfg = SOURCES[source]
    home_url = cfg["home_url"]
    stream = cfg["preconnect_extra"]

    # 1) Remove ANY existing dark-mode-class injection (light mode default)
    content = content.replace(
        'sub_filter "<html " "<html class=\\"dark\\" ";',
        ""
    )

    # 2) Remove ALL existing <head>, </head>, </body> sub_filters — we will rebuild them.
    # Use line-level regex
    content = re.sub(r'^[ \t]*sub_filter "<head>".*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^[ \t]*sub_filter "</head>".*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^[ \t]*sub_filter "</body>".*\n', '', content, flags=re.MULTILINE)

    # 3) Remove existing sandbox-bypass (any combo)
    content = re.sub(
        r'^[ \t]*sub_filter "(window\.(self|top) ?[!=]=? ?window\.(self|top)|self ?[!=]=? ?top|top ?[!=]=? ?self)" "(false|true)";\n',
        '', content, flags=re.MULTILINE,
    )

    # 4) Remove existing wildcard proxy_redirect (will re-add)
    content = re.sub(
        r'^[ \t]*proxy_redirect ~\^https\?://\(\[\^/\]\+\)\(/\.\*\)\?\$ /__ext2/\$1\$2;\n',
        '', content, flags=re.MULTILINE,
    )
    content = re.sub(
        r'^[ \t]*# Wildcard:[^\n]*\n',
        '', content, flags=re.MULTILINE,
    )

    # 5) Insert our customizations BEFORE the closing </body> would have been.
    # Find the location / { ... } main block and inject sub_filters at the end of its sub_filter list.
    # Easiest marker: just before "        sub_filter_once off;" — actually that's at the start.
    # Find the line that says `proxy_hide_header X-Powered-By;` (last common header) inside main /
    # location, and add proxy_redirect after it (only if not already there).

    # Add proxy_redirect to location / block
    main_loc_marker = '        proxy_hide_header X-Powered-By;'
    if main_loc_marker in content and 'proxy_redirect ~^https?' not in content:
        idx = content.find(main_loc_marker)
        end_of_line = content.find('\n', idx) + 1
        content = (
            content[:end_of_line]
            + TODAY_PROXY_REDIRECT
            + content[end_of_line:]
        )

    # 6) Append our <head>, </head>, </body>, sandbox sub_filters JUST BEFORE the
    # closing brace of the main `location / { ... }` block.
    # Identify the FIRST `    }` that's at depth 2 (closing `location /`).
    # The location starts with `    location / {` — find that, then find the matching `}`.
    loc_start = content.find('\n    location / {\n')
    if loc_start < 0:
        return content  # fallback
    # Find matching closing brace by counting
    depth = 0
    i = loc_start + 1
    while i < len(content):
        ch = content[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    close_brace_idx = i  # position of closing `}`
    # Insert before the `    }` line
    line_start = content.rfind('\n', 0, close_brace_idx) + 1

    inject = (
        '\n        # ============= Today\'s customizations (auto-managed) =============\n'
        + head_filter(stream)
        + close_head_filter()
        + body_filter(home_url)
        + SANDBOX_BYPASS
        + '        # =================================================================\n'
    )
    content = content[:line_start] + inject + content[line_start:]

    # 7) Apply same customizations to the /__ext2?/ external proxy location if present
    ext2_loc = re.search(r'\n    location ~ "(\^/__ext2\?/[^\n]+)"', content)
    if ext2_loc:
        # Find closing brace of __ext2 location block
        depth = 0
        i = ext2_loc.start() + 1
        # find the opening { for the location
        i = content.find('{', ext2_loc.start())
        depth = 1
        i += 1
        while i < len(content) and depth > 0:
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        close_brace_idx = i
        line_start = content.rfind('\n', 0, close_brace_idx) + 1

        inject_ext2 = (
            '\n        # ============= Today\'s customizations (auto-managed) =============\n'
            + head_filter(stream)
            + close_head_filter()
            + body_filter(home_url)
            + SANDBOX_BYPASS
            + '        # ==================================================================\n'
        )
        # Only add if not already present (check for our marker)
        existing_check = content[ext2_loc.start():close_brace_idx]
        if "Today's customizations (auto-managed)" not in existing_check:
            content = content[:line_start] + inject_ext2 + content[line_start:]

    return content


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
ts = int(time.time())

# Backup current state
shutil.copy(AVAIL / "yala.zaboni.store.yshoot",   f"/root/yshoot.bak.{ts}")
shutil.copy(AVAIL / "yala.zaboni.store.korasimo", f"/root/korasimo.bak.{ts}")
print(f"[0] backups -> /root/{{yshoot,korasimo}}.bak.{ts}")

# yshoot: rebuild from current (which has today's edits + yshootlive-specific filters)
yshoot_src = (AVAIL / "yala.zaboni.store.yshoot").read_text(encoding="utf-8")
yshoot_clean = normalize_source(yshoot_src, "yshoot")
(AVAIL / "yala.zaboni.store.yshoot").write_text(yshoot_clean, encoding="utf-8")
print(f"[1] rebuilt yshoot ({len(yshoot_clean)} bytes)")

# korasimo: rebuild from korasimo.bak (which has korasimo-specific filters)
korasimo_bak = AVAIL / "yala.zaboni.store.korasimo.bak"
if korasimo_bak.exists():
    korasimo_src = korasimo_bak.read_text(encoding="utf-8")
    print(f"  using korasimo.bak as base ({len(korasimo_src)} bytes)")
else:
    print("  WARN: korasimo.bak missing, falling back to current korasimo")
    korasimo_src = (AVAIL / "yala.zaboni.store.korasimo").read_text(encoding="utf-8")

korasimo_clean = normalize_source(korasimo_src, "korasimo")
(AVAIL / "yala.zaboni.store.korasimo").write_text(korasimo_clean, encoding="utf-8")
print(f"[2] rebuilt korasimo ({len(korasimo_clean)} bytes)")

# Apply currently active source
active = "yshoot"
try:
    active = STATE.read_text(encoding="utf-8").strip() or "yshoot"
except Exception:
    pass
src = AVAIL / f"yala.zaboni.store.{active}"
shutil.copy(src, AVAIL / "yala.zaboni.store")
print(f"[3] active = {active}")

# Test and reload nginx
test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
print("[4] nginx -t:", "ok" if test.returncode == 0 else "FAIL")
if test.returncode != 0:
    print(test.stderr)
    raise SystemExit("nginx config invalid; not reloading")
subprocess.run(["systemctl", "reload", "nginx"], check=True)
print("[5] nginx reloaded")
