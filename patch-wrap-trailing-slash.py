#!/usr/bin/env python3
"""Patch __yala_wrap_v10.js so external-link rewriting:
   1) Uses /__ext2/ (matches the named cookie/proxy convention)
   2) Adds a trailing slash on directory-like paths so upstream does not
      issue a 302 to add a slash (each 302 adds an extra history entry,
      which forces the user to press Back twice).
"""
p = "/var/www/yala.zaboni.store/__yala_wrap_v10.js"
with open(p) as f:
    c = f.read()

OLD = (
    'function rewriteExternalToProxy(url){\n'
    '  try {\n'
    '    var u = new URL(url, location.href);\n'
    '    if (!u.host || u.host === location.host) return null;\n'
    '    if (u.protocol !== "https:" && u.protocol !== "http:") return null;\n'
    '    if (u.pathname.indexOf("/__ext/") === 0) return null;\n'
    '    if (isBadUrl(u.href)) return null;       // ad domain — let it be blocked, don\'t proxy\n'
    '    if (isDirectHost(u.host)) return null;   // pass through (YouTube etc need original origin)\n'
    '    return "/__ext/" + u.host + u.pathname + u.search + u.hash;\n'
    '  } catch(_) { return null; }\n'
    '}'
)

NEW = (
    'function rewriteExternalToProxy(url){\n'
    '  try {\n'
    '    var u = new URL(url, location.href);\n'
    '    if (!u.host || u.host === location.host) return null;\n'
    '    if (u.protocol !== "https:" && u.protocol !== "http:") return null;\n'
    '    if (u.pathname.indexOf("/__ext/") === 0) return null;\n'
    '    if (u.pathname.indexOf("/__ext2/") === 0) return null;\n'
    '    if (isBadUrl(u.href)) return null;       // ad domain — let it be blocked, don\'t proxy\n'
    '    if (isDirectHost(u.host)) return null;   // pass through (YouTube etc need original origin)\n'
    '    // Ensure trailing slash on directory-like paths so upstream does not 302-redirect\n'
    '    // (e.g. /one-sport-max -> /one-sport-max/), which would add an extra history entry.\n'
    '    var path = u.pathname || "/";\n'
    '    if (path.length > 1 && !path.endsWith("/") && !/\\.[a-zA-Z0-9]{2,5}$/.test(path)) {\n'
    '      path += "/";\n'
    '    }\n'
    '    return "/__ext2/" + u.host + path + u.search + u.hash;\n'
    '  } catch(_) { return null; }\n'
    '}'
)

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    print("[OK] rewriteExternalToProxy patched")
else:
    print("[FAIL] marker not found")

with open(p, "w") as f:
    f.write(c)
