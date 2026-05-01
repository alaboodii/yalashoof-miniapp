#!/usr/bin/env python3
"""Sync today's customizations into BOTH per-source nginx configs and
   reconnect sites-enabled to sites-available so the bot's switch script
   actually takes effect.

Steps
-----
1. Read /etc/nginx/sites-enabled/yala.zaboni.store (current good with all today's fixes
   — uses yshootlive as upstream).
2. Save it as the canonical yshoot source: /etc/nginx/sites-available/yala.zaboni.store.yshoot
3. Generate a korasimo variant by host-substitution and save as:
   /etc/nginx/sites-available/yala.zaboni.store.korasimo
4. Copy the *active* source (read from /var/lib/yala-source) into
   /etc/nginx/sites-available/yala.zaboni.store
5. Make /etc/nginx/sites-enabled/yala.zaboni.store a symlink to the available file
   so future bot switches take effect.
6. nginx -t && reload.
"""
import shutil, subprocess, time, os
from pathlib import Path

ENABLED = Path("/etc/nginx/sites-enabled/yala.zaboni.store")
AVAIL = Path("/etc/nginx/sites-available")
STATE = Path("/var/lib/yala-source")

# 0) Backup what we have
ts = int(time.time())
shutil.copy(ENABLED, f"/root/yala.zaboni.store.pre-sync.{ts}")
print(f"[0] backup -> /root/yala.zaboni.store.pre-sync.{ts}")

current = ENABLED.read_text(encoding="utf-8")

# 1) yshoot: just save current as-is (it IS the yshoot version with our edits)
yshoot_path = AVAIL / "yala.zaboni.store.yshoot"
yshoot_path.write_text(current, encoding="utf-8")
print(f"[1] saved yshoot variant ({len(current)} bytes) to {yshoot_path}")

# 2) korasimo: substitute host references
def to_korasimo(s: str) -> str:
    # Order matters: longer/specific patterns first
    repl = [
        ("yshoot_upstream", "korasimo_upstream"),
        ("www.yshootlive.com", "www.korasimo.com"),
        ("yshootlive.com", "korasimo.com"),  # bare domain (no www)
    ]
    for old, new in repl:
        s = s.replace(old, new)
    return s

korasimo = to_korasimo(current)
korasimo_path = AVAIL / "yala.zaboni.store.korasimo"
korasimo_path.write_text(korasimo, encoding="utf-8")
print(f"[2] saved korasimo variant ({len(korasimo)} bytes) to {korasimo_path}")

# 3) Determine which is active
active = "yshoot"
try:
    active = STATE.read_text(encoding="utf-8").strip() or "yshoot"
except Exception:
    pass
print(f"[3] active source: {active}")

# 4) Write the active source to sites-available/yala.zaboni.store
src = AVAIL / f"yala.zaboni.store.{active}"
dst = AVAIL / "yala.zaboni.store"
shutil.copy(src, dst)
print(f"[4] sites-available/yala.zaboni.store := {src.name}")

# 5) Replace sites-enabled file with symlink to sites-available
if ENABLED.is_symlink() or ENABLED.exists():
    ENABLED.unlink()
ENABLED.symlink_to(dst)
print(f"[5] sites-enabled/yala.zaboni.store -> sites-available/yala.zaboni.store (symlink)")

# 6) Test nginx and reload
test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
print("[6] nginx -t:", "ok" if test.returncode == 0 else "FAIL")
if test.returncode != 0:
    print(test.stderr)
    raise SystemExit("nginx -t failed; not reloading")

reload = subprocess.run(["systemctl", "reload", "nginx"], capture_output=True, text=True)
print("[7] systemctl reload nginx:", "ok" if reload.returncode == 0 else "FAIL")
print("Done.")
