# Yalashoof Telegram Mini App

Lightweight Telegram bot (aiogram v3) + static wrapper page that embeds [yalashoof.com](https://www.yalashoof.com) inside Telegram as a fullscreen Mini App, with popups blocked and ad-iframes restricted via CSP.

## Files

| File | Purpose |
|------|---------|
| `bot.py` | aiogram v3 bot — `/start` returns an inline button that opens the WebApp |
| `index.html` | Wrapper page (fullscreen iframe + spinner) |
| `styles.css` | Lightweight CSS, Telegram-theme aware |
| `script.js` | Tiny JS — `tg.expand()`, fade-in, retry on failure |
| `requirements.txt` | Python deps (aiogram, python-dotenv) |
| `.env.example` | Template for `BOT_TOKEN` and `WEBAPP_URL` |

## 1. Create the bot

1. Open Telegram, message **@BotFather**.
2. Send `/newbot`, follow the prompts, copy the token.
3. (Optional, recommended) Send `/setmenubutton` to BotFather → choose your bot → paste your `WEBAPP_URL` (set in step 2 below) → name it e.g. `فتح التطبيق`. This adds a permanent menu button next to the chat input.

## 2. Host the wrapper page on GitHub Pages

Telegram Mini Apps require **HTTPS**. GitHub Pages provides this for free.

1. Create a new public repo, e.g. `yalashoof-miniapp`.
2. Push `index.html`, `styles.css`, `script.js` to the `main` branch.
3. In the repo: **Settings → Pages → Source: Deploy from a branch → Branch: `main` / `(root)` → Save**.
4. Wait ~1 min, then copy the URL it shows: `https://<your-username>.github.io/yalashoof-miniapp/`.
5. Open that URL in a normal browser to verify the spinner paints and the site loads.

## 3. Run the bot

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env       # on Windows: copy .env.example .env
# edit .env and fill in BOT_TOKEN + WEBAPP_URL

python bot.py
```

Send `/start` to your bot in Telegram. Tap the button — the WebApp opens fullscreen.

To run on a VPS, do the same on the server and keep the process alive with `nohup python bot.py &`, `screen`, `tmux`, or your preferred supervisor. (No systemd/Docker template included — keep it simple.)

## 4. How the ad/popup blocking works (and its limits)

**What works (cross-origin friendly):**
- `sandbox="allow-scripts allow-same-origin allow-forms"` on the iframe blocks new tabs, popups, and top-level navigation breakouts.
- `Content-Security-Policy` `frame-src` only allows `yalashoof.com` — any sub-iframe pointing at an ad network simply fails to load.
- Wrapper-level `window.open`, `alert`, `confirm`, `prompt` overrides catch anything running in the wrapper itself.
- `referrerpolicy="no-referrer-when-downgrade"` prevents ad networks from learning the Telegram referrer.

**What doesn't (browser security model):**
The wrapper and the iframe are on **different origins**. The Same-Origin Policy means the wrapper's JS and CSS cannot reach into the iframe's DOM. So:
- In-page banner ads served from the same origin as yalashoof.com are still visible.
- A `MutationObserver` on the wrapper sees nothing inside the iframe.
- Hiding ads with CSS only works for elements in the wrapper, not in the iframe.

Full DOM-level ad scrubbing inside the iframe is only possible with a **server-side HTML-rewriting proxy**, which is intentionally out of scope here (the brief said wrapper-only, no website modifications, no APIs).

## 5. Troubleshooting

- **"WEBAPP_URL missing or not HTTPS"** — set `WEBAPP_URL` in `.env` to your GitHub Pages URL (must start with `https://`).
- **Button does nothing in Telegram** — the WebApp URL must be reachable over HTTPS with a valid certificate. GitHub Pages handles this automatically; if you self-host, check your cert.
- **Site partially broken inside Telegram** — some pages may rely on `window.open` or top navigation, which the sandbox blocks. If a critical link fails, edit `index.html` and add `allow-popups` to the `sandbox` attribute. (Trade-off: more popup ads will leak through.)
- **Spinner spins forever, no site** — open the GitHub Pages URL in a desktop browser and check DevTools console / Network tab. CSP violations show up there.

## 6. Tweaking

- Change the welcome text or button label in `bot.py` (`WELCOME_TEXT`, `BUTTON_TEXT`).
- Change the loading timeout in `script.js` (`LOAD_TIMEOUT_MS`).
- Add more allowed domains in the `Content-Security-Policy` `<meta>` tag in `index.html` if yalashoof.com loads images/scripts from a CDN that's being blocked.
