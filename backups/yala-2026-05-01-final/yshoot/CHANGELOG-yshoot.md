# yshoot (Yalla Shoot — www.yshootlive.com)

## Source-specific customizations applied 2026-05-01

### Brand / UI
- Logo `h1.bg-sl-logo` replaced with red gradient pill containing "Alaboodi TV"
- Footer copyright replaced with "جميع الحقوق محفوظة - مصطفى العبودي"
- Day-tabs (الأمس/اليوم/الغد) coloured: teal/red/yellow
- Default theme switched to LIGHT (removed `<html class=dark>` injection)

### Hide / clean
- Tawk.to chat widget hidden
- Side notification ad banner hidden
- Hero section, FAQ, info-grid, app-promo banners hidden
- Header bar above player (.bg-sl-block-head) hidden
- Description paragraphs inside .post-body hidden — keeps player visible
- Telegram subscribe popup (#_sm, #_smb) hidden
- Ad iframes (doubleclick, adsterra, propellerads, etc.) hidden

### Telegram WebApp integration
- Loads telegram-web-app.js inline in <head>
- Calls tg.ready() + tg.expand() on load
- Adds `body{padding-top:100px}` so content starts below close button
- Adds blue background (`#004ea8`) extending up to status bar

### Network / proxy
- Wildcard `proxy_redirect` keeps any external 30x redirect on yala.zaboni.store
- proxy_cookie_domain rewrites yshootlive.com cookies to yala.zaboni.store
- Origin host: www.yshootlive.com (port 443)
- Cache: 30s for HTML, 7d for static assets

### Player (`/__ext2?/HOST/PATH/`)
- Sandbox bypass: `window.self !== window.top` → `false` (with/without spaces)
- Streaming origin (live2.d-kora.online) preconnect hint
- Brightcove fastly preconnect hint
- HLS p2p service worker registration neutralized
- wrap_v10.js loaded with <script defer> (fast)
- Home button at bottom-center: bottom:50px (mobile bottom:40px), href="/shoot/"

### Important fixes
- 2026-05-01: Sub_filter target switched from `<head>` to `<meta charset="UTF-8" />`
  to avoid injecting `<script>` inside upstream's `document.documentElement.innerHTML`
  template literal (which would corrupt the HTML parser via inner `</script>`).
- 2026-05-01: Removed duplicate `<meta charset>` sub_filter in / block that was
  overwriting the blue-bg style.

## Bot integration
The Telegram bot's source-switch button (`yala-switch yshoot`) copies this file to
`/etc/nginx/sites-available/yala.zaboni.store` and reloads nginx.
