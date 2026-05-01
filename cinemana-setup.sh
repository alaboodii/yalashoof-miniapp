#!/bin/bash
set -e

# === 1. mkdir + wrapper JS ===
mkdir -p /opt/cinemana-bot /var/www/cinemana.zaboni.store

cat > /var/www/cinemana.zaboni.store/__cinemana_wrap.js <<'JS'
(function(){
"use strict";
try {
  var s = document.createElement("script");
  s.src = "https://telegram.org/js/telegram-web-app.js";
  s.onload = function(){
    var tg = window.Telegram && window.Telegram.WebApp;
    if (!tg) return;
    try { tg.ready(); } catch(_){}
    try { tg.expand(); } catch(_){}
    try { tg.disableVerticalSwipes && tg.disableVerticalSwipes(); } catch(_){}
  };
  document.head.appendChild(s);
} catch(_){}
try {
  window.open = function(){ return null; };
  window.alert = function(){};
  window.confirm = function(){ return false; };
  window.prompt = function(){ return null; };
} catch(_){}
try {
  var st = document.createElement("style");
  st.textContent = ""
    + "iframe[src*=\"ads\"], iframe[src*=\"doubleclick\"], iframe[src*=\"googlesyndication\"],"
    + "[id*=\"google_ads\"], [class*=\"adsbygoogle\"], [class*=\"banner-ad\"],"
    + "[class*=\"popup\"], [class*=\"overlay\"][class*=\"ad\"], [id*=\"popup\"]"
    + " { display: none !important; visibility: hidden !important; height: 0 !important; }";
  (document.head || document.documentElement).appendChild(st);
} catch(_){}
})();
JS

# === 2. Cinemana-specific rate-limit zone ===
cat > /etc/nginx/conf.d/cinemana-ratelimit.conf <<'NGCONF'
limit_req_zone $binary_remote_addr zone=cinemana_rl:10m rate=30r/s;
limit_conn_zone $binary_remote_addr zone=cinemana_conn:10m;
NGCONF

# === 3. Full HTTPS Nginx site (replaces the temp HTTP-only one) ===
cat > /etc/nginx/sites-available/cinemana.zaboni.store <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name cinemana.zaboni.store;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name cinemana.zaboni.store;

    ssl_certificate /etc/letsencrypt/live/cinemana.zaboni.store/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cinemana.zaboni.store/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    if ($is_bad_bot = 1) { return 403; }

    location ~ /\.(env|git|svn|hg|bzr|htaccess|htpasswd|DS_Store) { deny all; return 404; }
    location ~ /(wp-admin|wp-login|xmlrpc\.php|phpmyadmin|adminer)(/|$) { return 403; }
    location ~* \.(bak|backup|old|orig|sql|swp|swo|tmp|conf|config|log|ini|env)$ { deny all; return 404; }

    proxy_buffer_size 32k;
    proxy_buffers 16 32k;
    proxy_busy_buffers_size 64k;
    client_max_body_size 50M;

    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    limit_conn cinemana_conn 30;

    location / {
        limit_req zone=cinemana_rl burst=60 nodelay;

        set $upstream "cinemana.shabakaty.com";

        proxy_set_header Accept-Encoding "";
        proxy_set_header Host $upstream;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Referer "https://$upstream/";

        proxy_pass https://$upstream;
        proxy_ssl_server_name on;
        proxy_ssl_name $upstream;
        proxy_ssl_verify off;

        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;

        proxy_redirect https://cinemana.shabakaty.com/ https://cinemana.zaboni.store/;
        proxy_redirect http://cinemana.shabakaty.com/ https://cinemana.zaboni.store/;

        proxy_cookie_domain cinemana.shabakaty.com cinemana.zaboni.store;
        proxy_cookie_domain .cinemana.shabakaty.com .cinemana.zaboni.store;
        proxy_cookie_domain shabakaty.com cinemana.zaboni.store;
        proxy_cookie_domain .shabakaty.com .cinemana.zaboni.store;

        proxy_hide_header X-Frame-Options;
        proxy_hide_header Content-Security-Policy;
        proxy_hide_header Content-Security-Policy-Report-Only;
        proxy_hide_header X-Server-Powered-By;
        proxy_hide_header X-Powered-By;

        sub_filter_types text/html text/css application/javascript application/x-javascript;
        sub_filter_once off;
        sub_filter "https://cinemana.shabakaty.com" "https://cinemana.zaboni.store";
        sub_filter "//cinemana.shabakaty.com" "//cinemana.zaboni.store";
        sub_filter "</body>" "<script src=\"/__cinemana_wrap.js\" defer></script></body>";
    }

    location = /__cinemana_wrap.js {
        alias /var/www/cinemana.zaboni.store/__cinemana_wrap.js;
        add_header Cache-Control "no-cache" always;
    }
}
NGINX

