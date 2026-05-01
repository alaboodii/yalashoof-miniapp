#!/usr/bin/env python3
"""Rebuild siiiir from a fresh yshoot template, applying customizations
   in SHORT separate sub_filters to avoid nginx's per-line parameter limit.

   yshoot/korasimo NOT touched.
"""
import shutil, subprocess
from pathlib import Path

AVAIL = Path("/etc/nginx/sites-available")

# Start from current yshoot (has all today's edits, blue bg, padding, etc.)
yshoot = (AVAIL / "yala.zaboni.store.yshoot").read_text(encoding="utf-8")

def to_siiiir(s: str) -> str:
    s = s.replace("yshoot_upstream", "siiiir_upstream")
    s = s.replace("www.yshootlive.com", "siiiir.tv")
    s = s.replace("yshootlive.com", "siiiir.tv")
    return s

c = to_siiiir(yshoot)

# Set home button to /today-matches/
c = c.replace(
    'alab-home\\" href=\\"/shoot/\\"',
    'alab-home\\" href=\\"/today-matches/\\"',
)

# Update header comment
import re
c = re.sub(
    r"# == Customizations for yshoot[^\n]*\n.*?# DO NOT EDIT[^\n]*\n\n",
    "# == Customizations for siiiir (Sir TV / siiiir.tv) ==\n"
    "# Cloned from yshoot template with host swap to siiiir.tv\n"
    "# DO NOT EDIT THIS COMMENT BLOCK.\n"
    "\n",
    c, count=1, flags=re.DOTALL,
)

# === Add siiiir-specific sub_filters as SHORT separate lines ===
# Insert after the existing sub_filter "<meta charset" lines, before </body> filter.
EXTRA_SIIIIR = """
        # === siiiir.tv-specific brand renames ===
        sub_filter "Sir TV" "Alaboodi TV";
        sub_filter "Siiir TV" "Alaboodi TV";
        sub_filter "Siiir.tv" "Alaboodi TV";
        sub_filter "siiir.tv" "alaboodi-tv";
        sub_filter "siiiir.tv" "alaboodi-tv";
        sub_filter "Sir.tv" "Alaboodi";
        sub_filter "سير تيفي" "العبودي تي في";
        sub_filter "سير تي في" "العبودي تي في";
        sub_filter "كورة لايف" "العبودي تي في";
        sub_filter "Koora Live" "Alaboodi TV";
        sub_filter "koora live" "alaboodi tv";
        sub_filter "Kooora" "Alaboodi";

        # === Route kooraextra streaming domain through our proxy ===
        sub_filter "https://kooraextra.com" "https://yala.zaboni.store/__ext2/kooraextra.com";
        sub_filter "//kooraextra.com" "//yala.zaboni.store/__ext2/kooraextra.com";
        sub_filter "https://www.kooraextra.com" "https://yala.zaboni.store/__ext2/www.kooraextra.com";
        sub_filter "//www.kooraextra.com" "//yala.zaboni.store/__ext2/www.kooraextra.com";

        # === Hide ad/promo containers (separate <style> injection) ===
        sub_filter "</head>" "<style>.albayalla-e3lan,.e3lan-thumb_start,[class*='e3lan']{display:none!important}#pwaBanner,.pwa-banner{display:none!important}[class*='betting'],[class*='prediction'],[class*='telegram-cta'],[class*='join-channel'],[class*='app-promo'],[class*='install-app']{display:none!important}[class*='sir-tv'],[class*='sirtv'],[class*='AY_TV'],.AY_TV,.AY_TVPos,.match-channel{display:none!important}.MainMenu .sub-menu,.AYaSocial,.bestbet,.subscribe-section,[class*='vip-channel']{display:none!important}#side-notification{display:none!important}html.Night,body.Night{background:#eceef2!important;color:#000!important}html.Night,body.Night{--body_bg:#eceef2!important;--LightColor:#fff!important;--Gray1:#eceef2!important;--Gray2:#ddd!important}.AYaLogo,.AYaLogo *{background:transparent!important}.AYaLogo a{font-size:0!important;background:linear-gradient(135deg,#b91c1c,#7f1d1d)!important;color:#fff!important;padding:8px 18px!important;border-radius:8px!important;display:inline-block!important;text-decoration:none!important;box-shadow:0 2px 8px rgba(185,28,28,0.4)!important}.AYaLogo a *{display:none!important}.AYaLogo a::before{content:'Alaboodi TV';font-family:'Poppins','Segoe UI',sans-serif;font-size:18px;font-weight:700;color:#fff;letter-spacing:0.4px;display:inline-block;direction:ltr}</style></head>";
"""

# Find the spot to inject — after the last sub_filter in / location BEFORE </body> filter
# Use a stable anchor: the first '</body>' sub_filter we know is in / block
ANCHOR = '        sub_filter "</body>" "<a id=\\"alab-home'
idx = c.find(ANCHOR)
if idx > 0:
    c = c[:idx] + EXTRA_SIIIIR + c[idx:]
    print("[1] siiiir-specific sub_filters inserted before </body>")
else:
    print("[1] FAIL: anchor not found")

# === Inject light-mode enforcer + kooraextra location override script in <head> ===
# Find the existing telegram init script and prepend our overrides
LIGHT_FIX_ANCHOR = "</script><link rel=preconnect href=https://fonts.googleapis.com>"
LIGHT_FIX = (
    "</script>"
    "<script>(function(){try{"
    "document.documentElement.classList.remove('Night');"
    "document.documentElement.classList.remove('dark');"
    "try{localStorage.setItem('theme','light');}catch(_){}"
    "try{var obs=new MutationObserver(function(){"
    "if(document.documentElement.classList.contains('Night')){"
    "document.documentElement.classList.remove('Night');"
    "}});"
    "obs.observe(document.documentElement,{attributes:true,attributeFilter:['class']});"
    "}catch(_){}"
    "try{var oA=window.location.assign.bind(window.location);"
    "var oR=window.location.replace.bind(window.location);"
    "function fx(u){try{var x=new URL(u,location.href);"
    "if(x.host==='kooraextra.com'||x.host.endsWith('.kooraextra.com')){"
    "return location.origin+'/__ext2/'+x.host+x.pathname+x.search+x.hash;}}catch(_){}return u;}"
    "window.location.assign=function(u){return oA(fx(u));};"
    "window.location.replace=function(u){return oR(fx(u));};"
    "}catch(_){}"
    "}catch(_){}})();</script>"
    "<link rel=preconnect href=https://fonts.googleapis.com>"
)
if LIGHT_FIX_ANCHOR in c and "kooraextra" not in c.split(LIGHT_FIX_ANCHOR, 1)[0][-500:]:
    c = c.replace(LIGHT_FIX_ANCHOR, LIGHT_FIX, 1)
    print("[2] light-mode + kooraextra location override script added")
elif "fx(u)" in c:
    print("[2] location override already present")
else:
    print("[2] anchor not found")

# Write
(AVAIL / "yala.zaboni.store.siiiir").write_text(c, encoding="utf-8")
size = (AVAIL / "yala.zaboni.store.siiiir").stat().st_size
print(f"[3] siiiir written: {size} bytes")

# Test + reload
test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
ok = test.returncode == 0
print(f"[4] nginx -t: {'ok' if ok else 'FAIL'}")
if not ok:
    print(test.stderr[-500:])
    raise SystemExit(1)
subprocess.run(["/usr/local/bin/yala-switch", "siiiir"], check=True)
subprocess.run(["systemctl", "reload", "nginx"], check=True)
print("[5] switched to siiiir + nginx reloaded")
