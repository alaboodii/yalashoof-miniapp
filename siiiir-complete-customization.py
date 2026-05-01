#!/usr/bin/env python3
"""Apply ALL pending customizations to siiiir source ONLY:
   1. Hide ad/promo banners (.albayalla-e3lan, telegram CTAs, etc.)
   2. Force light mode default (remove .Night class on load)
   3. Replace logo (Siiir.tv → Alaboodi TV)
   4. Brand renames (extra patterns)

   yshoot and korasimo configs untouched.
"""
import re

p = "/etc/nginx/sites-available/yala.zaboni.store.siiiir"
with open(p) as f:
    c = f.read()

# ─── 1) Update </head> hide CSS to include siiiir-specific selectors ───
OLD_TAIL = (
    ".post-body > pre,.post-body > table,.post-body > hr"
    "{display:none!important}"
    "</style></head>"
)
NEW_TAIL = (
    ".post-body > pre,.post-body > table,.post-body > hr,"
    # Ad slots (e3lan = "ad" in Arabic)
    ".albayalla-e3lan,.e3lan-thumb_start,[class*=\\\"e3lan\\\"],"
    # PWA install banner
    "#pwaBanner,.pwa-banner,"
    # Promo banners (betting, telegram CTAs)
    "[class*=\\\"betting\\\"],[class*=\\\"prediction\\\"],"
    "[class*=\\\"telegram-cta\\\"],[class*=\\\"join-channel\\\"],"
    "[class*=\\\"app-promo\\\"],[class*=\\\"app-install\\\"],"
    "[class*=\\\"download-app\\\"],[class*=\\\"install-app\\\"],"
    # SIR TV ribbons / branding
    "[class*=\\\"sir-tv\\\"],[class*=\\\"sirtv\\\"],"
    "[class*=\\\"siiiir\\\"],[class*=\\\"sponsor\\\"],"
    # HD banner above player
    ".video-serv > span:first-child,"
    # Sticky/floating bottom CTAs
    "[class*=\\\"sticky-bottom\\\"],[class*=\\\"floating-cta\\\"],"
    "[class*=\\\"stick-to-top\\\"],"
    # Ad iframes
    "iframe[src*=\\\"ads\\\"],iframe[src*=\\\"adv\\\"],iframe[src*=\\\"adsbygoogle\\\"],"
    "ins.adsbygoogle,"
    # Hide \"العودة للموقع\" header strip
    ".returnSite,.return-to-site,"
    # Hide \"البث الرسمي لموقع Siiir.tv\" header strip + side notification
    "#side-notification"
    "{display:none!important;visibility:hidden!important;height:0!important}"
    # FORCE LIGHT MODE: kill any .Night styling
    "html.Night,body.Night,.Night,.Night body{background:var(--body_bg)!important;color:#000!important}"
    ".Night,.Night body{--body_bg:#eceef2!important;--LightColor:#fff!important;--Gray1:#eceef2!important;--Gray2:#ddd!important;--Gray3:#d8dbe1!important}"
    "</style></head>"
)

if OLD_TAIL in c:
    c = c.replace(OLD_TAIL, NEW_TAIL)
    print("[1] siiiir hide rules + force-light overrides applied")
else:
    print("[1] FAIL: </head> CSS marker not found")

# ─── 2) Force light mode at runtime: inject script that removes 'Night' class ───
# Insert into the existing telegram-init script (at the start of the / block <head> filter)
# Look for the telegram script and add a small light-mode-enforcer
OLD_TG_INIT = "</script><link rel=preconnect href=https://fonts.googleapis.com>"
NEW_TG_INIT = (
    "</script>"
    "<script>(function(){"
    "try{document.documentElement.classList.remove('Night');"
    "document.documentElement.classList.remove('dark');"
    "localStorage.setItem('theme','light');"
    "localStorage.setItem('mode','wmode');"
    "var obs=new MutationObserver(function(){"
    "if(document.documentElement.classList.contains('Night')){"
    "document.documentElement.classList.remove('Night');"
    "}});"
    "obs.observe(document.documentElement,{attributes:true,attributeFilter:['class']});"
    "}catch(_){}})();"
    "</script>"
    "<link rel=preconnect href=https://fonts.googleapis.com>"
)
if OLD_TG_INIT in c and "remove('Night')" not in c:
    c = c.replace(OLD_TG_INIT, NEW_TG_INIT, 1)
    print("[2] light-mode enforcer script added")
elif "remove('Night')" in c:
    print("[2] light-mode enforcer already present")
else:
    print("[2] FAIL: telegram init marker not found")

# ─── 3) Logo replacement: hide the AYaLogo and replace with Alaboodi TV pill ───
# Find the existing <style> in </head> filter and add logo override
OLD_LOGO_HOOK = "/* Logo: replace nav-logo SVG with Alaboodi TV text */"
LOGO_OVERRIDE = (
    "/* siiiir logo override: replace SiiirTV logo with Alaboodi TV pill */"
    ".AYaLogo,.AYaLogo *{background:transparent!important}"
    ".AYaLogo a{font-size:0!important;background:linear-gradient(135deg,#b91c1c 0%,#7f1d1d 100%)!important;"
    "color:#fff!important;padding:8px 18px!important;border-radius:8px!important;"
    "display:inline-block!important;text-decoration:none!important;"
    "box-shadow:0 2px 8px rgba(185,28,28,0.4)!important}"
    ".AYaLogo a *{display:none!important}"
    ".AYaLogo a::before{content:'Alaboodi TV';font-family:'Poppins','Segoe UI','Helvetica Neue',sans-serif;"
    "font-size:18px;font-weight:700;color:#fff;letter-spacing:0.4px;line-height:1.2;"
    "display:inline-block;direction:ltr}"
    "/* Original block continues: */"
)
if OLD_LOGO_HOOK in c and ".AYaLogo a::before" not in c:
    c = c.replace(OLD_LOGO_HOOK, LOGO_OVERRIDE + OLD_LOGO_HOOK, 1)
    print("[3] logo override applied")
elif ".AYaLogo a::before" in c:
    print("[3] logo override already present")
else:
    print("[3] FAIL: logo hook marker not found")

# ─── 4) Extra brand renames ───
OLD_BRAND = "        sub_filter \"Sir TV\" \"Alaboodi TV\";"
NEW_BRAND = (
    "        sub_filter \"Sir TV\" \"Alaboodi TV\";\n"
    "        sub_filter \"كورة لايف\" \"العبودي تي في\";\n"
    "        sub_filter \"koora live\" \"alaboodi tv\";\n"
    "        sub_filter \"Koora Live\" \"Alaboodi TV\";\n"
    "        sub_filter \"KOORA LIVE\" \"ALABOODI TV\";"
)
if OLD_BRAND in c and "كورة لايف" not in c.split(OLD_BRAND, 1)[1][:200]:
    c = c.replace(OLD_BRAND, NEW_BRAND, 1)
    print("[4] extra brand renames added")

with open(p, "w") as f:
    f.write(c)
print("Done.")
