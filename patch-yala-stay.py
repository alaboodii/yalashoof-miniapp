#!/usr/bin/env python3
"""Patch yala.zaboni.store nginx config:
   1) Add wildcard proxy_redirect to keep external 30x redirects on our domain
   2) Hide the Telegram subscribe popup (#_sm / #_smb) and ad overlays in the player
"""
import re, sys, shutil, time

p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()
shutil.copy(p, p + ".bak." + str(int(time.time())))

# ----- 1) proxy_redirect inside __ext2 block -----
marker_ext2 = (
    "        proxy_hide_header X-Frame-Options;\n"
    "        proxy_hide_header Content-Security-Policy;\n"
    "        proxy_hide_header Content-Security-Policy-Report-Only;\n"
    "        proxy_hide_header X-Powered-By;\n"
    "\n"
    "        proxy_cookie_domain ~^.*$ yala.zaboni.store;"
)
patch_ext2 = (
    "        proxy_hide_header X-Frame-Options;\n"
    "        proxy_hide_header Content-Security-Policy;\n"
    "        proxy_hide_header Content-Security-Policy-Report-Only;\n"
    "        proxy_hide_header X-Powered-By;\n"
    "\n"
    "        # Catch any external 30x redirect and keep it on yala.zaboni.store via /__ext2/\n"
    "        proxy_redirect ~^https?://([^/]+)(/.*)?$ /__ext2/$1$2;\n"
    "\n"
    "        proxy_cookie_domain ~^.*$ yala.zaboni.store;"
)
if marker_ext2 in c:
    c = c.replace(marker_ext2, patch_ext2, 1)
    print("[1] proxy_redirect added to __ext2 block")
else:
    print("[1] WARNING: __ext2 marker not found")

# ----- 2) proxy_redirect inside / (main) block -----
marker_root = (
    "        proxy_redirect https://yshootlive.com/ https://yala.zaboni.store/;\n"
    "        proxy_redirect https://www.yshootlive.com/ https://yala.zaboni.store/;\n"
    "        proxy_redirect http://yshootlive.com/  https://yala.zaboni.store/;"
)
patch_root = (
    marker_root
    + "\n        # Catch ANY external 30x redirect and keep on yala.zaboni.store via /__ext2/"
    + "\n        proxy_redirect ~^https?://([^/]+)(/.*)?$ /__ext2/$1$2;"
)
if marker_root in c:
    c = c.replace(marker_root, patch_root, 1)
    print("[2] proxy_redirect added to / block")
else:
    print("[2] WARNING: / block marker not found")

# ----- 3) Update __ext2 </head> CSS filter to hide popups + ad overlays -----
TAWK = '<style>.header-nav,#side-notification,.tawk-min-container,.server-switcher,iframe[src*=\\"tawk\\"]{display:none!important}</style>'
NEW_CSS = (
    '<style>'
    '.header-nav,#side-notification,.tawk-min-container,.server-switcher,'
    'iframe[src*=\\"tawk\\"],'
    # Telegram subscribe popup discovered on d-kora player pages
    '#_sm,#_smb,[id^=\\"_sm\\"],'
    # Generic popup containers
    '.popup-overlay,.popup-container,#popup,#shahidkoora-popup,#app-popup-overlay,'
    '[class*=\\"download-btn-popup\\"],'
    # Fixed full-screen overlay ads
    'div[style*=\\"z-index: 99999\\"],div[style*=\\"z-index:99999\\"],'
    # Ad-network iframes
    'iframe[src*=\\"ads\\"],iframe[src*=\\"doubleclick\\"],iframe[src*=\\"googlesyndication\\"],'
    'iframe[src*=\\"eruptpriority\\"],iframe[src*=\\"propeller\\"],iframe[src*=\\"adsterra\\"],'
    'iframe[src*=\\"popcash\\"],iframe[src*=\\"adcash\\"],iframe[src*=\\"onclickads\\"],'
    'iframe[src*=\\"exoclick\\"],iframe[src*=\\"juicy\\"],'
    # Empty / about:blank iframes used as popunders
    'iframe[src=\\"\\"],iframe[src=\\"about:blank\\"]:not([data-keep]),'
    'iframe[style*=\\"z-index: 2147483647\\"],iframe[style*=\\"z-index:2147483647\\"]'
    '{display:none!important;visibility:hidden!important;height:0!important;width:0!important;opacity:0!important;pointer-events:none!important}'
    # Restore body scroll if popup locked it
    'body.no-scroll,html.no-scroll{overflow:auto!important}'
    '</style>'
)
cnt = c.count(TAWK)
if cnt:
    c = c.replace(TAWK, NEW_CSS)
    print(f"[3] __ext2 popup CSS replaced ({cnt} occurrence)")
else:
    print("[3] WARNING: tawk style block not found")

with open(p, "w") as f:
    f.write(c)
print("Patch written to:", p)
