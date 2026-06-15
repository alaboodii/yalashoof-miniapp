# Yalashoof / Trab TV — Telegram Mini App

A Telegram Mini App that streams live football. Architecture: an **nginx reverse-proxy
gateway** at `https://yala.zaboni.store/` serves a static portal (`showcase.html`,
branded "Trab TV") whose cards open up to 4 upstream sources, each reverse-proxied
under `/s/<id>/`. A Python (aiogram v3) bot opens that gateway as a WebApp and provides
an admin dashboard.

> **Why a reverse proxy and not an iframe?** Iframing a streaming site breaks inside
> iOS Telegram (top-level navigation + fullscreen video suspension). Every source is
> served same-origin through nginx instead. See `index.html` — it is only a redirect.

## Layout

| Path | Purpose |
|------|---------|
| `bot.py` | aiogram v3 bot — `/start`, WebApp button, full admin dashboard |
| `index.html` | Safety redirect to the gateway (legacy GitHub Pages URL). **No iframe.** |
| `requirements.txt` | Python deps (aiogram, python-dotenv) |
| `.env.example` | Template for `BOT_TOKEN`, `WEBAPP_URL`, `ADMIN_IDS`, `DEV_URL` |
| `server/nginx/yala.zaboni.store.conf` | The live nginx gateway config (4 sources under `/s/`) |
| `server/nginx/yala-switch` | Legacy single-source switch script (**no longer used** by the bot) |
| `server/webroot/showcase.html` | The "Trab TV" portal served at `/` |
| `server/webroot/__kooracity-wrapper.html` | Iframe wrapper for the CF-blocked source |
| `server/webroot/__*-logo.svg`, `__yala_styles.css`, `diag.html` | Portal assets |

`server/` mirrors what is deployed on the VPS so it is version-controlled and recoverable.

## Sources (under `/s/<id>/`)

| Card | id | Upstream | State |
|------|----|----------|-------|
| المصدر الأول | `koora4live` | `gonutradeal.com` (rotates) | passthrough; re-point when domain rotates |
| المصدر الثاني | `kooracity` | `koooracity.io` | **iframe wrapper** (Cloudflare blocks datacenter IPs) |
| المصدر الثالث | `livescore` | `www.freekora.com` (rotates) | passthrough |
| المصدر الرابع | `syrlive` | `d.syrlive.com` | full proxy + ad/popup nuke — most stable |

## Deployment (VPS)

- Bot runs as systemd service `yalashoof-bot.service` from `/opt/yalashoof-bot/`.
- nginx config: `/etc/nginx/sites-available/yala.zaboni.store` (symlinked into `sites-enabled`).
- Webroot: `/var/www/yala.zaboni.store/`.
- TLS via certbot for `yala.zaboni.store`.

```bash
# deploy bot
scp bot.py root@VPS:/opt/yalashoof-bot/bot.py
ssh root@VPS systemctl restart yalashoof-bot.service

# deploy nginx
scp server/nginx/yala.zaboni.store.conf root@VPS:/etc/nginx/sites-available/yala.zaboni.store
ssh root@VPS 'nginx -t && systemctl reload nginx'
```

## Local development

```bash
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env                          # fill BOT_TOKEN, WEBAPP_URL, ADMIN_IDS
python bot.py
```

## Bot configuration (`.env`)

| Key | Meaning |
|-----|---------|
| `BOT_TOKEN` | BotFather token |
| `WEBAPP_URL` | `https://yala.zaboni.store/` — the gateway portal (HTTPS required) |
| `ADMIN_IDS` | Comma-separated Telegram IDs that get the admin dashboard |
| `DEV_URL` | Optional "Dev" contact link shown under the WebApp button |

## Admin dashboard

`/admin` (admins only): user stats, paginated user list, broadcast (copy-message to all
users with confirm step), forced-channel join gate (add/remove/toggle + membership
enforcement on `/start`), and a read-only source-status view.
