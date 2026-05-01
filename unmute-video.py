#!/usr/bin/env python3
path = "/etc/nginx/sites-available/yala.zaboni.store"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add to /__ext/ section: strip "muted" attribute from video tags before they reach the browser
addition = """        # Remove muted attribute so video player starts with sound on
        sub_filter ' muted ' ' ';
        sub_filter ' muted>' '>';
        sub_filter ' muted=\"\"' '';
        sub_filter ' muted=\"muted\"' '';

"""

# Insert before the </body> sub_filter line in the /__ext/ block
anchor = "        # Inject ad-blocker JS\n        sub_filter \"</body>\""
if "Remove muted attribute" not in content and anchor in content:
    content = content.replace(anchor, addition + anchor, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("ok")
