#!/usr/bin/env python3
"""Re-apply ALL fixes after backup-restore wiped the CSS hide-rules:
   1) Hide Telegram subscribe popup + ad iframes (CSS in </head> filter)
   2) Hide page header bar above player + description text inside post-body
   3) Inject pushState neutralizer in <head> of player pages (back-button hijack defense)
"""
import shutil, time

p = "/etc/nginx/sites-enabled/yala.zaboni.store"
shutil.copy(p, p + ".pre-reapply." + str(int(time.time())))
with open(p) as f:
    c = f.read()

changes = []

# ==== 1) Replace tawk style block in __ext2 with full popup/ad-hide CSS + scope-targeted hides ====
TAWK = '<style>.header-nav,#side-notification,.tawk-min-container,.server-switcher,iframe[src*=\\"tawk\\"]{display:none!important}</style>'
FULL_CSS = (
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
    # Empty / about:blank popunder iframes
    'iframe[src=\\"\\"],iframe[src=\\"about:blank\\"]:not([data-keep]),'
    'iframe[style*=\\"z-index: 2147483647\\"],iframe[style*=\\"z-index:2147483647\\"]'
    '{display:none!important;visibility:hidden!important;height:0!important;width:0!important;opacity:0!important;pointer-events:none!important}'
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
if TAWK in c:
    c = c.replace(TAWK, FULL_CSS, 1)
    changes.append("[1] popup/ad/header/article CSS applied")
else:
    changes.append("[1] FAIL: tawk style marker not found")

# ==== 2) Inject early pushState neutralizer at </head> in __ext2 (back-button hijack defense) ====
# We prepend a <script> before the FULL_CSS we just inserted.
SCRIPT = (
    '<script>(function(){'
    'try{'
    # 1) Block same-URL pushState/replaceState (back-button hijack via JS)
    'var op=history.pushState,or=history.replaceState;'
    "function sameUrl(u){try{return !u||new URL(u,location.href).href===location.href;}catch(_){return false;}}"
    'history.pushState=function(s,t,u){if(sameUrl(u))return;return op.apply(history,arguments);};'
    'history.replaceState=function(s,t,u){if(sameUrl(u))return;return or.apply(history,arguments);};'
    # 2) When user presses Back and we are still on the player page (duplicate entry),
    # auto-go-back one more time to escape the trap. Flag prevents infinite loop.
    'var didEscape=false;'
    "var initialPath=location.pathname;"
    "window.addEventListener('popstate',function(e){"
    "if(!didEscape && location.pathname===initialPath && location.pathname.indexOf('/__ext2/')===0){"
    "didEscape=true;history.go(-1);"
    "}"
    "},false);"
    '}catch(_){}'
    "window.addEventListener('beforeunload',function(e){e.stopImmediatePropagation();},true);"
    '})();</script>'
)

OLD2 = f'sub_filter "</head>" "{FULL_CSS}'
NEW2 = f'sub_filter "</head>" "{SCRIPT}{FULL_CSS}'
if OLD2 in c:
    c = c.replace(OLD2, NEW2, 1)
    changes.append("[2] pushState neutralizer injected before </head> in __ext2")
else:
    changes.append("[2] FAIL: full-css marker not found (CSS step must succeed first)")

with open(p, "w") as f:
    f.write(c)

for line in changes:
    print(line)
