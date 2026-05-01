(function(){
"use strict";

// ============================================================
// 1. Telegram WebApp expand
// ============================================================
try {
  var ts = document.createElement("script");
  ts.src = "https://telegram.org/js/telegram-web-app.js";
  ts.onload = function(){
    var tg = window.Telegram && window.Telegram.WebApp;
    if (!tg) return;
    try { tg.ready(); } catch(_){}
    try { tg.expand(); } catch(_){}
    try { tg.disableVerticalSwipes && tg.disableVerticalSwipes(); } catch(_){}
  };
  document.head.appendChild(ts);
} catch(_){}

// ============================================================
// 2. Aggressive popup / dialog / new-tab blocker
// ============================================================
var noop = function(){};
var nullFn = function(){ return null; };
var falseFn = function(){ return false; };

// Make window.open non-overridable
try {
  Object.defineProperty(window, "open", { value: nullFn, writable: false, configurable: false });
} catch(_) { try { window.open = nullFn; } catch(__) {} }

try { window.alert = noop; } catch(_){}
try { window.confirm = falseFn; } catch(_){}
try { window.prompt = nullFn; } catch(_){}
try { if (window.print) window.print = noop; } catch(_){}

// Block Notification permission requests
try {
  if (window.Notification) {
    Object.defineProperty(window, "Notification", {
      value: { permission: "denied", requestPermission: function(){ return Promise.resolve("denied"); } },
      writable: false
    });
  }
} catch(_){}

// Service Worker is needed by HLS p2p-engine for stream playback — leave it intact.

// Lock window.location to prevent JS from navigating away to ad pages.
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
} catch(_){}

// ============================================================
// 3. Known ad / popup / tracker domain blocklist
// ============================================================
var BAD_DOMAINS = [
  "doubleclick.net","googlesyndication.com","googleadservices.com","adservice.google",
  "googletagmanager.com","googletagservices.com","adsystem","adnxs.com","amazon-adsystem.com",
  "propellerads","propeller-ads","propu.sh","onclickads","onclkds","adskeeper",
  "popads","popcash","popmyads","popunder","pop-ads","clickadu","clicksvc",
  "adsterra","adstera","ad-maven","admaven","ad-delivery","adcash","adcdn",
  "exoclick","exosrv","exdynsrv","juicyads","trafficjunky","trafficfactory",
  "mgid.com","yieldmo","outbrain","taboola","revcontent","contentad",
  "yandex.ru/ads","mc.yandex","ads-pixel","ads.yahoo",
  "histats","statcounter","quantserve","scorecardresearch","hotjar.com/c/",
  "criteo.com","criteo.net","rubiconproject","openx.net","casalemedia",
  "moatads","2mdn.net","serving-sys","atdmt","fastclick","tradedoubler",
  "zedo.com","zergnet","mediaplex","valueclick","clicksor","clicktale",
  "advertising.com","advertize","advertising-online","advertise","ads-twitter",
  "alipromo","disqusads","admixer","admost","onpushads","redirectvoluum",
  "buysellads","ad.gif","ads.js","ad-core","adsense","adframe","ad-banner",
  // Discovered on yalashoof match-streaming pages (Adsterra family + popunder networks)
  "eruptpriority.com","eruptpriority","llvpn.com","sansat.link",
  "tawk.to/chat","tag.min.js","invoke.js",
  "highperformanceformat","mainnewsplate","nessusresult","contentwidget",
  "datsbrowngutter","groleegni.net","onmicroscopic","tropicalmotor","horizonmovecal"
];

function isBadUrl(u){
  if (!u) return false;
  if (typeof u !== "string") { try { u = String(u); } catch(_){ return false; } }
  var s = u.toLowerCase();
  for (var i = 0; i < BAD_DOMAINS.length; i++) {
    if (s.indexOf(BAD_DOMAINS[i]) !== -1) return true;
  }
  return false;
}

// ============================================================
// 4. Block ad-domain network requests at the API level
// ============================================================
// Streaming hosts whose URLs should be routed through our /__ext2/ proxy
// so anti-hotlink / CORS / Referer checks at the CDN are bypassed.
var STREAM_HOSTS = [
  "kora-plus.dad","a1.kora-plus.dad","a2.kora-plus.dad","a3.kora-plus.dad",
  "kora-top.zip","kora-api.top","kora-img.b-cdn.net",
  "reddit-soccer-streams.online","reddit-soccer-streams.app",
  "soccertvhd.live","frekora.live","korasimo.com"
];
function isStreamHost(host){
  if (!host) return false;
  host = host.toLowerCase();
  for (var i = 0; i < STREAM_HOSTS.length; i++) {
    var d = STREAM_HOSTS[i];
    if (host === d || host.endsWith("." + d)) return true;
  }
  return false;
}
function maybeProxyStreamUrl(url){
  try {
    var u = new URL(url, location.href);
    if (u.host === location.host) return null;
    if (!isStreamHost(u.host)) return null;
    return location.origin + "/__ext2/" + u.host + u.pathname + u.search + u.hash;
  } catch(_) { return null; }
}

try {
  var origFetch = window.fetch;
  if (origFetch) {
    window.fetch = function(input, init){
      var url = (typeof input === "string") ? input : (input && input.url);
      if (isBadUrl(url)) return Promise.reject(new Error("blocked"));
      var proxied = maybeProxyStreamUrl(url);
      if (proxied) {
        if (typeof input === "string") input = proxied;
        else { try { input = new Request(proxied, input); } catch(_){ input = proxied; } }
      }
      return origFetch.call(this, input, init);
    };
  }
} catch(_){}

try {
  var origXHROpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, async, user, password){
    if (isBadUrl(url)) {
      this.send = noop;
      this.abort = noop;
      this.setRequestHeader = noop;
      return;
    }
    var proxied = maybeProxyStreamUrl(url);
    var finalUrl = proxied || url;
    if (arguments.length <= 2) return origXHROpen.call(this, method, finalUrl);
    return origXHROpen.call(this, method, finalUrl, async, user, password);
  };
} catch(_){}

