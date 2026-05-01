# Snapshot 2026-05-01-final

Working state of yala.zaboni.store nginx configs and assets after all
fixes from 2026-05-01.

## Per-source isolation

Each source has its own folder with its config and a CHANGELOG describing
the customizations specific to that source.

| Source   | Upstream            | Config file (live)                                  | Status   |
|----------|---------------------|-----------------------------------------------------|----------|
| yshoot   | www.yshootlive.com  | /etc/nginx/sites-available/yala.zaboni.store.yshoot | working  |
| korasimo | www.korasimo.com    | /etc/nginx/sites-available/yala.zaboni.store.korasimo | working |

The Telegram bot picks one source via `/usr/local/bin/yala-switch <id>`,
which copies that source's file to `yala.zaboni.store` and reloads nginx.
`/etc/nginx/sites-enabled/yala.zaboni.store` is a symlink to the active file.

## Restore

To restore yshoot from this snapshot:
    cp yshoot/yala.zaboni.store.yshoot.conf  /etc/nginx/sites-available/yala.zaboni.store.yshoot
    /usr/local/bin/yala-switch yshoot

To restore korasimo:
    cp korasimo/yala.zaboni.store.korasimo.conf  /etc/nginx/sites-available/yala.zaboni.store.korasimo
    /usr/local/bin/yala-switch korasimo

To restore the wrap_v10.js client script:
    cp __yala_wrap_v10.js  /var/www/yala.zaboni.store/__yala_wrap_v10.js
