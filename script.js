(function () {
    "use strict";

    const FAST_HIDE_MS = 2500;
    const FAILSAFE_HIDE_MS = 8000;

    function init() {
        const frame = document.getElementById("mainFrame");
        const loader = document.getElementById("loader");
        const retry = document.getElementById("retry");
        const loaderText = document.getElementById("loader-text");

        const tg = window.Telegram && window.Telegram.WebApp;
        if (tg) {
            try { tg.ready(); } catch (_) {}
            try { tg.expand(); } catch (_) {}
            try { tg.disableVerticalSwipes && tg.disableVerticalSwipes(); } catch (_) {}
        }

        let hidden = false;
        function hideLoader() {
            if (hidden) return;
            hidden = true;
            loader.classList.add("hidden");
        }

        // Hide as soon as iframe fires load.
        frame.addEventListener("load", hideLoader, { passive: true });

        // Speed-up: hide loader quickly even if cross-origin load event is delayed.
        setTimeout(hideLoader, FAST_HIDE_MS);

        // Failsafe: never let the loader stick around forever.
        setTimeout(function () {
            if (hidden) return;
            loaderText.textContent = "تعذّر تحميل الموقع.";
            retry.hidden = false;
        }, FAILSAFE_HIDE_MS);

        retry.addEventListener("click", function () {
            const src = frame.src;
            frame.src = "about:blank";
            setTimeout(function () { frame.src = src; }, 50);
            retry.hidden = true;
            loaderText.textContent = "جاري التحميل…";
            loader.classList.remove("hidden");
            hidden = false;
            setTimeout(hideLoader, FAST_HIDE_MS);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();