try {
  if (navigator.sendBeacon) {
    var origBeacon = navigator.sendBeacon.bind(navigator);
    navigator.sendBeacon = function(url, data){
      if (isBadUrl(url)) return true;
      return origBeacon(url, data);
    };
  }
} catch(_){}

// ============================================================
// 5. Block ad scripts/iframes at DOM-creation time
// ============================================================
try {
  var origCreateElement = document.createElement.bind(document);
  document.createElement = function(name){
    var el = origCreateElement(name);
    if (!name) return el;
    var n = String(name).toLowerCase();
    if (n === "script" || n === "iframe" || n === "img" || n === "link") {
      try {
        var origSetAttribute = el.setAttribute.bind(el);
        el.setAttribute = function(attr, val){
          if ((attr === "src" || attr === "href") && isBadUrl(val)) return;
          return origSetAttribute(attr, val);
        };
        Object.defineProperty(el, "src", {
          set: function(v){ if (!isBadUrl(v)) this.setAttribute("src", v); },
          get: function(){ return this.getAttribute("src"); },
          configurable: true
        });
        if (n === "link") {
          Object.defineProperty(el, "href", {
            set: function(v){ if (!isBadUrl(v)) this.setAttribute("href", v); },
            get: function(){ return this.getAttribute("href"); },
            configurable: true
          });
        }
      } catch(_){}
    }
    return el;
  };
} catch(_){}

// ============================================================
// 5b. Universal external-link interceptor — route ANY external click
//     through our /__ext/ proxy so the same ad-blocking applies.
//     This means new external streaming sites are auto-protected, no whitelist.
// ============================================================
// Hosts we let load directly (not through proxy) — they need their original
// origin to function (CORS, API endpoints, OAuth, signed URLs, etc.)
var DIRECT_HOSTS = [
  "youtube.com","www.youtube.com","youtu.be","youtube-nocookie.com","www.youtube-nocookie.com",
  "googlevideo.com","ytimg.com","i.ytimg.com",
  "vimeo.com","www.vimeo.com","player.vimeo.com",
  "dailymotion.com","www.dailymotion.com","dai.ly",
  "facebook.com","www.facebook.com","fbcdn.net","scontent.fbcdn.net",
  "twitter.com","x.com","twimg.com","abs.twimg.com",
  "telegram.org","t.me","web.telegram.org",
  "fonts.googleapis.com","fonts.gstatic.com","ajax.googleapis.com",
  "cdnjs.cloudflare.com","jsdelivr.net","cdn.jsdelivr.net","unpkg.com",
  "google.com","www.google.com","gstatic.com","www.gstatic.com",
  "amazonaws.com","cloudfront.net","akamaihd.net","akamaized.net",
  // Stream player domain — must load native (token signing + p2p require original origin)
  "000007.mov","www.000007.mov"
];

