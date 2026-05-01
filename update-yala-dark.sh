#!/bin/bash
set -e

python3 - <<'PY'
import re
path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Default-to-dark-mode script: only sets dark on first visit; respects user's switch via the moon icon afterwards.
dark_script = (
    "<script>try{"
    "var m=localStorage.getItem('mode');"
    "if(!m){localStorage.setItem('mode','rdmode');m='rdmode'}"
    "if(m==='rdmode')document.documentElement.classList.add('Night')"
    "}catch(e){}</script>"
)

style = (
    "<style>"
    # Day tabs colour overrides (no flash, all states covered)
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
    # Logo button: rename Yalla Shoot -> Alaboodi TV via ::before, change colour
    "#AYaLogo a{font-size:0!important;background:#b91c1c!important;color:#fff!important;"
    "padding:8px 18px!important;border-radius:8px!important;display:inline-block!important;"
    "text-decoration:none!important}"
    "#AYaLogo a::before{content:'Alaboodi TV';font-size:16px;font-weight:700;color:#fff;"
    "letter-spacing:0.3px;line-height:1.2;display:inline-block;direction:ltr}"
    # Footer (existing customisation)
    "#AYaFooter > *:not(#__yala_credit){display:none!important}"
    ".AY_Block.PS_1{display:none!important}"
    "#AYaFooter{padding:18px 12px!important;text-align:center!important;"
    "background:#1a1a1a!important;color:#fff!important}"
    "</style>"
)

new_line = f'        sub_filter "<head>" "<head>{dark_script}{style}";\n'

pattern = re.compile(r'^\s*sub_filter\s+"<head>".*\n', re.MULTILINE)
content = pattern.sub(new_line, content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("ok")
PY

nginx -t 2>&1 | tail -2
nginx -s reload && echo reloaded
