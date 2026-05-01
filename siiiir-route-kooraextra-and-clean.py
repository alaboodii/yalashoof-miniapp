#!/usr/bin/env python3
"""siiiir source: route kooraextra.com URLs through /__ext2/ proxy + hide
   the remaining SIR.TV ribbons and Telegram betting promo banner.

   ONLY modifies yala.zaboni.store.siiiir — yshoot/korasimo untouched.
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.siiiir"
with open(p) as f:
    c = f.read()

# 1) Route kooraextra.com URLs through our proxy (in / location's sub_filter list)
ANCHOR_1 = '        sub_filter "https://www.yshootlive.com" "https://yala.zaboni.store";'
ROUTING = (
    '        # Route kooraextra and player CDNs through our /__ext2/ proxy\n'
    '        sub_filter "https://kooraextra.com"  "https://yala.zaboni.store/__ext2/kooraextra.com";\n'
    '        sub_filter "//kooraextra.com"        "//yala.zaboni.store/__ext2/kooraextra.com";\n'
    '        sub_filter "https://www.kooraextra.com" "https://yala.zaboni.store/__ext2/www.kooraextra.com";\n'
    '        sub_filter "//www.kooraextra.com"    "//yala.zaboni.store/__ext2/www.kooraextra.com";\n'
)
if ANCHOR_1 in c and "kooraextra.com" not in c:
    c = c.replace(ANCHOR_1, ROUTING + ANCHOR_1, 1)
    print("[1] kooraextra routing added to / block")
elif "kooraextra.com" in c:
    print("[1] kooraextra routing already present")
else:
    print("[1] anchor for / block not found")

# 2) Add ribbon + nav cleanup CSS in </head>
OLD_HEAD_TAIL = (
    "html.Night,body.Night,.Night,.Night body{background:var(--body_bg)!important;color:#000!important}"
    ".Night,.Night body{--body_bg:#eceef2!important;--LightColor:#fff!important;--Gray1:#eceef2!important;--Gray2:#ddd!important;--Gray3:#d8dbe1!important}"
    "</style></head>"
)
NEW_HEAD_TAIL = (
    "html.Night,body.Night,.Night,.Night body{background:var(--body_bg)!important;color:#000!important}"
    ".Night,.Night body{--body_bg:#eceef2!important;--LightColor:#fff!important;--Gray1:#eceef2!important;--Gray2:#ddd!important;--Gray3:#d8dbe1!important}"
    # === Hide SIR.TV ribbons on match cards (corner branded labels) ===
    ".AY_Match::before,.AY_Match > [class*=\\\"AY_TV\\\"],.gr-bimg::before,"
    "[class*=\\\"AY_TV\\\"],[class*=\\\"sir-tv\\\"],"
    "[class*=\\\"AY_LV\\\"],[class*=\\\"channel-label\\\"],"
    "/* triangle ribbons that say SIR TV */"
    ".AY_TV,.AY_TVPos,.match-channel,"
    # Sub-menu items / nav (hide everything except logo + day tabs + matches)
    ".MainMenu .menu-item:not(:nth-child(1)):not(:nth-child(2)),"
    ".MainMenu .sub-menu,.AYaSocial,.AYa-SiteInfo,"
    "/* Hide footer widgets except copyright */"
    ".FW-Area .FWidget,"
    "/* Hide huge betting/telegram promo banner above player */"
    ".bestbet,.telegram-section,.subscribe-section,"
    "[class*=\\\"premium-channel\\\"],[class*=\\\"vip-channel\\\"]"
    "{display:none!important}"
    # === SIR.TV corner ribbons via :before/:after (often used) ===
    ".AY_Match,.MtCard{position:relative}"
    "</style></head>"
)
if OLD_HEAD_TAIL in c:
    c = c.replace(OLD_HEAD_TAIL, NEW_HEAD_TAIL)
    print("[2] ribbons + nav cleanup CSS added")
else:
    print("[2] tail anchor not found")

# 3) Also add sub_filter to remove the kooraextra meta-refresh / JS redirect
# Look for the <head> filter and inject a small JS at the start that overrides location.replace
ANCHOR_3 = "<script>(function(){try{document.documentElement.classList.remove('Night');"
NEW_3 = (
    "<script>(function(){try{"
    # Override window.location to rewrite kooraextra.com to /__ext2/ before navigation
    "var origAssign=window.location.assign.bind(window.location);"
    "var origReplace=window.location.replace.bind(window.location);"
    "function fix(u){try{var x=new URL(u,location.href);if(x.host==='kooraextra.com'||x.host.endsWith('.kooraextra.com')){return location.origin+'/__ext2/'+x.host+x.pathname+x.search+x.hash;}}catch(_){}return u;}"
    "try{window.location.assign=function(u){return origAssign(fix(u));};}catch(_){}"
    "try{window.location.replace=function(u){return origReplace(fix(u));};}catch(_){}"
    "}catch(_){}"
    "try{document.documentElement.classList.remove('Night');"
)
if ANCHOR_3 in c and "kooraextra.com" not in c[:c.find(ANCHOR_3)]:
    c = c.replace(ANCHOR_3, NEW_3, 1)
    print("[3] kooraextra location.assign override added")
elif "fix(u)" in c:
    print("[3] location override already present")
else:
    print("[3] light-mode anchor not found")

with open(p, "w") as f:
    f.write(c)
print("Done.")