nginx -t && nginx -s reload

# === 4. Bot files ===
cat > /opt/cinemana-bot/bot.py <<'PY'
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
if not BOT_TOKEN:
    sys.exit("BOT_TOKEN missing")
if not WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
    sys.exit("WEBAPP_URL missing or not HTTPS")

WELCOME = (
    "🎬 مرحباً بك في <b>سينمانا</b>\n\n"
    "🎞️ استمتع بمشاهدة:\n"
    "• أحدث الأفلام\n"
    "• أفضل المسلسلات\n"
    "• محتوى ترفيهي حصري\n\n"
    "🍿 اضغط الزر بالأسفل لفتح التطبيق"
)
BUTTON = "🎬 فتح سينمانا"

dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=BUTTON, web_app=WebAppInfo(url=WEBAPP_URL))
    ]])
    await message.answer(WELCOME, reply_markup=kb)


async def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
PY

cat > /opt/cinemana-bot/requirements.txt <<'REQ'
aiogram>=3.13,<4
python-dotenv>=1.0
REQ

cat > /opt/cinemana-bot/.env <<'ENV'
BOT_TOKEN=8607262223:AAGB4xJkPKxoSMxG4eP7Y6hA99qqI0Chwgg
WEBAPP_URL=https://cinemana.zaboni.store/
ENV

chmod 600 /opt/cinemana-bot/.env
chmod 700 /opt/cinemana-bot

# === 5. venv + install ===
cd /opt/cinemana-bot
python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

# === 6. systemd hardened ===
cat > /etc/systemd/system/cinemana-bot.service <<'UNIT'
[Unit]
Description=Cinemana Telegram Mini App Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cinemana-bot
EnvironmentFile=/opt/cinemana-bot/.env
ExecStart=/opt/cinemana-bot/venv/bin/python /opt/cinemana-bot/bot.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/cinemana-bot
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictNamespaces=true
RestrictRealtime=true
LockPersonality=true
MemoryDenyWriteExecute=true
SystemCallArchitectures=native
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

MemoryMax=256M
TasksMax=64
CPUQuota=50%

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now cinemana-bot.service
sleep 3

# === 7. Daily backup ===
mkdir -p /var/backups/cinemana
cat > /usr/local/bin/cinemana-backup.sh <<'BACKUP'
#!/bin/bash
set -e
DATE=$(date +%Y%m%d-%H%M%S)
DEST=/var/backups/cinemana/cinemana-$DATE.tar.gz
tar czf "$DEST" \
  /opt/cinemana-bot/.env \
  /opt/cinemana-bot/bot.py \
  /var/www/cinemana.zaboni.store \
  /etc/nginx/sites-available/cinemana.zaboni.store \
  /etc/systemd/system/cinemana-bot.service 2>/dev/null || true
chmod 600 "$DEST"
ls -1t /var/backups/cinemana/cinemana-*.tar.gz 2>/dev/null | tail -n +15 | xargs -r rm
BACKUP
chmod 755 /usr/local/bin/cinemana-backup.sh
/usr/local/bin/cinemana-backup.sh

cat > /etc/cron.d/cinemana-backup <<'CRON'
35 3 * * * root /usr/local/bin/cinemana-backup.sh
CRON
chmod 644 /etc/cron.d/cinemana-backup

echo "=== status ==="
systemctl is-active cinemana-bot
echo "=== logs ==="
journalctl -u cinemana-bot -n 5 --no-pager
echo "=== backups ==="
ls -lh /var/backups/cinemana/
echo "=== Done ==="
