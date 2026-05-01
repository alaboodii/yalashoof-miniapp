#!/usr/bin/env python3
path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = '        # Inject ad-blocker JS\n        sub_filter "</body>"'
addition = '''        # Bypass P2P service worker registration that fails in proxy chain
        sub_filter "P2PEngineHls.tryRegisterServiceWorker(p2pConfig)" "Promise.resolve()";

'''

if "P2PEngineHls.tryRegisterServiceWorker" in c:
    print("already present")
elif target in c:
    c = c.replace(target, addition + target, 1)
    print("inserted")
else:
    print("anchor not found")

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
