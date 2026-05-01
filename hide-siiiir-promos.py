#!/usr/bin/env python3
"""Add aggressive hide rules for promotional banners + ads on siiiir.tv source.
   Scoped to /etc/nginx/sites-available/yala.zaboni.store.siiiir ONLY —
   yshoot and korasimo configs are NOT touched.
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.siiiir"
with open(p) as f:
    c = f.read()

# Find the </head> sub_filter where the popup/ad CSS lives, and append siiiir-specific hides
OLD = (
    ".post-body > pre,.post-body > table,.post-body > hr"
    "{display:none!important}"
    "</style></head>"
)
NEW = (
    ".post-body > pre,.post-body > table,.post-body > hr,"
    # === siiiir.tv specific: hide ad slots (e3lan = "ad" in Arabic) ===
    ".albayalla-e3lan,.e3lan-thumb_start,[class*=\\\"e3lan\\\"],"
    "#pwaBanner,.pwa-banner,"
    # === Hide promotional banners (betting predictions, telegram CTAs, app installs) ===
    "[class*=\\\"betting\\\"],[class*=\\\"prediction\\\"],"
    "[class*=\\\"telegram-cta\\\"],[class*=\\\"join-channel\\\"],"
    "[class*=\\\"app-promo\\\"],[class*=\\\"app-install\\\"],"
    "[class*=\\\"download-app\\\"],[class*=\\\"install-app\\\"],"
    # === Hide \"SIR TV\" branding ribbons on match cards ===
    "[class*=\\\"sir-tv\\\"],[class*=\\\"sirtv\\\"],"
    "[class*=\\\"siiiir\\\"],[class*=\\\"sponsor\\\"],"
    # === Hide HD banner above player (the purple SIR TV HD bar) ===
    ".video-serv > span:first-child,"
    # === Hide native overlay banners + sticky bottom CTAs ===
    "[class*=\\\"sticky-bottom\\\"],[class*=\\\"floating-cta\\\"],"
    "[class*=\\\"stick-to-top\\\"],"
    # === Native ad slot iframes ===
    "iframe[src*=\\\"ads\\\"],iframe[src*=\\\"adv\\\"],iframe[src*=\\\"adsbygoogle\\\"],"
    "ins.adsbygoogle"
    "{display:none!important;visibility:hidden!important;height:0!important;width:0!important}"
    "</style></head>"
)

n = c.count(OLD)
if n:
    c = c.replace(OLD, NEW)
    print(f"[OK] siiiir-specific hide rules added ({n} occurrence)")
else:
    print("[FAIL] anchor not found")

with open(p, "w") as f:
    f.write(c)
