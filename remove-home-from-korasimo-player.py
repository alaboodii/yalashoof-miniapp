#!/usr/bin/env python3
"""Remove the home button injection from korasimo's player pages (__ext2 block).
   Replace it with just the wrap_v10.js loader.
"""
import re

p = "/etc/nginx/sites-available/yala.zaboni.store.korasimo"
with open(p) as f:
    c = f.read()

OLD_PATTERN = re.compile(
    r'        sub_filter "</body>" "<a id=\\"alab-home\\"[^"]*?'
    r'<script src=\\"/__yala_wrap_v10\.js\?v=12\\" defer></script></body>";\n'
)
NEW = '        sub_filter "</body>" "<script src=\\"/__yala_wrap_v10.js?v=12\\" defer></script></body>";\n'

count = len(OLD_PATTERN.findall(c))
c = OLD_PATTERN.sub(NEW, c)

with open(p, "w") as f:
    f.write(c)

print(f"Removed {count} home-button injection(s)")
