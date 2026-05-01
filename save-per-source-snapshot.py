#!/usr/bin/env python3
"""Save a fresh, dated, per-source snapshot of the current working state.

   Creates:
     /root/backups/yala-2026-05-01-final/
        yshoot/
          yala.zaboni.store.yshoot.conf
          CHANGELOG-yshoot.md
        korasimo/
          yala.zaboni.store.korasimo.conf
          CHANGELOG-korasimo.md
        wrap_v10.js
        README.md

   Adds a comment header to the LIVE configs in /etc/nginx/sites-available/
   that lists the fixes applied today (so future-you can read the file and
   know what was customized).
"""
import os, shutil, time, subprocess
from datetime import datetime

DATE = datetime.now().strftime("%Y-%m-%d")
ROOT = f"/root/backups/yala-{DATE}-final"
os.makedirs(f"{ROOT}/yshoot",   exist_ok=True)
os.makedirs(f"{ROOT}/korasimo", exist_ok=True)

AVAIL = "/etc/nginx/sites-available"
WWW = "/var/www/yala.zaboni.store"

# 1) Copy current configs
shutil.copy(f"{AVAIL}/yala.zaboni.store.yshoot",   f"{ROOT}/yshoot/yala.zaboni.store.yshoot.conf")
shutil.copy(f"{AVAIL}/yala.zaboni.store.korasimo", f"{ROOT}/korasimo/yala.zaboni.store.korasimo.conf")
shutil.copy(f"{WWW}/__yala_wrap_v10.js",           f"{ROOT}/__yala_wrap_v10.js")

# 2) Per-source changelog
YSHOOT_CHANGELOG = """# yshoot (Yalla Shoot — www.yshootlive.com)

## Source-specific customizations applied 2026-05-01

### Brand / UI
- Logo `h1.bg-sl-logo` replaced with red gradient pill containing "Alaboodi TV"
- Footer copyright replaced with "جميع الحقوق محفوظة - مصطفى العبودي"
- Day-tabs (الأمس/اليوم/الغد) coloured: teal/red/yellow
- Default theme switched to LIGHT (removed `<html class=dark>` injection)

### Hide / clean
- Tawk.to chat widget hidden
- Side notification ad banner hidden
- Hero section, FAQ, info-grid, app-promo banners hidden
- Header bar above player (.bg-sl-block-head) hidden
- Description paragraphs inside .post-body hidden — keeps player visible
- Telegram subscribe popup (#_sm, #_smb) hidden
- Ad iframes (doubleclick, adsterra, propellerads, etc.) hidden

### Telegram WebApp integration
- Loads telegram-web-app.js inline in <head>
- Calls tg.ready() + tg.expand() on load
- Adds `body{padding-top:100px}` so content starts below close button
- Adds blue background (`#004ea8`) extending up to status bar

### Network / proxy
- Wildcard `proxy_redirect` keeps any external 30x redirect on yala.zaboni.store
- proxy_cookie_domain rewrites yshootlive.com cookies to yala.zaboni.store
- Origin host: www.yshootlive.com (port 443)
- Cache: 30s for HTML, 7d for static assets

### Player (`/__ext2?/HOST/PATH/`)
- Sandbox bypass: `window.self !== window.top` → `false` (with/without spaces)
- Streaming origin (live2.d-kora.online) preconnect hint
- Brightcove fastly preconnect hint
- HLS p2p service worker registration neutralized
- wrap_v10.js loaded with <script defer> (fast)
- Home button at bottom-center: bottom:50px (mobile bottom:40px), href="/shoot/"

### Important fixes
- 2026-05-01: Sub_filter target switched from `<head>` to `<meta charset="UTF-8" />`
  to avoid injecting `<script>` inside upstream's `document.documentElement.innerHTML`
  template literal (which would corrupt the HTML parser via inner `</script>`).
- 2026-05-01: Removed duplicate `<meta charset>` sub_filter in / block that was
  overwriting the blue-bg style.

## Bot integration
The Telegram bot's source-switch button (`yala-switch yshoot`) copies this file to
`/etc/nginx/sites-available/yala.zaboni.store` and reloads nginx.
"""

KORASIMO_CHANGELOG = """# korasimo (Kora Simo — www.korasimo.com)

## Source-specific customizations applied 2026-05-01

### Brand / UI
- Default theme: LIGHT
- Korasimo brand renames: "كورة سيمو" → "العبودي تي في", "Kora Simo" → "Alaboodi TV"
- Footer copyright: "جميع الحقوق محفوظة - مصطفى العبودي"

### Hide / clean
- Side notification ad banner (#side-notification) hidden
- Watermark .watermark hidden
- Header bar above player (.bg-sl-block-head) hidden
- Description paragraphs inside .post-body hidden
- Telegram popup (#_sm, #_smb) hidden
- Ad iframes hidden
- Leaked JS text from broken </script> in template literal — removed via sub_filter

### Telegram WebApp integration
- Loads telegram-web-app.js inline in <head> (after `<meta charset>`)
- Calls tg.ready() + tg.expand() on load
- Adds `body{padding-top:100px}` so content starts below close button
- (No blue bg — korasimo's design is dark navy)

### Network / proxy
- Wildcard `proxy_redirect` keeps any external 30x redirect on yala.zaboni.store
- proxy_cookie_domain rewrites korasimo.com cookies to yala.zaboni.store
- Origin host: www.korasimo.com (port 443)

### Player (`/__ext2?/HOST/PATH/` — Live3.php at 1.soccertvhd.live)
- Sandbox bypass: `window.self !== window.top` → `false` (handles both spaced and unspaced)
- popupTest bypass: `if (popupTest)` / `if(popupTest)` → `if (false)` / `if(false)`
- isInIframe bypass: `if (isInIframe` → `if (false`
- HLS speed boost:
    - maxBufferLength 30s → 8s
    - lowLatencyMode: true
    - manifestLoadingTimeOut 10s → 4s
    - fragLoadingTimeOut 20s → 6s
- Mobile player: `.main-wrapper{height:100dvh}`, video `object-fit:contain`, no padding ≤768px
- Quality selector preserved (visible)
- Home button on player REMOVED (per user request — korasimo player has its own UI)

### Stream proxying (KEY FIX)
The S3 stream URLs (s3.us-east-2.amazonaws.com/simo3/...) require Origin/Referer
matching the upstream player domain (1.soccertvhd.live). Browser fetching from
yala.zaboni.store sent wrong Origin → S3 returned 403.

Fix: rewrite stream URLs to /__ext2/HOST/PATH/ via sub_filter; in __ext2 proxy
detect amazonaws/brightcove/fastly hosts and override headers:
    Referer: https://1.soccertvhd.live/
    Origin:  https://1.soccertvhd.live

Result: stream loads at 720p, playback starts within ~1-2s on mobile.

### Important fixes
- 2026-05-01: Referer rewriting in __ext2: rewrite browser's referer from
  yala.zaboni.store host to www.korasimo.com host so Live3.php can identify
  which match the user came from.

## Bot integration
The Telegram bot's source-switch button (`yala-switch korasimo`) copies this file
to `/etc/nginx/sites-available/yala.zaboni.store` and reloads nginx.
"""

