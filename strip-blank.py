#!/usr/bin/env python3
path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

addition = """        # Strip target=_blank so Telegram WebApp does not prompt to leave the app
        sub_filter ' target=\"_blank\"' '';
        sub_filter ' target=_blank' '';
        sub_filter \" target='_blank'\" '';

"""

anchor = "        # === Brand rename: Korasimo / كورة سيمو → Alaboodi TV"
if "Strip target=_blank" not in content and anchor in content:
    content = content.replace(anchor, addition + anchor, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("ok")
