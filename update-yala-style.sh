#!/bin/bash
set -e

# Replace the head-inject sub_filter with a stronger CSS rule that:
#  - sets background shorthand (overrides background: var(--btn-bg))
#  - overrides --btn-bg CSS variable directly
#  - covers :hover, :focus, :active, .active
#  - disables transitions (no animation flash)
#  - kills iOS tap-highlight (the brief click flash)

# Use python to safely rewrite the sub_filter line, no quoting nightmares.
python3 - <<'PY'
import re
path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_style = (
    "<style>"
    "a.aya-btn,a.aya-btn:hover,a.aya-btn:focus,a.aya-btn:active,a.aya-btn.active{"
    "transition:none!important;-webkit-tap-highlight-color:transparent!important}"
    "a.aya-btn[title*=\\\"الأمس\\\"],"
    "a.aya-btn[title*=\\\"الأمس\\\"]:hover,"
    "a.aya-btn[title*=\\\"الأمس\\\"]:focus,"
    "a.aya-btn[title*=\\\"الأمس\\\"]:active{"
    "background:#0d9488!important;background-color:#0d9488!important;"
    "--btn-bg:#0d9488!important}"
    "a.aya-btn[title*=\\\"اليوم\\\"],"
    "a.aya-btn[title*=\\\"اليوم\\\"]:hover,"
    "a.aya-btn[title*=\\\"اليوم\\\"]:focus,"
    "a.aya-btn[title*=\\\"اليوم\\\"]:active{"
    "background:#dc2626!important;background-color:#dc2626!important;"
    "--btn-bg:#dc2626!important}"
    "a.aya-btn[title*=\\\"الغد\\\"],"
    "a.aya-btn[title*=\\\"الغد\\\"]:hover,"
    "a.aya-btn[title*=\\\"الغد\\\"]:focus,"
    "a.aya-btn[title*=\\\"الغد\\\"]:active{"
    "background:#7c3aed!important;background-color:#7c3aed!important;"
    "--btn-bg:#7c3aed!important}"
    "#AYaFooter > *:not(#__yala_credit){display:none!important}"
    ".AY_Block.PS_1{display:none!important}"
    "#AYaFooter{padding:18px 12px!important;text-align:center!important;"
    "background:#1a1a1a!important;color:#fff!important}"
    "</style>"
)

new_line = f'        sub_filter "<head>" "<head>{new_style}";\n'

# Replace any existing "<head>" sub_filter line with the new one
pattern = re.compile(r'^\s*sub_filter\s+"<head>".*\n', re.MULTILINE)
if pattern.search(content):
    content = pattern.sub(new_line, content)
else:
    # Insert before the </body> sub_filter
    content = content.replace(
        '        sub_filter "</body>"',
        new_line + '        sub_filter "</body>"',
        1,
    )

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("ok")
PY

nginx -t 2>&1 | tail -2
nginx -s reload && echo "reloaded"

echo "---verify---"
curl -s "https://yala.zaboni.store/" | head -c 1500 | grep -oE "<style>[^<]*" | head -c 600
