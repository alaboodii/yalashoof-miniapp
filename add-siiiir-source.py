#!/usr/bin/env python3
"""Add siiiir.tv as the third source.
   - Generate /etc/nginx/sites-available/yala.zaboni.store.siiiir from
     yshoot template with host substitutions.
   - Update yala-switch script to accept 'siiiir' as a target.
   - Update bot.py SOURCES list to map slot3 -> siiiir.
   - Apply ALL today's customizations (Telegram padding, blue bg variant,
     popup hide, header hide, post-body hide, sandbox bypass, light mode,
     home button, mobile optimization).
"""
import os, re, shutil, subprocess
from pathlib import Path

AVAIL = Path("/etc/nginx/sites-available")
SWITCH = Path("/usr/local/bin/yala-switch")
BOT = Path("/opt/yalashoof-bot/bot.py")

# 1) Generate siiiir config from yshoot template
yshoot = (AVAIL / "yala.zaboni.store.yshoot").read_text(encoding="utf-8")
print(f"[0] yshoot template size: {len(yshoot)} bytes")

def to_siiiir(s: str) -> str:
    s = s.replace("yshoot_upstream", "siiiir_upstream")
    s = s.replace("www.yshootlive.com", "siiiir.tv")
    s = s.replace("yshootlive.com", "siiiir.tv")
    return s

siiiir = to_siiiir(yshoot)

# Source-specific tweaks for siiiir:
# - Home URL: siiiir uses /today-matches/ as the matches list
siiiir = siiiir.replace(
    'alab-home\\" href=\\"/shoot/\\"',
    'alab-home\\" href=\\"/today-matches/\\"',
)
# - Update the file's header comment
siiiir = re.sub(
    r"# == Customizations for yshoot[^\n]*\n.*?# DO NOT EDIT[^\n]*\n\n",
    "# == Customizations for siiiir (Sir TV / siiiir.tv) ==\n"
    "# Cloned from yshoot template 2026-05-01 with host swap to siiiir.tv\n"
    "# Live snapshot:     /root/backups/yala-2026-05-01-final/siiiir/ (after first run)\n"
    "# Bot switch script: /usr/local/bin/yala-switch siiiir\n"
    "# DO NOT EDIT THIS COMMENT BLOCK — it is the marker for documentation.\n"
    "\n",
    siiiir, count=1, flags=re.DOTALL,
)

# Append siiiir-specific brand renames before the wrap_v10.js loader
SIIIIR_BRANDS = (
    "\n        # === siiiir.tv-specific brand renames ===\n"
    "        sub_filter \"Sir TV\" \"Alaboodi TV\";\n"
    "        sub_filter \"SIR TV\" \"ALABOODI TV\";\n"
    "        sub_filter \"sir tv\" \"alaboodi tv\";\n"
    "        sub_filter \"Siiir TV\" \"Alaboodi TV\";\n"
    "        sub_filter \"Siiiir TV\" \"Alaboodi TV\";\n"
    "        sub_filter \"siiir.tv\" \"alaboodi-tv\";\n"
    "        sub_filter \"siiiir.tv\" \"alaboodi-tv\";\n"
    "        sub_filter \"سير تيفي\" \"العبودي تي في\";\n"
    "        sub_filter \"سير تي في\" \"العبودي تي في\";\n"
    "        sub_filter \"كوورة\" \"العبودي\";\n"
    "        sub_filter \"Kooora\" \"Alaboodi\";\n"
)
# Insert just before the </body> sub_filter
BODY_MARKER = "        sub_filter \"</body>\""
n_pos = siiiir.rfind(BODY_MARKER)
if n_pos > 0:
    siiiir = siiiir[:n_pos] + SIIIIR_BRANDS + siiiir[n_pos:]
    print("[1] siiiir-specific brand renames added")

(AVAIL / "yala.zaboni.store.siiiir").write_text(siiiir, encoding="utf-8")
print(f"[2] siiiir config written: {(AVAIL / 'yala.zaboni.store.siiiir').stat().st_size} bytes")

# 3) Update yala-switch to accept 'siiiir'
sw = SWITCH.read_text(encoding="utf-8")
if "siiiir" not in sw:
    sw = sw.replace(
        "case \"$TARGET\" in\n  yshoot|korasimo|slot3|slot4) ;;",
        "case \"$TARGET\" in\n  yshoot|korasimo|siiiir|slot3|slot4) ;;",
    )
    SWITCH.write_text(sw, encoding="utf-8")
    print("[3] yala-switch updated to accept 'siiiir'")
else:
    print("[3] yala-switch already supports 'siiiir'")

# 4) Update bot.py SOURCES list — change slot3 to siiiir
bot_src = BOT.read_text(encoding="utf-8")
OLD_SOURCES = '    {"id": "slot3",    "label": "خانة 3",        "host": None},'
NEW_SOURCES = '    {"id": "siiiir",   "label": "Sir TV",        "host": "siiiir.tv"},'
if OLD_SOURCES in bot_src:
    bot_src = bot_src.replace(OLD_SOURCES, NEW_SOURCES, 1)
    BOT.write_text(bot_src, encoding="utf-8")
    print("[4] bot.py SOURCES list updated: slot3 -> siiiir")
elif "siiiir" in bot_src:
    print("[4] bot.py already has siiiir entry")
else:
    print("[4] WARNING: SOURCES list marker not found in bot.py")

# 5) nginx test + restart bot
test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
print(f"[5] nginx -t: {'ok' if test.returncode == 0 else 'FAIL'}")
if test.returncode != 0:
    print(test.stderr)
    raise SystemExit(1)
subprocess.run(["systemctl", "reload", "nginx"], check=True)
print("[6] nginx reloaded")

subprocess.run(["systemctl", "restart", "yalashoof-bot"], check=True)
print("[7] bot restarted with new SOURCES list")