function isDirectHost(host){
  if (!host) return false;
  host = host.toLowerCase();
  for (var i = 0; i < DIRECT_HOSTS.length; i++) {
    var d = DIRECT_HOSTS[i];
    if (host === d || host.endsWith("." + d)) return true;
  }
  return false;
}

function rewriteExternalToProxy(url){
  try {
    var u = new URL(url, location.href);
    if (!u.host || u.host === location.host) return null;
    if (u.protocol !== "https:" && u.protocol !== "http:") return null;
    if (u.pathname.indexOf("/__ext/") === 0) return null;
    if (isBadUrl(u.href)) return null;       // ad domain — let it be blocked, don't proxy
    if (isDirectHost(u.host)) return null;   // pass through (YouTube etc need original origin)
    return "/__ext/" + u.host + u.pathname + u.search + u.hash;
  } catch(_) { return null; }
}

// Sanitize YouTube embed URLs: disable related videos, more-videos overlay,
// info card, branding, etc. Returns the cleaned URL or null if no change needed.
function sanitizeYouTubeEmbed(url){
  try {
    var u = new URL(url, location.href);
    if (!/(^|\.)youtube(-nocookie)?\.com$/i.test(u.host)) return null;
    if (u.pathname.indexOf("/embed/") !== 0) return null;
    var params = {
      "rel": "0",
      "modestbranding": "1",
      "iv_load_policy": "3",
      "showinfo": "0",
      "playsinline": "1",
      "fs": "1",
      "disablekb": "1",
      "autoplay": "1"
    };
    var changed = false;
    for (var k in params) {
      if (u.searchParams.get(k) !== params[k]) {
        u.searchParams.set(k, params[k]);
        changed = true;
      }
    }
    return changed ? u.toString() : null;
  } catch(_) { return null; }
}

try {
  document.addEventListener("click", function(e){
    var a = e.target;
    while (a && a !== document) {
      if (a.tagName === "A" && a.href) {
        var newHref = rewriteExternalToProxy(a.href);
        if (newHref) {
          e.preventDefault();
          e.stopPropagation();
          // Force same-tab navigation (no popups)
          window.location.href = newHref;
          return false;
        }
      }
      a = a.parentNode;
    }
  }, true);
} catch(_){}

// ============================================================
// 6. Click hijack defense: stop popunder onclick window.open chains
//    Many sites attach onclick handlers anywhere on body that open a new window.
//    We capture clicks at the document level FIRST and prevent any anchor with
//    target=_blank that points to a bad domain, plus any anchor with no href
//    (common popunder trigger).
// ============================================================
try {
  document.addEventListener("click", function(e){
    var t = e.target;
    while (t && t !== document) {
      if (t.tagName === "A") {
        var href = t.getAttribute("href") || "";
        if (isBadUrl(href) || href === "" || href === "#" || href.toLowerCase().indexOf("javascript:") === 0) {
          // If href is bad, block. But if href is "#" or empty, only block if also target=_blank or has popup-like onclick.
          if (isBadUrl(href)) {
            e.preventDefault();
            e.stopPropagation();
            return false;
          }
        }
        if (t.target === "_blank" && isBadUrl(t.href)) {
          e.preventDefault();
          e.stopPropagation();
          return false;
        }
      }
      t = t.parentNode;
    }
  }, true);
} catch(_){}