with open(f"{ROOT}/yshoot/CHANGELOG-yshoot.md", "w", encoding="utf-8") as f:
    f.write(YSHOOT_CHANGELOG)
with open(f"{ROOT}/korasimo/CHANGELOG-korasimo.md", "w", encoding="utf-8") as f:
    f.write(KORASIMO_CHANGELOG)

# 3) Top-level README.md for the snapshot
README = f"""# Snapshot {DATE}-final

Working state of yala.zaboni.store nginx configs and assets after all
fixes from 2026-05-01.

## Per-source isolation

Each source has its own folder with its config and a CHANGELOG describing
the customizations specific to that source.

| Source   | Upstream            | Config file (live)                                  | Status   |
|----------|---------------------|-----------------------------------------------------|----------|
| yshoot   | www.yshootlive.com  | /etc/nginx/sites-available/yala.zaboni.store.yshoot | working  |
| korasimo | www.korasimo.com    | /etc/nginx/sites-available/yala.zaboni.store.korasimo | working |

The Telegram bot picks one source via `/usr/local/bin/yala-switch <id>`,
which copies that source's file to `yala.zaboni.store` and reloads nginx.
`/etc/nginx/sites-enabled/yala.zaboni.store` is a symlink to the active file.

## Restore

To restore yshoot from this snapshot:
    cp yshoot/yala.zaboni.store.yshoot.conf  /etc/nginx/sites-available/yala.zaboni.store.yshoot
    /usr/local/bin/yala-switch yshoot

To restore korasimo:
    cp korasimo/yala.zaboni.store.korasimo.conf  /etc/nginx/sites-available/yala.zaboni.store.korasimo
    /usr/local/bin/yala-switch korasimo

To restore the wrap_v10.js client script:
    cp __yala_wrap_v10.js  /var/www/yala.zaboni.store/__yala_wrap_v10.js
"""
with open(f"{ROOT}/README.md", "w", encoding="utf-8") as f:
    f.write(README)

# 4) Add a small comment header on top of each LIVE config so anyone opening
#    the file sees what's been customized and where to find the changelog.
def prepend_header(live_path: str, source: str, changelog_path: str):
    with open(live_path) as f:
        existing = f.read()
    # Skip if already has our header
    if "# == Customizations for " + source in existing:
        return False
    header = (
        f"# == Customizations for {source} (Alaboodi TV / yala.zaboni.store) ==\n"
        f"# Source-specific changelog: /root/backups/yala-{DATE}-final/{source}/CHANGELOG-{source}.md\n"
        f"# Live snapshot:             /root/backups/yala-{DATE}-final/{source}/\n"
        f"# Last verified working:     {DATE}\n"
        f"# Bot switch script:         /usr/local/bin/yala-switch {source}\n"
        f"# DO NOT EDIT THIS COMMENT BLOCK — it is the marker for documentation.\n"
        f"\n"
    )
    with open(live_path, "w") as f:
        f.write(header + existing)
    return True

added_yshoot   = prepend_header(f"{AVAIL}/yala.zaboni.store.yshoot",   "yshoot",   f"{ROOT}/yshoot/CHANGELOG-yshoot.md")
added_korasimo = prepend_header(f"{AVAIL}/yala.zaboni.store.korasimo", "korasimo", f"{ROOT}/korasimo/CHANGELOG-korasimo.md")

# Re-apply active source so the header appears in the live yala.zaboni.store too
active = open("/var/lib/yala-source").read().strip() or "yshoot"
shutil.copy(f"{AVAIL}/yala.zaboni.store.{active}", f"{AVAIL}/yala.zaboni.store")

# Test + reload
test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
ok = test.returncode == 0
print(f"[1] yshoot config + CHANGELOG -> {ROOT}/yshoot/")
print(f"[2] korasimo config + CHANGELOG -> {ROOT}/korasimo/")
print(f"[3] wrap_v10.js -> {ROOT}/__yala_wrap_v10.js")
print(f"[4] README.md -> {ROOT}/README.md")
print(f"[5] live config headers added: yshoot={added_yshoot}, korasimo={added_korasimo}")
print(f"[6] active source: {active} (re-copied to live)")
print(f"[7] nginx -t: {'ok' if ok else 'FAIL'}")
if ok:
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
    print("[8] nginx reloaded")
