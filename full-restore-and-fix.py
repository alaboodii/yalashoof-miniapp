#!/usr/bin/env python3
"""Restore nginx config from oldest backup (pre back-button experiments) and
   re-apply only the SAFE customizations:
   - Hide Telegram subscribe popup (#_sm, #_smb) + ad iframes
   - Hide page header bar above player
   - Hide description paragraphs inside .post-body (keep player visible)
   - Switch default theme to LIGHT (remove `class=dark` injection)

   NOTHING related to back-button, history, or home button is added.
"""
import shutil, time

BAK = "/root/yala.zaboni.store.bak.1777643244"
NGINX = "/etc/nginx/sites-enabled/yala.zaboni.store"

# Step 0: snapshot current state then restore baseline
shutil.copy(NGINX, "/root/yala.zaboni.store.pre-restore." + str(int(time.time())))
shutil.copy(BAK, NGINX)
print("[0] restored baseline config from", BAK)

with open(NGINX) as f:
    c = f.read()

# Step 1: Switch default theme to LIGHT — remove the html class=dark injection
DARK = 'sub_filter "<html " "<html class=\\"dark\\" ";'
if DARK in c:
    c = c.replace(DARK, "", 1)
    print("[1] removed default-dark class injection (light mode now default)")
else:
    print("[1] dark class injection not found")

# Step 2: Replace the simple tawk-style filter with our richer popup/header/text hide CSS
TAWK = '<style>.header-nav,#side-notification,.tawk-min-container,.server-switcher,iframe[src*=\\"tawk\\"]{display:none!important}</style>'
NEW = (
    '<style>'
    '.header-nav,#side-notification,.tawk-min-container,.server-switcher,'
    'iframe[src*=\\"tawk\\"],'
    # Telegram subscribe popup
    '#_sm,#_smb,[id^=\\"_sm\\"],'
    # Generic popup containers
    '.popup-overlay,.popup-container,#popup,#shahidkoora-popup,#app-popup-overlay,'
    '[class*=\\"download-btn-popup\\"],'
    # Ad-network iframes
    'iframe[src*=\\"ads\\"],iframe[src*=\\"doubleclick\\"],iframe[src*=\\"googlesyndication\\"],'
    'iframe[src*=\\"eruptpriority\\"],iframe[src*=\\"propeller\\"],iframe[src*=\\"adsterra\\"],'
    'iframe[src*=\\"popcash\\"],iframe[src*=\\"adcash\\"],iframe[src*=\\"onclickads\\"],'
    'iframe[src*=\\"exoclick\\"],iframe[src*=\\"juicy\\"]'
    '{display:none!important;visibility:hidden!important}'
    'body.no-scroll,html.no-scroll{overflow:auto!important}'
    # Hide page header bar above player ("On Sport Max" title)
    '.bg-sl-block-head{display:none!important}'
    # Hide text/description siblings inside post-body — keep player wrapper visible
    '.post-body > p,.post-body > h1,.post-body > h2,.post-body > h3,.post-body > h4,'
    '.post-body > h5,.post-body > h6,.post-body > ul,.post-body > ol,'
    '.post-body > blockquote,.post-body > figure,.post-body > pre,'
    '.post-body > table,.post-body > hr{display:none!important}'
    '</style>'
)
n = c.count(TAWK)
if n:
    c = c.replace(TAWK, NEW)
    print(f"[2] applied popup/header/post-body hide CSS to {n} occurrence(s)")
else:
    print("[2] tawk marker not found — CSS hides not applied")

with open(NGINX, "w") as f:
    f.write(c)

print("Done. Test nginx and reload.")
