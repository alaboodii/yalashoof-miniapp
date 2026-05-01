#!/usr/bin/env python3
"""HLS player speed boost for korasimo: lower initial buffer + low-latency mode
   so the stream starts faster on mobile (Telegram WebView).
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.korasimo"
with open(p) as f:
    c = f.read()

ANCHOR = '        sub_filter "P2PEngineHls.tryRegisterServiceWorker(p2pConfig)" "Promise.resolve()";'
NEW_RULES = (
    '        # HLS player speed boost (faster start on mobile)\n'
    '        sub_filter "maxBufferLength: 30," "maxBufferLength: 8, lowLatencyMode: true, backBufferLength: 4,";\n'
    '        sub_filter "maxBufferLength: 60," "maxBufferLength: 8, lowLatencyMode: true, backBufferLength: 4,";\n'
    '        sub_filter "maxBufferSize: 60*1000*1000," "maxBufferSize: 8*1000*1000,";\n'
    '        sub_filter "manifestLoadingTimeOut: 10000," "manifestLoadingTimeOut: 4000,";\n'
    '        sub_filter "fragLoadingTimeOut: 20000," "fragLoadingTimeOut: 6000,";\n'
)

if ANCHOR in c and "lowLatencyMode" not in c:
    c = c.replace(ANCHOR, NEW_RULES + ANCHOR, 1)
    with open(p, "w") as f:
        f.write(c)
    print("[OK] HLS speed tweaks added")
else:
    print("[SKIP] already added or anchor missing")
