#!/usr/bin/env python3
"""Remove dangerous Object.defineProperty overrides from wrap_v10.js that
   break iOS Telegram WebView (WKWebView). Replace them with simple, safe
   try/catch assignments. The click handler and DOM walker (which do the
   useful proxy rewriting) are kept untouched.
"""
import shutil, time

p = "/var/www/yala.zaboni.store/__yala_wrap_v10.js"
shutil.copy(p, "/root/__yala_wrap_v10.js.bak." + str(int(time.time())))

with open(p) as f:
    js = f.read()

# 1) Soften window.open block — drop the non-configurable defineProperty
OLD1 = (
    "// Make window.open non-overridable\n"
    "try {\n"
    "  Object.defineProperty(window, \"open\", { value: nullFn, writable: false, configurable: false });\n"
    "} catch(_) { try { window.open = nullFn; } catch(__) {} }"
)
NEW1 = (
    "// Soft block window.open (do not lock it; iOS WebView can choke on a\n"
    "// non-configurable defineProperty and refuse same-page anchor clicks).\n"
    "try { window.open = nullFn; } catch(_) {}"
)
if OLD1 in js:
    js = js.replace(OLD1, NEW1, 1)
    print("[1] window.open override softened")
else:
    print("[1] window.open marker not found")

# 2) Soften Notification block
OLD2 = (
    "// Block Notification permission requests\n"
    "try {\n"
    "  if (window.Notification) {\n"
    "    Object.defineProperty(window, \"Notification\", {\n"
    "      value: { permission: \"denied\", requestPermission: function(){ return Promise.resolve(\"denied\"); } },\n"
    "      writable: false\n"
    "    });\n"
    "  }\n"
    "} catch(_){}"
)
NEW2 = (
    "// Block Notification permission requests (soft override)\n"
    "try {\n"
    "  if (window.Notification && window.Notification.requestPermission) {\n"
    "    window.Notification.requestPermission = function(){ return Promise.resolve(\"denied\"); };\n"
    "  }\n"
    "} catch(_){}"
)
if OLD2 in js:
    js = js.replace(OLD2, NEW2, 1)
    print("[2] Notification override softened")
else:
    print("[2] Notification marker not found")

# 3) REMOVE the entire location.assign / replace / href setter override block.
# This block uses Object.defineProperty on Location.prototype.href which iOS
# WebView in Telegram does not allow — causing all anchor clicks to fail.
OLD3 = """// Lock window.location to prevent JS from navigating away to ad pages.
// We allow same-origin navigation only.
try {
  var origLocation = window.location;
  var origAssign = origLocation.assign.bind(origLocation);
  var origReplace = origLocation.replace.bind(origLocation);
  function safeNav(fn, url){
    try {
      var u = new URL(url, location.href);
      if (isBadUrl(u.href)) return; // ad URL — block
      if (u.host !== location.host && !isDirectHost(u.host)) {
        // External — route through our proxy
        var proxied = "/__ext/" + u.host + u.pathname + u.search + u.hash;
        return fn(proxied);
      }
      return fn(url);
    } catch(_) { return fn(url); }
  }
  origLocation.assign = function(url){ return safeNav(origAssign, url); };
  origLocation.replace = function(url){ return safeNav(origReplace, url); };
  // Block sneaky setters: location.href = "..."
  try {
    var origHrefDescriptor = Object.getOwnPropertyDescriptor(Location.prototype, "href")
      || Object.getOwnPropertyDescriptor(window.location, "href");
    if (origHrefDescriptor && origHrefDescriptor.set) {
      var origHrefSet = origHrefDescriptor.set;
      Object.defineProperty(window.location, "href", {
        set: function(v){ safeNav(function(u){ origHrefSet.call(window.location, u); }, v); },
        get: function(){ return origLocation.toString(); },
        configurable: true
      });
    }
  } catch(_){}
} catch(_){}"""
NEW3 = (
    "// REMOVED: location.assign/replace/href descriptor overrides.\n"
    "// They break iOS Telegram WebView. Click handler + DOM walker (below)\n"
    "// already rewrite anchor href values to /__ext/ before navigation,\n"
    "// so this defense is redundant for the common path."
)
if OLD3 in js:
    js = js.replace(OLD3, NEW3, 1)
    print("[3] location.assign/replace/href descriptor overrides removed")
else:
    print("[3] location override marker not found")

with open(p, "w") as f:
    f.write(js)

print("Done.")
