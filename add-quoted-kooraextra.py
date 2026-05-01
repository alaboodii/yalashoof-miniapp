#!/usr/bin/env python3
"""Add sub_filter that matches the quoted JS string `'kooraextra.com'`
   in the response from siiiir.koora-online.mov (its DMCA-bait redirect script).
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.siiiir"
with open(p) as f:
    c = f.read()

ANCHOR = '        sub_filter "P2PEngineHls.tryRegisterServiceWorker(p2pConfig)" "Promise.resolve()";'

NEW_LINES = (
    "        # Rewrite quoted kooraextra string (DMCA-bait JS uses string literal)\n"
    "        sub_filter \"'kooraextra.com'\" \"'yala.zaboni.store/__ext2/kooraextra.com'\";\n"
    '        sub_filter \'"kooraextra.com"\' \'"yala.zaboni.store/__ext2/kooraextra.com"\';\n'
)

if "'yala.zaboni.store/__ext2/kooraextra.com'" not in c:
    if ANCHOR in c:
        c = c.replace(ANCHOR, NEW_LINES + ANCHOR, 1)
        with open(p, "w") as f:
            f.write(c)
        print("[OK] added")
    else:
        print("[FAIL] anchor not found")
else:
    print("[SKIP] already added")
