#!/usr/bin/env python3
"""Fix stream loading on korasimo player.
   - The S3 stream URL `https://s3.us-east-2.amazonaws.com/simo3/hls/0/stream.m3u8`
     requires Origin/Referer matching the upstream player domain (1.soccertvhd.live).
   - When browser fetches from our yala.zaboni.store, the Origin doesn't match,
     so S3 returns 403.
   FIX: Rewrite S3 URLs in the response to go through our /__ext2/ proxy,
        AND make __ext2 proxy send proper Origin/Referer for S3 hosts.
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.korasimo"
with open(p) as f:
    c = f.read()

# 1) Rewrite S3 stream URLs to go through our proxy
# Insert after the existing kora-api.space sub_filter or similar
S3_REWRITE = (
    '        # Route stream CDN through our proxy so browser fetches same-origin\n'
    '        sub_filter "https://s3.us-east-2.amazonaws.com" "https://yala.zaboni.store/__ext2/s3.us-east-2.amazonaws.com";\n'
    '        sub_filter "//s3.us-east-2.amazonaws.com" "//yala.zaboni.store/__ext2/s3.us-east-2.amazonaws.com";\n'
    '        sub_filter "https://s3.amazonaws.com" "https://yala.zaboni.store/__ext2/s3.amazonaws.com";\n'
    '        sub_filter "//s3.amazonaws.com" "//yala.zaboni.store/__ext2/s3.amazonaws.com";\n'
    '        sub_filter "https://fastly.live.brightcove.com" "https://yala.zaboni.store/__ext2/fastly.live.brightcove.com";\n'
    '        sub_filter "//fastly.live.brightcove.com" "//yala.zaboni.store/__ext2/fastly.live.brightcove.com";\n'
)

# Insert in __ext2 block (the player block) just before our auto-managed marker, OR
# before "P2PEngineHls" marker which is in __ext2 block
P2P_MARKER = '        sub_filter "P2PEngineHls.tryRegisterServiceWorker(p2pConfig)" "Promise.resolve()";'
if P2P_MARKER in c and "yala.zaboni.store/__ext2/s3.us-east-2.amazonaws.com" not in c:
    c = c.replace(P2P_MARKER, S3_REWRITE + P2P_MARKER, 1)
    print("[1] S3/CDN rewrites added to __ext2 block")
else:
    print("[1] P2P marker not found OR already applied")

# 2) Add per-host Origin/Referer for streaming hosts in __ext2 block
# Find the existing rewritten_referer block we added and extend it.
OLD_REF = (
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
NEW_REF = (
    '        # Forward browser Referer (rewrite our host -> upstream host)\n'
    '        set $rewritten_referer $http_referer;\n'
    '        if ($rewritten_referer ~ "^(https?)://yala\\.zaboni\\.store(.*)$") {\n'
    '            set $rewritten_referer "$1://www.korasimo.com$2";\n'
    '        }\n'
    '        if ($rewritten_referer = "") {\n'
    '            set $rewritten_referer "https://www.korasimo.com/";\n'
    '        }\n'
    '        # Streaming CDN hosts need the player\'s origin as Referer\n'
    '        set $rewritten_origin "";\n'
    '        if ($ext_host ~ "(amazonaws\\.com|brightcove\\.com|fastly|akamaized|akamaihd)$") {\n'
    '            set $rewritten_referer "https://1.soccertvhd.live/";\n'
    '            set $rewritten_origin "https://1.soccertvhd.live";\n'
    '        }\n'
    '        proxy_set_header Referer $rewritten_referer;\n'
    '        proxy_set_header Origin $rewritten_origin;'
)

if OLD_REF in c:
    c = c.replace(OLD_REF, NEW_REF, 1)
    print("[2] streaming-aware Referer/Origin headers applied")
else:
    print("[2] OLD_REF not found")

with open(p, "w") as f:
    f.write(c)
print("Done.")