// ============================================================
// 6c. Auto-unmute video players (so audio plays automatically)
// ============================================================
function tryUnmute(){
  try {
    var videos = document.querySelectorAll("video");
    videos.forEach(function(v){
      try {
        v.muted = false;
        v.volume = 1.0;
        v.removeAttribute("muted");
        if (v.paused) { v.play().catch(function(){ /* will retry on user interaction */ }); }
      } catch(_){}
    });
    // Click site's unmute button if shown
    var unmuteBtn = document.querySelector(".unmute-btn") || document.querySelector("#unmute-overlay");
    if (unmuteBtn && typeof unmuteBtn.click === "function") {
      try { unmuteBtn.click(); } catch(_){}
    }
    // Hide the unmute overlay (no longer needed once video is unmuted)
    var overlay = document.getElementById("unmute-overlay");
    if (overlay) overlay.style.display = "none";
  } catch(_){}
}
// Try multiple times — videos often load asynchronously
setTimeout(tryUnmute, 300);
setTimeout(tryUnmute, 1000);
setTimeout(tryUnmute, 2500);
setTimeout(tryUnmute, 5000);

// iOS WebKit fallback: unmute on FIRST user touch anywhere on the page.
// (iOS Telegram WebView blocks unmuted autoplay without an in-page gesture.)
try {
  var firstGestureUnmuted = false;
  function firstGestureHandler(){
    if (firstGestureUnmuted) return;
    firstGestureUnmuted = true;
    tryUnmute();
    // Also click the site's existing "tap to unmute" button if present
    try {
      var btn = document.querySelector(".unmute-btn") || document.getElementById("unmute-overlay");
      if (btn) btn.click();
    } catch(_){}
  }
  ["touchstart","touchend","click","pointerdown","mousedown","keydown"].forEach(function(ev){
    document.addEventListener(ev, firstGestureHandler, { capture: true, passive: true });
  });
} catch(_){}

// Hook video play events: every time video starts playing, force unmute.
try {
  document.addEventListener("play", function(e){
    var t = e.target;
    if (t && t.tagName === "VIDEO") {
      try { t.muted = false; t.volume = 1.0; t.removeAttribute("muted"); } catch(_){}
    }
  }, true);
} catch(_){}

// Force volume to MAX always: poll every 250ms and snap any video back to volume 1, unmuted.
// (Event-based volumechange listeners don't always fire reliably across browsers.)
try {
  setInterval(function(){
    var vids = document.getElementsByTagName("video");
    for (var i = 0; i < vids.length; i++) {
      var v = vids[i];
      try {
        if (v.muted) v.muted = false;
        if (v.volume < 1) v.volume = 1.0;
        if (v.hasAttribute("muted")) v.removeAttribute("muted");
      } catch(_){}
    }
  }, 250);
} catch(_){}

// Watch for dynamically added <video> elements
try {
  var unmuteObs = new MutationObserver(function(mutations){
    for (var i = 0; i < mutations.length; i++) {
      var added = mutations[i].addedNodes;
      for (var j = 0; j < added.length; j++) {
        var n = added[j];
        if (n.nodeType !== 1) continue;
        if (n.tagName === "VIDEO" || (n.querySelectorAll && n.querySelectorAll("video").length > 0)) {
          tryUnmute();
          // Also catch the moment the video starts playing
          if (n.tagName === "VIDEO") {
            n.addEventListener("loadeddata", tryUnmute, { once: true });
            n.addEventListener("play",       tryUnmute, { once: true });
          }
        }
      }
    }
  });
  setTimeout(function(){
    if (document.body) unmuteObs.observe(document.body, { childList: true, subtree: true });
  }, 50);
} catch(_){}

// ============================================================
// 7. Custom copyright in footer
// ============================================================
function injectCredit(){
  var foot = document.getElementById("AYaFooter");
  if (!foot) return false;
  if (document.getElementById("__yala_credit")) return true;
  var span = document.createElement("span");
  span.id = "__yala_credit";
  span.textContent = "جميع الحقوق محفوظة - مصطفى العبودي";
  foot.appendChild(span);
  return true;
}
if (!injectCredit()) {
  document.addEventListener("DOMContentLoaded", injectCredit, { once: true });
  setTimeout(injectCredit, 500);
  setTimeout(injectCredit, 1500);
}

