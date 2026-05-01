#!/usr/bin/env python3
"""Switch the <head> sub_filter target to <meta charset="UTF-8"> so the injection
   does NOT happen inside the template literal (which has only <meta name="viewport">).

   This fixes the issue where the upstream's `document.documentElement.innerHTML = `<...<head>...>``
   template literal got our <script> injected into it, breaking the HTML parser
   (because the inner </script> closed the outer script prematurely).
"""
for source in ["yshoot", "korasimo"]:
    p = f"/etc/nginx/sites-available/yala.zaboni.store.{source}"
    with open(p) as f:
        c = f.read()

    OLD_PREFIX = '        sub_filter "<head>" "<head>'
    NEW_PREFIX = '        sub_filter "<meta charset=\\"UTF-8\\">" "<meta charset=\\"UTF-8\\">'
    cnt = c.count(OLD_PREFIX)
    if cnt:
        c = c.replace(OLD_PREFIX, NEW_PREFIX)
        with open(p, "w") as f:
            f.write(c)
        print(f"[{source}] updated {cnt} <head> filter(s)")
    else:
        print(f"[{source}] no <head> filter found")
