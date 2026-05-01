#!/usr/bin/env python3
"""Inject an early-running script in <head> of /__ext2/ pages (player pages)
that neutralizes history.pushState / history.replaceState calls that try to
push the SAME URL — a common back-button hijack technique that forces users
to press the Back button twice.
"""
p = "/etc/nginx/sites-enabled/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# Find the __ext2 block's </head> sub_filter and prepend a <script> before <style>
OLD = 'sub_filter "</head>" "<style>.header-nav,#side-notification,.tawk-min-container'

# Inline script: blocks same-URL pushState/replaceState (back-button hijack defense).
# - Use SINGLE quotes inside JS so the surrounding nginx double-quoted string is not broken.
# - Avoid // comments (nginx string is one line; // would consume the rest).
SCRIPT = (
    '<script>(function(){'
    'try{'
    'var op=history.pushState,or=history.replaceState;'
    "function sameUrl(u){try{return !u||new URL(u,location.href).href===location.href;}catch(_){return false;}}"
    'history.pushState=function(s,t,u){if(sameUrl(u))return;return op.apply(history,arguments);};'
    'history.replaceState=function(s,t,u){if(sameUrl(u))return;return or.apply(history,arguments);};'
    '}catch(_){}'
    "window.addEventListener('beforeunload',function(e){e.stopImmediatePropagation();},true);"
    '})();</script>'
)

# Prepend the SCRIPT inside the </head> filter (before existing <style>)
NEW = f'sub_filter "</head>" "{SCRIPT}<style>.header-nav,#side-notification,.tawk-min-container'

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    print("[OK] pushState neutralizer injected before </head> style block in __ext2")
else:
    print("[FAIL] OLD marker not found")

with open(p, "w") as f:
    f.write(c)