// ============================================================
// 8. Brand-name runtime replacer (safety net for dynamic content)
// ============================================================
var REPLACEMENTS = [
  [/Yalla\s*Shoot\s*Live/gi, "Alaboodi TV"],
  [/Yalla\s*Shoot/gi,        "Alaboodi TV"],
  [/Yallashoot\s*Live/gi,    "Alaboodi TV"],
  [/Yallashoot/gi,           "Alaboodi TV"],
  [/يلا\s*شوت\s*لايف/g,   "العبودي تي في"],
  [/يلا\s*شوت/g,           "العبودي تي في"],
  [/يلاشوت/g,              "العبودي تي في"]
];

function replaceText(node){
  var t = node.nodeValue;
  if (!t) return;
  var orig = t, changed = false;
  for (var i = 0; i < REPLACEMENTS.length; i++) {
    if (REPLACEMENTS[i][0].test(t)) {
      t = t.replace(REPLACEMENTS[i][0], REPLACEMENTS[i][1]);
      changed = true;
    }
  }
  if (changed && t !== orig) node.nodeValue = t;
}

function walk(root){
  if (!root) return;
  if (root.id === "AYaLogo" || (root.parentNode && root.parentNode.id === "AYaLogo")) return;
  if (root.nodeType === Node.TEXT_NODE) { replaceText(root); return; }
  if (root.nodeType !== Node.ELEMENT_NODE) return;
  var tag = root.tagName;
  if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT") return;
  if (root.hasAttribute && root.hasAttribute("title")) {
    var ta = root.getAttribute("title"), tac = ta;
    for (var j = 0; j < REPLACEMENTS.length; j++) tac = tac.replace(REPLACEMENTS[j][0], REPLACEMENTS[j][1]);
    if (tac !== ta) root.setAttribute("title", tac);
  }
  // Rewrite external links/iframes/embeds to go through our proxy
  if (tag === "A" && root.href) {
    var ah = rewriteExternalToProxy(root.href);
    if (ah) root.setAttribute("href", ah);
  } else if ((tag === "IFRAME" || tag === "EMBED") && root.src) {
    if (isBadUrl(root.src)) { try { root.remove(); return; } catch(_){} }
    else if (tag === "IFRAME") {
      var ytC = sanitizeYouTubeEmbed(root.src);
      if (ytC) root.setAttribute("src", ytC);
      else {
        var srcRR = rewriteExternalToProxy(root.src);
        if (srcRR) root.setAttribute("src", srcRR);
      }
    } else {
      var srcR = rewriteExternalToProxy(root.src);
      if (srcR) root.setAttribute("src", srcR);
    }
  } else if (tag === "OBJECT" && root.data) {
    var od = rewriteExternalToProxy(root.data);
    if (od) root.setAttribute("data", od);
  }
  for (var c = root.firstChild; c; c = c.nextSibling) walk(c);
}

function scanAll(){
  if (document.body) walk(document.body);
  if (document.title) {
    var nt = document.title;
    for (var i = 0; i < REPLACEMENTS.length; i++) nt = nt.replace(REPLACEMENTS[i][0], REPLACEMENTS[i][1]);
    if (nt !== document.title) document.title = nt;
  }
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", scanAll, { once: true });
} else { scanAll(); }

