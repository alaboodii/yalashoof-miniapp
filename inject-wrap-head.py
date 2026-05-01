#!/usr/bin/env python3
"""Add wrap.js script tag to top of <head> in /__ext2/ proxy responses
so XHR/fetch overrides are in place BEFORE Clappr/hls.js initializes."""

path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# In the /__ext2/ block, find the </head> sub_filter and ADD a <head> sub_filter before it
# that injects wrap.js synchronously at top of head
new_line = '        sub_filter "<head>" "<head><script src=\\"/__yala_wrap.js\\"></script>";\n'

# Find the existing </head> sub_filter line in /__ext2/ block and insert above it
target = '        sub_filter "</head>" "<style>iframe[src*=\\\'ads\\\']'
already = 'sub_filter "<head>" "<head><script src='
if already not in c and target in c:
    c = c.replace(target, new_line + target, 1)
    print("inserted")
else:
    print("already present or anchor not found")

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
