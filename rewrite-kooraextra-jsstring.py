#!/usr/bin/env python3
"""Rewrite the JS string `PLAYER_HOST = 'kooraextra.com'` (and quoted variants)
   in the response from siiiir.koora-online.mov so the JS redirects to our
   /__ext2/kooraextra.com/ proxy instead of leaving our domain.

   Modifies yala.zaboni.store.siiiir ONLY.
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.siiiir"
with open(p) as f:
    c = f.read()

ANCHOR = '        sub_filter "P2PEngineHls.tryRegisterServiceWorker(p2pConfig)" "Promise.resolve()";'

NEW = (
    "        # Rewrite kooraextra.com so the JS redirect stays on our domain\n"
    "        sub_filter \"'kooraextra.com'\" \"'yala.zaboni.store/__ext2/kooraextra.com'\";\n"
    "        sub_filter '\"kooraextra.com\"' '\"yala.zaboni.store/__ext2/kooraextra.com\"';\n"
    "        sub_filter \"https://kooraextra.com\" \"https://yala.zaboni.store/__ext2/kooraextra.com\";\n"
    "        sub_filter \"//kooraextra.com\" \"//yala.zaboni.store/__ext2/kooraextra.com\";\n"
)

if "yala.zaboni.store/__ext2/kooraextra.com" not in c and ANCHOR in c:
    c = c.replace(ANCHOR, NEW + ANCHOR, 1)
    with open(p, "w") as f:
        f.write(c)
    print("[OK] kooraextra rewrite sub_filters added")
elif "yala.zaboni.store/__ext2/kooraextra.com" in c:
    print("[SKIP] already added")
else:
    print("[FAIL] anchor missing")
