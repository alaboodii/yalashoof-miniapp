# korasimo (Kora Simo — www.korasimo.com)

## Source-specific customizations applied 2026-05-01

### Brand / UI
- Default theme: LIGHT
- Korasimo brand renames: "كورة سيمو" → "العبودي تي في", "Kora Simo" → "Alaboodi TV"
- Footer copyright: "جميع الحقوق محفوظة - مصطفى العبودي"

### Hide / clean
- Side notification ad banner (#side-notification) hidden
- Watermark .watermark hidden
- Header bar above player (.bg-sl-block-head) hidden
- Description paragraphs inside .post-body hidden
- Telegram popup (#_sm, #_smb) hidden
- Ad iframes hidden
- Leaked JS text from broken </script> in template literal — removed via sub_filter

### Telegram WebApp integration
- Loads telegram-web-app.js inline in <head> (after `<meta charset>`)
- Calls tg.ready() + tg.expand() on load
- Adds `body{padding-top:100px}` so content starts below close button
- (No blue bg — korasimo's design is dark navy)

### Network / proxy
- Wildcard `proxy_redirect` keeps any external 30x redirect on yala.zaboni.store
- proxy_cookie_domain rewrites korasimo.com cookies to yala.zaboni.store
- Origin host: www.korasimo.com (port 443)

### Player (`/__ext2?/HOST/PATH/` — Live3.php at 1.soccertvhd.live)
- Sandbox bypass: `window.self !== window.top` → `false` (handles both spaced and unspaced)
- popupTest bypass: `if (popupTest)` / `if(popupTest)` → `if (false)` / `if(false)`
- isInIframe bypass: `if (isInIframe` → `if (false`
- HLS speed boost:
    - maxBufferLength 30s → 8s
    - lowLatencyMode: true
    - manifestLoadingTimeOut 10s → 4s
    - fragLoadingTimeOut 20s → 6s
- Mobile player: `.main-wrapper{height:100dvh}`, video `object-fit:contain`, no padding ≤768px
- Quality selector preserved (visible)
- Home button on player REMOVED (per user request — korasimo player has its own UI)

### Stream proxying (KEY FIX)
The S3 stream URLs (s3.us-east-2.amazonaws.com/simo3/...) require Origin/Referer
matching the upstream player domain (1.soccertvhd.live). Browser fetching from
yala.zaboni.store sent wrong Origin → S3 returned 403.

Fix: rewrite stream URLs to /__ext2/HOST/PATH/ via sub_filter; in __ext2 proxy
detect amazonaws/brightcove/fastly hosts and override headers:
    Referer: https://1.soccertvhd.live/
    Origin:  https://1.soccertvhd.live

Result: stream loads at 720p, playback starts within ~1-2s on mobile.

### Important fixes
- 2026-05-01: Referer rewriting in __ext2: rewrite browser's referer from
  yala.zaboni.store host to www.korasimo.com host so Live3.php can identify
  which match the user came from.

## Bot integration
The Telegram bot's source-switch button (`yala-switch korasimo`) copies this file
to `/etc/nginx/sites-available/yala.zaboni.store` and reloads nginx.