// ============================================================
// 9. MutationObserver — catch dynamically added content (ads + brand text)
// ============================================================
try {
  var observer = new MutationObserver(function(mutations){
    for (var m = 0; m < mutations.length; m++) {
      var mut = mutations[m];
      if (mut.type === "childList") {
        for (var n = 0; n < mut.addedNodes.length; n++) {
          var node = mut.addedNodes[n];
          // Block iframes/scripts pointing at ad domains
          if (node.nodeType === Node.ELEMENT_NODE) {
            try {
              var tag = node.tagName;
              if (tag === "IFRAME" || tag === "SCRIPT" || tag === "EMBED" || tag === "OBJECT") {
                var src = node.src || node.getAttribute("src") || node.data || node.getAttribute("data") || "";
                if (isBadUrl(src)) {
                  node.remove();
                  continue;
                }
                // Sanitize YouTube embeds: hide related videos, info card, branding
                if (tag === "IFRAME") {
                  var ytClean = sanitizeYouTubeEmbed(src);
                  if (ytClean) { node.setAttribute("src", ytClean); continue; }
                }
                // Route external (non-bad) iframe/embed/object src through our proxy
                if (tag === "IFRAME" || tag === "EMBED" || tag === "OBJECT") {
                  var rewritten = rewriteExternalToProxy(src);
                  if (rewritten) {
                    if (tag === "OBJECT") node.setAttribute("data", rewritten);
                    else node.setAttribute("src", rewritten);
                  }
                }
              }
              // Rewrite anchor hrefs to external sites so middle-click/copy-link uses our proxy
              if (tag === "A" && node.href) {
                var ah = rewriteExternalToProxy(node.href);
                if (ah) node.setAttribute("href", ah);
              }
              // Hide overlay-style fixed elements with high z-index (likely ads)
              if (tag === "DIV" || tag === "SECTION" || tag === "ASIDE" || tag === "IFRAME") {
                var cs = window.getComputedStyle(node);
                if (cs && cs.position === "fixed") {
                  var zi = parseInt(cs.zIndex, 10);
                  if (zi > 9000 && (node.offsetWidth >= 200 || node.offsetHeight >= 100)) {
                    // Iframe with empty/about:blank src and high z-index = popup ad container
                    if (tag === "IFRAME") {
                      var fsrc = node.getAttribute("src") || "";
                      if (fsrc === "" || fsrc === "about:blank") {
                        node.remove();
                        continue;
                      }
                    }
                    var cls = (node.className || "").toString().toLowerCase();
                    if (/\b(ad|ads|popup|overlay|banner|promo|sponsor)\b/.test(cls) || node.querySelector("iframe")) {
                      node.style.setProperty("display", "none", "important");
                    }
                  }
                }
              }
            } catch(_){}
            walk(node);
          } else if (node.nodeType === Node.TEXT_NODE) {
            replaceText(node);
          }
        }
      } else if (mut.type === "characterData") {
        replaceText(mut.target);
      }
    }
  });
  setTimeout(function(){
    if (document.body) observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }, 50);
} catch(_){}

// ============================================================
// 10. CSS-level ad / popup hiding (broader patterns)
// ============================================================
try {
  var st = document.createElement("style");
  st.textContent = [
    "iframe[src*=\"ads\"],iframe[src*=\"doubleclick\"],iframe[src*=\"googlesyndication\"],",
    "iframe[src*=\"adservice\"],iframe[src*=\"propeller\"],iframe[src*=\"popcash\"],",
    "iframe[src*=\"adsterra\"],iframe[src*=\"exoclick\"],iframe[src*=\"juicy\"],",
    "iframe[src*=\"mgid\"],iframe[src*=\"taboola\"],iframe[src*=\"outbrain\"],",
    "iframe[src*=\"criteo\"],iframe[src*=\"yieldmo\"],iframe[src*=\"adnxs\"],",
    "[id*=\"google_ads\"],[class*=\"adsbygoogle\"],[class*=\"adsense\"],[class*=\"ad-banner\"],",
    "[class*=\"ad-block\"],[class*=\"banner-ad\"],[class*=\"popup-ad\"],[class*=\"ad-container\"],",
    "[id*=\"popup\"],[class*=\"popup\"],[class*=\"overlay\"][class*=\"ad\"],",
    "[class*=\"sticky-ad\"],[class*=\"floating-ad\"],[class*=\"ad-wrapper\"],",
    "div[id^=\"adngin\"],div[id^=\"div-gpt-ad\"],div[id^=\"google_ads\"],",
    "ins.adsbygoogle,ins[data-ad],a[href*=\"//adclick\"],a[href*=\"//ads.\"],",
    /* Empty-src iframes pinned full-screen are ad overlays (popup/popunder pattern) */
    "iframe[style*=\"z-index: 2147483647\"],",
    "iframe[style*=\"z-index:2147483647\"],",
    "iframe:not([src]):not([data-keep]),",
    "iframe[src=\"\"],iframe[src=\"about:blank\"]",
    "{display:none!important;visibility:hidden!important;height:0!important;width:0!important;opacity:0!important;pointer-events:none!important}"
  ].join("");
  (document.head || document.documentElement).appendChild(st);
} catch(_){}

})();
