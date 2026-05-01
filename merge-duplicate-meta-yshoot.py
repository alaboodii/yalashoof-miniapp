#!/usr/bin/env python3
"""Merge the two duplicate `<meta charset>` sub_filters in yshoot's / block.
   Currently:
   - Line 259 has the telegram script with html,body blue background + nav-brand styles
   - Line 261 has a DIFFERENT telegram script with only padding (no blue bg) +
     preconnect hints
   The second one overwrites the first, so the blue background never applies.
   FIX: merge into a single filter that has BOTH blue bg AND preconnect hints.

   Scoped to yshoot only — korasimo file untouched.
"""
import re

p = "/etc/nginx/sites-available/yala.zaboni.store.yshoot"
with open(p) as f:
    c = f.read()

# Find both filter lines.
LINE_A = re.compile(
    r'        sub_filter "<meta charset=\\"UTF-8\\">" "<meta charset=\\"UTF-8\\">'
    r'<script>\(function\(\)\{[^"]*?html,body\{background-color:#004ea8[^"]*?</script>'
    r'<link rel=preconnect[^"]*?</style>";'
)
LINE_B = re.compile(
    r'\n        sub_filter "<meta charset=\\"UTF-8\\">" "<meta charset=\\"UTF-8\\">'
    r'<script>\(function\(\)\{[^"]*?body\{padding-top:100px![^"]*?</script>'
    r'<link rel=\\"dns-prefetch\\"[^"]*?";'
)

m_a = LINE_A.search(c)
m_b = LINE_B.search(c)

if not (m_a and m_b):
    print(f"[FAIL] line A found: {bool(m_a)}, line B found: {bool(m_b)}")
    raise SystemExit(1)

# Build merged filter: keep line A's content + append line B's preconnect hints just before </style>
line_a_text = m_a.group(0)
line_b_text = m_b.group(0)

# Extract preconnect hints from line B (everything after </script> up to ";)
hints_match = re.search(r'</script>(<link rel=\\"dns-prefetch\\"[^"]*?)";', line_b_text)
hints = hints_match.group(1) if hints_match else ''

# Insert hints BEFORE the closing "; of line A (i.e., after the last </style>)
# line_a_text ends with `</style>";`
merged = line_a_text.rstrip(';').rstrip('"') + hints + '";'

# Replace line A with merged, remove line B (with leading newline)
c = c.replace(line_a_text, merged, 1)
c = c.replace(line_b_text, '', 1)

with open(p, "w") as f:
    f.write(c)

print("[OK] merged duplicate filters in yshoot / block")
print(f"     line A (blue bg): preserved")
print(f"     line B (preconnect hints): merged in")
