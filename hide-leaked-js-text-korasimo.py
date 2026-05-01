#!/usr/bin/env python3
"""Hide the leaked JS text that appears at bottom-right of korasimo player.
   Cause: upstream's template literal contains `</script></body></html>\``.
   Our </body> sub_filter injects `<script src="..." defer></script></body>`,
   making the inner template literal contain `<script>...</script>`.
   The HTML parser sees the inner </script> and closes the outer script
   prematurely. Everything after becomes visible text.

   Fix: sub_filter to remove the leaked text from the response.
"""
p = "/etc/nginx/sites-available/yala.zaboni.store.korasimo"
with open(p) as f:
    c = f.read()

ANCHOR = '        sub_filter "P2PEngineHls.tryRegisterServiceWorker(p2pConfig)" "Promise.resolve()";'
NEW = (
    '        # Hide the leaked JS text that escaped from broken </script> in template literal\n'
    '        sub_filter "`;window.stop();} else {popupTest.close();}}})();" "`;";\n'
    '        sub_filter ";window.stop();} else {popupTest.close();}}})();</script>" "</script>";\n'
)

if ANCHOR in c and NEW not in c:
    c = c.replace(ANCHOR, NEW + ANCHOR, 1)
    print("[OK] leaked-text removal sub_filter added")
else:
    print("[SKIP] already added or anchor missing")

with open(p, "w") as f:
    f.write(c)
