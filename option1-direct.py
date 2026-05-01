#!/usr/bin/env python3
"""Option 1: watch links go directly to 000007.mov (not through our proxy).
Stream works native; matches grid still proxied for ad-blocking + branding."""
import re

path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# 1) Remove any broken target=_blank lines I may have left
c = re.sub(r'^\s*sub_filter " target=.*\n', "", c, flags=re.MULTILINE)
# Specifically clean malformed lines
c = re.sub(r'^.*target=\\".*_blank.*\n', "", c, flags=re.MULTILINE)

# 2) Strip target="_blank" cleanly (one rule per quote style)
addition = (
    '        # Strip target=_blank so Telegram WebApp navigates same-tab\n'
    '        sub_filter \' target="_blank"\' \'\';\n'
    '        sub_filter \' target=_blank\' \'\';\n'
    "        sub_filter \" target='_blank'\" '';\n"
    '\n'
)
anchor = '        # === URL rewrites: hesgoal'
if 'Strip target=_blank' not in c and anchor in c:
    c = c.replace(anchor, addition + anchor, 1)

# 3) Make watch links go direct to 000007.mov (not /__ext2/000007.mov)
c = c.replace('"https://yala.zaboni.store/__ext2/000007.mov"', '"https://000007.mov"')
c = c.replace('"//yala.zaboni.store/__ext2/000007.mov"', '"//000007.mov"')
c = c.replace('https://yala.zaboni.store/__ext2/000007.mov', 'https://000007.mov')

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("ok")
