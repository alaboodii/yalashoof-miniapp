#!/usr/bin/env python3
"""Restore yshoot from pre-rebuild backup (has all today's edits) and
   build korasimo by HOST SWAP from yshoot — preserving every customization.
"""
import shutil, subprocess, time
from pathlib import Path

AVAIL = Path("/etc/nginx/sites-available")
STATE = Path("/var/lib/yala-source")

# 1) Restore yshoot from the pre-rebuild backup (most recent)
YSHOOT_BAK = "/root/yshoot.bak.1777651677"
shutil.copy(YSHOOT_BAK, AVAIL / "yala.zaboni.store.yshoot")
print(f"[1] yshoot restored from {YSHOOT_BAK}")

# 2) Read yshoot (now has all today's edits)
yshoot = (AVAIL / "yala.zaboni.store.yshoot").read_text(encoding="utf-8")
print(f"   yshoot size: {len(yshoot)} bytes")

# 3) Build korasimo by host swap. Order matters (longest first).
def to_korasimo(s: str) -> str:
    s = s.replace("yshoot_upstream", "korasimo_upstream")
    s = s.replace("www.yshootlive.com", "www.korasimo.com")
    s = s.replace("yshootlive.com", "korasimo.com")
    return s

korasimo = to_korasimo(yshoot)

# 4) Source-specific tweaks for korasimo:
#    - home button URL: /shoot/ -> /
#    - add korasimo-specific brand replacements
korasimo = korasimo.replace(
    'alab-home\\" href=\\"/shoot/\\"',
    'alab-home\\" href=\\"/\\"',
)

# Append korasimo-specific brand sub_filters JUST BEFORE the auto-managed marker
KORASIMO_BRAND = (
    '\n        # === Korasimo-specific brand renames ===\n'
    '        sub_filter "Korasimo" "Alaboodi TV";\n'
    '        sub_filter "KORASIMO" "ALABOODI TV";\n'
    '        sub_filter "korasimo" "alaboodi-tv";\n'
    '        sub_filter "Kora Simo" "Alaboodi TV";\n'
    '        sub_filter "kora simo" "alaboodi-tv";\n'
    '        sub_filter "كورة سيمو" "العبودي تي في";\n'
)
# Insert after the last "sub_filter" line in / location block but before our auto-managed block
marker = "        # ============= Today's customizations (auto-managed) ============="
if marker in korasimo:
    korasimo = korasimo.replace(marker, KORASIMO_BRAND + marker, 1)
    print("[3] korasimo-specific brand renames inserted")

(AVAIL / "yala.zaboni.store.korasimo").write_text(korasimo, encoding="utf-8")
print(f"[4] korasimo written ({len(korasimo)} bytes)")

# 5) Apply currently active source
active = STATE.read_text(encoding="utf-8").strip() or "yshoot"
src = AVAIL / f"yala.zaboni.store.{active}"
shutil.copy(src, AVAIL / "yala.zaboni.store")
print(f"[5] active = {active}")

# 6) Test + reload
test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
print("[6] nginx -t:", "ok" if test.returncode == 0 else "FAIL")
if test.returncode != 0:
    print(test.stderr)
    raise SystemExit(1)
subprocess.run(["systemctl", "reload", "nginx"], check=True)
print("[7] nginx reloaded")
