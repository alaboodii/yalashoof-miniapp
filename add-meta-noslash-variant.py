#!/usr/bin/env python3
"""Some upstream pages (siiiir.koora-online.mov) emit <meta charset="UTF-8">
   WITHOUT a trailing space and slash. Add a sub_filter for that variant so
   our telegram + location-override scripts get injected on those pages too.

   ONLY modifies yala.zaboni.store.siiiir.
"""
import re

p = "/etc/nginx/sites-available/yala.zaboni.store.siiiir"
with open(p) as f:
    c = f.read()

# Find all `<meta charset="UTF-8" />` sub_filter lines (with slash variant).
# The ones in our config are 2: one in / block, one in __ext2 block. Pick the __ext2 one.
PATTERN = re.compile(
    r'^[ \t]+sub_filter "<meta charset=\\"UTF-8\\" />" "<meta charset=\\"UTF-8\\" />[^\n]*?";$',
    re.MULTILINE,
)
matches = list(PATTERN.finditer(c))
print(f"Found {len(matches)} <meta charset> filter lines")

if len(matches) >= 2:
    second = matches[1]
    line = second.group(0)
    # Build a no-slash variant by replacing both occurrences of `UTF-8" />` with `UTF-8">`
    no_slash = line.replace('UTF-8\\" />', 'UTF-8\\">')
    if no_slash != line and no_slash not in c:
        c = c[:second.end()] + '\n' + no_slash + c[second.end():]
        with open(p, "w") as f:
            f.write(c)
        print("[OK] no-slash variant added")
    else:
        print("[SKIP] already present or no change")
elif len(matches) >= 1:
    # Only / block has it; copy to __ext2 by inserting at appropriate place
    print("[INFO] only one match found — manual placement needed")
else:
    print("[FAIL] no <meta charset> filters found")
