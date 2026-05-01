#!/usr/bin/env python3
"""Fix the Referer header in korasimo's __ext2 block so Live3.php receives
   the actual match-page referer (rewritten to korasimo's domain) instead of
   the player URL itself.
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.korasimo"
with open(p) as f:
    c = f.read()

OLD = '        proxy_set_header Referer "https://$ext_host$ext_path";'
# Replace with logic that uses actual browser Referer (rewriting our host
# to korasimo's host) so upstream can identify which match the user came from.
NEW = (
    '        # Forward browser Referer but rewrite our host -> upstream host so\n'
    '        # Live3.php can identify the match the user was on.\n'
    '        set $rewritten_referer $http_referer;\n'
    '        if ($rewritten_referer ~ "^(https?)://yala\\.zaboni\\.store(.*)$") {\n'
    '            set $rewritten_referer "$1://www.korasimo.com$2";\n'
    '        }\n'
    '        if ($rewritten_referer = "") {\n'
    '            set $rewritten_referer "https://www.korasimo.com/";\n'
    '        }\n'
    '        proxy_set_header Referer $rewritten_referer;'
)

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    with open(p, "w") as f:
        f.write(c)
    print("[OK] Referer rewriting added to korasimo __ext2 block")
else:
    print("[FAIL] OLD marker not found")
