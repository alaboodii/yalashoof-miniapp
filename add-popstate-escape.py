#!/usr/bin/env python3
"""Add popstate-escape logic to the existing pushState-block script.
   When user presses Back and is still on the player URL (duplicate entry trap),
   automatically go back one more time so a single press lands them on /shoot/.
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

OLD = (
    "history.pushState=function(s,t,u){if(sameUrl(u))return;return op.apply(history,arguments);};"
    "history.replaceState=function(s,t,u){if(sameUrl(u))return;return or.apply(history,arguments);};"
    "}catch(_){}"
)
NEW = (
    "history.pushState=function(s,t,u){if(sameUrl(u))return;return op.apply(history,arguments);};"
    "history.replaceState=function(s,t,u){if(sameUrl(u))return;return or.apply(history,arguments);};"
    "var didEscape=false;var initialPath=location.pathname;"
    "window.addEventListener('popstate',function(e){"
    "if(!didEscape && location.pathname===initialPath && location.pathname.indexOf('/__ext2/')===0){"
    "didEscape=true;history.go(-1);"
    "}"
    "},false);"
    "}catch(_){}"
)

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    print("[OK] popstate-escape added")
else:
    print("[FAIL] OLD marker not found")

with open(p, "w") as f:
    f.write(c)
